import io
import json
import warnings
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from datetime import timedelta
from time import perf_counter
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple


@dataclass(frozen=True)
class BenchmarkResult:
    """Benchmark execution results and stats."""

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
    """Collection of results with export utilities."""

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
        """Format and print results to stdout."""
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
        return str(timedelta(seconds=int(round(t)))).removeprefix("0:")


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

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        # Configuration overrides
        self.bench_timeout: Optional[float] = kwargs.pop("bench_timeout", None)
        self.bench_max_itr: Optional[int] = kwargs.pop("bench_max_itr", None)
        self.bench_min_itr: Optional[int] = kwargs.pop("bench_min_itr", None)
        self.bench_cut: Optional[float] = kwargs.pop("bench_cut", None)
        self.bench_name: Optional[str] = kwargs.pop("bench_name", None)
        self.bench_disable_stdout: Optional[bool] = kwargs.pop("bench_disable_stdout", None)
        self.bench_verbose: Optional[bool] = kwargs.pop("bench_verbose", None)
        self.bench_before: Optional[Callable[..., Any]] = kwargs.pop("bench_before", None)
        self.bench_after: Optional[Callable[..., Any]] = kwargs.pop("bench_after", None)

        self.func = func
        self.before: Optional[_BeforeAfter] = None
        self.after: Optional[_BeforeAfter] = None
        self.args = args
        self.kwargs = kwargs
        self.name = func.__name__

    def before_after(self, before: Optional[_BeforeAfter] = None, after: Optional[_BeforeAfter] = None) -> None:
        """Apply test-specific or suite-level hooks."""
        self.before = _BeforeAfter(self.bench_before) if self.bench_before else before
        self.after = _BeforeAfter(self.bench_after) if self.bench_after else after

    def __call__(self) -> Tuple[float, Any]:
        """Run function once and return elapsed time."""
        if self.before:
            self.before()
        start = perf_counter()
        res = self.func(*self.args, **self.kwargs)
        duration = perf_counter() - start
        if self.after:
            self.after()
        return duration, res

    def __hash__(self) -> int:
        return hash(tuple([self.name, self.args, tuple(self.kwargs.items())]))

    def pretty(self) -> str:
        """String representation of the call."""
        if self.bench_name:
            return self.bench_name
        args_str = ", ".join([str(a) for a in self.args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in self.kwargs.items()])
        sep = ", " if self.args and self.kwargs else ""
        return f"{self.name}({args_str}{sep}{kwargs_str})"


class Suite:
    """Benchmarking suite for registering and running tests."""

    def __init__(self, max_itr: int = 1000, timeout: float = 10.0) -> None:
        self.tests: List[_Function] = []
        self.timeout = timeout
        self.max_itr = max_itr
        self.min_itr = 3
        self.cut = 0.05
        self.disable_stdout = False
        self.verbose = False
        self.warmup_itr = 0
        self.validate_responses = False
        self.validate_limit = 10000
        self._beforeFunc: Optional[_BeforeAfter] = None
        self._afterFunc: Optional[_BeforeAfter] = None

    def bench(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a benchmark function."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add(func, *args, **kwargs)
            return func

        return decorator

    def set_timeout(self, t: float) -> None:
        self.timeout = t

    def set_max_itr(self, n: int) -> None:
        self.max_itr = n

    def set_min_itr(self, n: int) -> None:
        self.min_itr = n

    def set_cut(self, n: float) -> None:
        self.cut = n

    def set_warmup_itr(self, n: int) -> None:
        self.warmup_itr = n

    def set_validate_responses(self, val: bool) -> None:
        self.validate_responses = val

    def set_validate_limit(self, n: int) -> None:
        self.validate_limit = n

    def add(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Add a function to the suite."""
        if not callable(func):
            raise TypeError("Benchmark target must be callable")
        self.tests.append(_Function(func, *args, **kwargs))

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
            "max_itr": self.max_itr,
            "min_itr": self.min_itr,
            "cut_percentage": self.cut,
            "disable_stdout": self.disable_stdout,
            "verbose": self.verbose,
            "before": self._beforeFunc.name if self._beforeFunc else None,
            "after": self._afterFunc.name if self._afterFunc else None,
        }

    def _apply_before_after(self) -> None:
        for t in self.tests:
            t.before_after(self._beforeFunc, self._afterFunc)

    def _run_test(self, func: _Function) -> Tuple[List[float], int, List[Any], int]:
        times = []
        total = 0.0
        runs = 0
        results_seq: List[Any] = []
        tail_hash = 0

        # Configuration priority: test override > suite default
        max_itr = func.bench_max_itr if func.bench_max_itr is not None else self.max_itr
        timeout = func.bench_timeout if func.bench_timeout is not None else self.timeout
        min_itr = func.bench_min_itr if func.bench_min_itr is not None else self.min_itr
        cut = func.bench_cut if func.bench_cut is not None else self.cut

        # Warm-up phase
        for _ in range(self.warmup_itr):
            func()

        actual_max = int(max_itr / (1 - (2 * cut)))
        for _ in range(actual_max):
            t, res = func()
            times.append(t)
            total += t
            runs += 1

            if self.validate_responses:
                if len(results_seq) < self.validate_limit:
                    results_seq.append(res)
                else:
                    tail_hash = hash((tail_hash, res))

            if total > timeout and runs >= min_itr:
                break
        return times, runs, results_seq, tail_hash

    def _get_output_details(self, func: _Function, times: List[float], runs: int) -> BenchmarkResult:
        s = sorted(times)
        minimum, maximum = s[0], s[-1]

        cut = func.bench_cut if func.bench_cut is not None else self.cut
        start, end = int(runs * cut), int(runs * (1 - cut))
        s = s[start:end] if start < end else s

        if not s:
            return BenchmarkResult(
                name=func.pretty(),
                avg=0.0,
                std=0.0,
                median=0.0,
                minimum=minimum,
                maximum=maximum,
                itr_ps=0.0,
                iterations=runs,
                counted_iterations=0,
                total_time=sum(times),
                verbose=func.bench_verbose if func.bench_verbose is not None else self.verbose,
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
            iterations=runs,
            counted_iterations=len(s),
            total_time=sum(times),
            verbose=func.bench_verbose if func.bench_verbose is not None else self.verbose,
        )

    def run(self) -> BenchmarkResults:
        """Run registered tests and return results."""
        self._apply_before_after()

        if self.validate_responses and len(self.tests) > 1:
            # Check for inconsistent args/kwargs
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
            mute = func.bench_disable_stdout if func.bench_disable_stdout is not None else self.disable_stdout
            if mute:
                with io.StringIO() as buf, redirect_stdout(buf):
                    times, runs, seq, thash = self._run_test(func)
            else:
                times, runs, seq, thash = self._run_test(func)

            all_sequences.append((seq, thash))
            results.append(self._get_output_details(func, times, runs))

        if self.validate_responses and len(all_sequences) > 1:
            first_seq, first_hash = all_sequences[0]
            for i, (seq, thash) in enumerate(all_sequences[1:], 1):
                # Compare sequences up to minimum length
                min_len = min(len(first_seq), len(seq))
                if first_seq[:min_len] != seq[:min_len]:
                    raise ValueError(
                        f"Response validation failed between '{self.tests[0].pretty()}' "
                        f"and '{self.tests[i].pretty()}': sequences do not match."
                    )
                # Compare hashes ONLY if both reached the same length beyond the limit
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
