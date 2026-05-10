import gc
import io
import sys
import json
import warnings
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from datetime import timedelta
from time import perf_counter
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class BenchmarkResult:
    """Single benchmark result with timing statistics.

    Attributes:
        name: Target name or custom override.
        avg, std, median, minimum, maximum: Timing stats in seconds.
        itr_ps: Iterations per second (after outlier trimming).
        iterations: Total runs executed.
        counted_iterations: Runs used for stats after trimming.
        total_time: Wall-clock time for all runs.
    """

    name: str
    avg: float
    std: float
    median: float
    minimum: float
    maximum: float
    itr_ps: float
    iterations: int
    counted_iterations: int
    total_time: float
    verbose: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __repr__(self) -> str:
        return f"BenchmarkResult(name='{self.name}', avg={self.avg:.3g}, itr_ps={self.itr_ps})"


class BenchmarkResults:
    """Iterable collection of BenchmarkResult objects with export utilities."""

    def __init__(self, results: List[BenchmarkResult]):
        self._results = results

    def __iter__(self) -> Iterator[BenchmarkResult]:
        return iter(self._results)

    def __getitem__(self, index: int) -> BenchmarkResult:
        return self._results[index]

    def __len__(self) -> int:
        return len(self._results)

    def to_list(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._results]

    def to_json(self, indent: int = 4) -> str:
        return json.dumps(self.to_list(), indent=indent)

    def print(self, verbose: Optional[bool] = None) -> None:
        """Print results to stdout. Pass verbose=True for extended stats."""
        for r in self._results:
            is_verbose = verbose if verbose is not None else r.verbose
            print(f"{r.name}: {self._format_time(r.avg)}/itr | {r.itr_ps:.2f} itr/s")
            if is_verbose:
                print(f"  std:     {self._format_time(r.std)}")
                print(f"  median:  {self._format_time(r.median)}")
                print(f"  min/max: {self._format_time(r.minimum)} / {self._format_time(r.maximum)}")
                print(f"  runs:    {r.iterations} ({r.counted_iterations} counted)")
                print(f"  total:   {self._format_time(r.total_time)}")

    @staticmethod
    def _format_time(t: float) -> str:
        """Format seconds to human readable string with units."""
        units = {"ps": 1e-12, "ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1}
        for unit, ratio in units.items():
            factor = 59.95 if unit == "s" else 999.5
            if t < factor * ratio:
                num = f"{t / ratio:#.3g}".rstrip(".")
                return f"{num}{unit}"
        return str(timedelta(seconds=round(t))).removeprefix("0:")


class _BeforeAfter:
    """Runnable hook for setup/teardown."""

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.name = func.__name__

    def __call__(self) -> Any:
        return self.func(*self.args, **self.kwargs)

    def __hash__(self) -> int:
        return hash(tuple([self.func.__name__, self.args, tuple(self.kwargs.items())]))


class _Function:
    """Benchmark target with configuration and optional hooks."""

    def __init__(
        self,
        func: Callable[..., Any],
        *,
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        max_samples: Optional[int] = None,
        min_samples: Optional[int] = None,
        cut: Optional[float] = None,
        disable_stdout: Optional[bool] = None,
        verbose: Optional[bool] = None,
        disable_gc: Optional[bool] = None,
        batch_size: Optional[int] = None,
        live_output: Optional[bool] = None,
        before: Optional[Callable[..., Any]] = None,
        after: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs: Dict[str, Any] = kwargs if kwargs is not None else {}
        self.func_name = func.__name__

        # Config overrides (None = inherit from Suite)
        self._display_name = name
        self._timeout = timeout
        self._max_samples = max_samples
        self._min_samples = min_samples
        self._cut = cut
        self._disable_stdout = disable_stdout
        self._verbose = verbose
        self._disable_gc = disable_gc
        self._batch_size = batch_size
        self._live_output = live_output
        self._before_fn = before
        self._after_fn = after

        # Resolved hooks (set by before_after())
        self.before_hook: Optional[_BeforeAfter] = None
        self.after_hook: Optional[_BeforeAfter] = None

    def apply_hooks(
        self,
        before: Optional[_BeforeAfter] = None,
        after: Optional[_BeforeAfter] = None,
    ) -> None:
        """Apply test-specific or suite-level hooks."""
        self.before_hook = _BeforeAfter(self._before_fn) if self._before_fn else before
        self.after_hook = _BeforeAfter(self._after_fn) if self._after_fn else after

    def __call__(self, default_batch_size: int = 0) -> Tuple[float, Any]:
        """Run function once (or batch_size times) and return elapsed time."""
        if self.before_hook:
            self.before_hook()

        batch_size = self._batch_size if self._batch_size is not None else default_batch_size
        if batch_size == 0:
            batch_size = 1

        start = perf_counter()

        # Amortize overhead for micro-benchmarks
        if batch_size > 1:
            for _ in range(batch_size):
                res = self.func(*self.args, **self.kwargs)
        else:
            res = self.func(*self.args, **self.kwargs)

        duration = perf_counter() - start

        if self.after_hook:
            self.after_hook()

        return duration / batch_size, res

    def __hash__(self) -> int:
        return hash(tuple([self.func_name, self.args, tuple(self.kwargs.items())]))

    def pretty(self) -> str:
        """String representation of the call."""
        if self._display_name:
            return self._display_name
        args_str = ", ".join([str(a) for a in self.args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in self.kwargs.items()])
        sep = ", " if self.args and self.kwargs else ""
        return f"{self.func_name}({args_str}{sep}{kwargs_str})"


class Suite:
    """Benchmarking suite for registering and running tests.

    Args:
        max_samples: Maximum statistical samples per benchmark (default 1000).
        timeout: Time limit in seconds per benchmark (default 10.0).
    """

    def __init__(self, max_samples: int = 1000, timeout: float = 10.0) -> None:
        self.tests: List[_Function] = []
        self.timeout = timeout
        self.max_samples = max_samples
        self.min_samples = 3
        self.cut = 0.05
        self.disable_stdout = False
        self.verbose = False
        self.disable_gc = False
        self.batch_size = 0
        self.live_output = True
        self.warmup_samples = 0
        self.validate_responses = False
        self.validate_limit = 5
        self._beforeFunc: Optional[_BeforeAfter] = None
        self._afterFunc: Optional[_BeforeAfter] = None

    def bench(
        self,
        *,
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        max_samples: Optional[int] = None,
        min_samples: Optional[int] = None,
        cut: Optional[float] = None,
        disable_stdout: Optional[bool] = None,
        verbose: Optional[bool] = None,
        disable_gc: Optional[bool] = None,
        batch_size: Optional[int] = None,
        live_output: Optional[bool] = None,
        before: Optional[Callable[..., Any]] = None,
        after: Optional[Callable[..., Any]] = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Decorator to register a benchmark.

        Pass function inputs via ``args`` and ``kwargs``.
        All other parameters are benchmark configuration overrides.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            self.add(
                func,
                args=args,
                kwargs=kwargs,
                name=name,
                timeout=timeout,
                max_samples=max_samples,
                min_samples=min_samples,
                cut=cut,
                disable_stdout=disable_stdout,
                verbose=verbose,
                disable_gc=disable_gc,
                batch_size=batch_size,
                live_output=live_output,
                before=before,
                after=after,
            )
            return func

        return decorator

    def set_timeout(self, t: float) -> None:
        self.timeout = t

    def set_max_samples(self, n: int) -> None:
        self.max_samples = n

    def set_min_samples(self, n: int) -> None:
        self.min_samples = n

    def set_cut(self, n: float) -> None:
        self.cut = n

    def set_warmup_samples(self, n: int) -> None:
        self.warmup_samples = n

    def set_validate_responses(self, val: bool) -> None:
        self.validate_responses = val

    def set_validate_limit(self, n: int) -> None:
        self.validate_limit = n

    def set_batch_size(self, n: int) -> None:
        self.batch_size = n

    def set_live_output(self, val: bool) -> None:
        self.live_output = val

    def add(
        self,
        func: Callable[..., Any],
        *,
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        max_samples: Optional[int] = None,
        min_samples: Optional[int] = None,
        cut: Optional[float] = None,
        disable_stdout: Optional[bool] = None,
        verbose: Optional[bool] = None,
        disable_gc: Optional[bool] = None,
        batch_size: Optional[int] = None,
        live_output: Optional[bool] = None,
        before: Optional[Callable[..., Any]] = None,
        after: Optional[Callable[..., Any]] = None,
    ) -> None:
        """Register a callable for benchmarking. Equivalent to ``@suite.bench()``."""
        if not callable(func):
            raise TypeError("Benchmark target must be callable")
        self.tests.append(
            _Function(
                func,
                args=args,
                kwargs=kwargs,
                name=name,
                timeout=timeout,
                max_samples=max_samples,
                min_samples=min_samples,
                cut=cut,
                disable_stdout=disable_stdout,
                verbose=verbose,
                disable_gc=disable_gc,
                batch_size=batch_size,
                live_output=live_output,
                before=before,
                after=after,
            )
        )

    def before(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Global pre-benchmark hook."""
        self._beforeFunc = _BeforeAfter(func, *args, **kwargs)

    def after(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Global post-benchmark hook."""
        self._afterFunc = _BeforeAfter(func, *args, **kwargs)

    def clear(self) -> None:
        self.tests = []

    def get_suite(self) -> Dict[str, Any]:
        """Return suite configuration and registration metadata."""
        return {
            "tests": [t.pretty() for t in self.tests],
            "timeout": self.timeout,
            "max_samples": self.max_samples,
            "min_samples": self.min_samples,
            "cut_percentage": self.cut,
            "disable_stdout": self.disable_stdout,
            "verbose": self.verbose,
            "disable_gc": self.disable_gc,
            "batch_size": self.batch_size,
            "live_output": self.live_output,
            "before": self._beforeFunc.name if self._beforeFunc else None,
            "after": self._afterFunc.name if self._afterFunc else None,
        }

    def _apply_hooks(self) -> None:
        for t in self.tests:
            t.apply_hooks(self._beforeFunc, self._afterFunc)

    def _run_test(self, func: _Function, mute: bool = False) -> Tuple[List[float], int, List[Any], int, int]:
        times: List[float] = []
        total = 0.0
        runs = 0
        results_seq: List[Any] = []
        tail_hash = 0
        _is_hashable: Optional[bool] = None

        # Configuration priority: test > suite
        max_samples = func._max_samples if func._max_samples is not None else self.max_samples
        timeout = func._timeout if func._timeout is not None else self.timeout
        min_samples = func._min_samples if func._min_samples is not None else self.min_samples
        cut = func._cut if func._cut is not None else self.cut
        disable_gc = func._disable_gc if func._disable_gc is not None else self.disable_gc
        batch_size = func._batch_size if func._batch_size is not None else self.batch_size
        live_output = (
            func._live_output if getattr(func, "_live_output", None) is not None else getattr(self, "live_output", True)
        )

        # Calibrate batch size
        if batch_size == 0:
            bs = 1
            t, _ = func(default_batch_size=bs)
            # Scale until batch takes ~2ms (max 1M) to amortize timer overhead
            while t * bs < 0.002 and bs < 1_000_000:
                bs *= 10
                t, _ = func(default_batch_size=bs)
            batch_size = bs

        # Warm-up
        warmup_start = perf_counter()
        for _ in range(self.warmup_samples):
            func(default_batch_size=batch_size)
            if perf_counter() - warmup_start > timeout:
                warnings.warn(
                    f"Warmup phase for '{func.pretty()}' exceeded timeout ({timeout}s), aborting warmup early."
                )
                break

        # Adjust for outlier trimming (cut)
        denominator = 1 - (2 * cut)
        if denominator <= 0:
            actual_max = max_samples
        else:
            actual_max = int(max_samples / denominator)

        if disable_gc:
            gc_was_enabled = gc.isenabled()
            gc.disable()

        try:
            loop_start = perf_counter()
            for _ in range(actual_max):
                t, res = func(default_batch_size=batch_size)
                times.append(t)
                runs += 1

                # Approx time (faster than calling perf_counter every run)
                total += t * batch_size

                if self.validate_responses:
                    if len(results_seq) < self.validate_limit:
                        results_seq.append(res)
                    else:
                        if _is_hashable is None:
                            try:
                                hash(res)
                                _is_hashable = True
                            except TypeError:
                                _is_hashable = False

                        if _is_hashable:
                            tail_hash = hash((tail_hash, res))
                        else:
                            tail_hash = hash((tail_hash, repr(res)))

                elapsed = perf_counter() - loop_start
                if live_output and not mute:
                    # Live status update
                    sys.stdout.write(
                        f"\rBenchmarking {func.pretty()}... {runs * batch_size:,} iterations ({elapsed:.2f}s elapsed)"
                    )
                    sys.stdout.flush()

                if elapsed > timeout and runs >= min_samples:
                    break
        finally:
            if disable_gc and gc_was_enabled:
                gc.enable()

        if live_output and not mute:
            # Preserve final status line
            sys.stdout.write("\n")
            sys.stdout.flush()

        return times, runs, results_seq, tail_hash, batch_size

    def _get_output_details(self, func: _Function, times: List[float], runs: int, batch_size: int) -> BenchmarkResult:
        if not times:
            return BenchmarkResult(
                name=func.pretty(),
                avg=0.0,
                std=0.0,
                median=0.0,
                minimum=0.0,
                maximum=0.0,
                itr_ps=0.0,
                iterations=0,
                counted_iterations=0,
                total_time=0.0,
                verbose=func._verbose if func._verbose is not None else self.verbose,
            )

        s = sorted(times)
        minimum, maximum = s[0], s[-1]

        cut = func._cut if func._cut is not None else self.cut
        start, end = int(runs * cut), int(runs * (1 - cut))
        s = s[start:end]

        verbose = func._verbose if func._verbose is not None else self.verbose

        if not s:
            return BenchmarkResult(
                name=func.pretty(),
                avg=0.0,
                std=0.0,
                median=0.0,
                minimum=minimum,
                maximum=maximum,
                itr_ps=0.0,
                iterations=runs * batch_size,
                counted_iterations=0,
                total_time=sum(t * batch_size for t in times),
                verbose=verbose,
            )

        avg = sum(s) / len(s)
        std = (sum((t - avg) ** 2 for t in s) / len(s)) ** 0.5
        med = s[len(s) // 2]
        total = sum(s)
        itrps = len(s) / total if total > 0 else 0.0

        return BenchmarkResult(
            name=func.pretty(),
            avg=avg,
            std=std,
            median=med,
            minimum=minimum,
            maximum=maximum,
            itr_ps=itrps,
            iterations=runs * batch_size,
            counted_iterations=len(s) * batch_size,
            total_time=sum(t * batch_size for t in times),
            verbose=verbose,
        )

    def run(self) -> BenchmarkResults:
        """Execute all registered benchmarks and return a BenchmarkResults collection."""
        self._apply_hooks()

        if self.validate_responses and len(self.tests) > 1:
            # Warn if args mismatch during validation
            first_args = (self.tests[0].args, self.tests[0].kwargs)
            for t in self.tests[1:]:
                if (t.args, t.kwargs) != first_args:
                    warnings.warn(
                        "validate_responses is enabled but benchmark targets have different arguments. "
                        "This may lead to validation failures.",
                        RuntimeWarning,
                        stacklevel=2,
                    )
                    break

        results = []
        all_sequences: List[Tuple[List[Any], int]] = []

        for func in self.tests:
            mute = func._disable_stdout if func._disable_stdout is not None else self.disable_stdout
            if mute:
                with io.StringIO() as buf, redirect_stdout(buf):
                    times, runs, seq, thash, batch_size = self._run_test(func, mute=mute)
            else:
                times, runs, seq, thash, batch_size = self._run_test(func, mute=mute)

            all_sequences.append((seq, thash))
            results.append(self._get_output_details(func, times, runs, batch_size))

        if self.validate_responses and len(all_sequences) > 1:
            first_seq, first_hash = all_sequences[0]
            for i, (seq, thash) in enumerate(all_sequences[1:], 1):
                # Compare head sequences
                min_len = min(len(first_seq), len(seq))
                if first_seq[:min_len] != seq[:min_len]:
                    raise ValueError(
                        f"Response validation failed between '{self.tests[0].pretty()}' "
                        f"and '{self.tests[i].pretty()}': sequences do not match."
                    )
                # Compare tail hashes if lengths match and are above limit
                if (
                    len(first_seq) >= self.validate_limit
                    and len(seq) >= self.validate_limit
                    and results[0].iterations == results[i].iterations
                ):
                    if first_hash != thash:
                        raise ValueError(
                            f"Response validation failed between '{self.tests[0].pretty()}' "
                            f"and '{self.tests[i].pretty()}': tail hashes do not match."
                        )

        return BenchmarkResults(results)
