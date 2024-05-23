from datetime import datetime as dt
from time import perf_counter

from contextlib import redirect_stdout
import io
from typing import Any, Dict, List, Optional, Tuple

class _BeforeAfter:
    """
    A class representing a function to be run before or after a benchmark test.
    """
    def __init__(self, func: Any, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.name = func.__name__
    
    def __call__(self) -> None:
        return self.func(*self.args, **self.kwargs)
    
    def __hash__(self):
        return hash(tuple([self.func.__name__, self.args, tuple(self.kwargs.items())]))

class _Function:
    """
    A class representing a benchmark test function.
    """
    def __init__(self, func: Any, *args, **kwargs):
        self.func = func
        self.before = None
        self.after = None
        self.args = args
        self.kwargs = kwargs
        self.name = func.__name__
    
    def beforeAfter(self, before: Optional[_BeforeAfter]=None, after: Optional[_BeforeAfter]=None):
        self.before = before
        self.after = after
    
    def __call__(self) -> Tuple[float, Any]:
        if self.before:
            self.before()
        start_time = perf_counter()
        result = self.func(*self.args, **self.kwargs)
        end_time = perf_counter()
        if self.after:
            self.after()
        return end_time - start_time, result
    
    def __hash__(self):
        return hash(tuple([self.name, self.args, tuple(self.kwargs.items())]))
    
    def pretty(self):
        return f'{self.name}({", ".join([str(a) for a in self.args])}{", " if self.args and self.kwargs else ""}{", ".join([f"{k}={v}" for k, v in self.kwargs.items()])})'


class Suite:
    """
    A class representing a suite of benchmark tests.
    """
    def __init__(self) -> None:
        self.tests = []
        self.units = {
            'ps': 1e-12,
            'ns': 1e-9,
            'us': 1e-6,
            'ms': 1e-3,
            's': 1,
        }
        # Number of seconds to run each function before exiting early
        self.timeout = 10
        # Maximum number of iterations to run each function
        self.max_itr = 1000
        # Minimum number of iterations to run each function
        self.min_itr = 3
        # Percentage of iterations to cut off from each end when calculating average time
        self.cut = 0.05
        # If True, disables stdout. Defaults to False.
        self.disable_stdout = False
        # If True, prints additional details for each benchmark test. Defaults to False.
        self.verbose = False

        self._beforeFunc = None
        self._afterFunc = None
    
    def __hash__(self) -> int:
        return hash(tuple([t.__hash__() for t in self.tests]))

    def set_timeout(self, t: float) -> None:
        self.timeout = t
    
    def set_max_itr(self, n: int) -> None:
        self.max_itr = n

    def set_min_itr(self, n: int) -> None:
        self.min_itr = n
    
    def set_cut(self, n: int) -> None:
        self.cut = n

    def add(self, func: Any, *args, **kwargs) -> None:
        """
        Adds a benchmark test function to the suite.
        
        Args:
            func (function): The benchmark test function to be added.
            *args: Variable-length arguments to be passed to the benchmark test function.
            **kwargs: Keyword arguments to be passed to the benchmark test function.
        
        Raises:
            TypeError: If the provided `func` is not callable.
        """
        if not callable(func):
            raise TypeError('must be a function')
        self.tests.append(_Function(func, *args, **kwargs))
    
    def before(self, func: Any, *args, **kwargs) -> None:
        """
        Sets a function to be run before each benchmark test in the suite.
        """
        self._beforeFunc = _BeforeAfter(func, *args, **kwargs)
    
    def after(self, func: Any, *args, **kwargs) -> None:
        """
        Sets a function to be run after each benchmark test in the suite.
        """
        self._afterFunc = _BeforeAfter(func, *args, **kwargs)
    
    def clear(self) -> None:
        """
        Clears the list of benchmark test functions in the suite.
        """
        self.tests = []
    
    def get_suite(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing the details of the suite.
        
        Returns:
            dict: A dictionary containing the details of the suite, including the list of benchmark tests,
                  timeout value, maximum number of iterations, minimum number of iterations, and cut percentage.
        """
        return {
            'tests': [t.pretty() for t in self.tests],
            'timeout': self.timeout,
            'max_itr': self.max_itr,
            'min_itr': self.min_itr,
            'cut_percentage': self.cut,
            'disable_stdout': self.disable_stdout,
            'verbose': self.verbose,
            'before': self._beforeFunc.name if self._beforeFunc else None,
            'after': self._afterFunc.name if self._afterFunc else None
        }

    def _setup(self) -> None:
        """
        Sets up the benchmark tests in the suite.
        """
        self._applyBeforeAfter()
    
    def _applyBeforeAfter(self):
        """
        Applies the before and after functions to each test in the suite.
        """
        for test in self.tests:
            test.beforeAfter(self._beforeFunc, self._afterFunc)
    
    def _run_test(self, func: _Function) -> Tuple[List[float], int]:
        times = []
        total_time = 0
        executions = 0
        actual_max_runs = int(self.max_itr / (1-(2*self.cut)))
        for _ in range(actual_max_runs):
            t, _ = func()
            times.append(t)
            total_time += t
            executions += 1
            if total_time > self.timeout and executions >= self.min_itr:
                break
        return times, executions
    
    def _pretty_time(self, t: float) -> str:
        for unit, ratio in self.units.items():
            factor = 59.95 if unit == 's' else 999.5
            if t < factor * ratio:
                num = f'{t/ratio:#.3g}'.rstrip('.')
                return f'{num}{unit}'
        return str(dt.timedelta(seconds=int(round(t)))).removeprefix('0:')
    
    def _get_output_details(self, times: List[float], executions: int) -> Dict[str, Any]:
        s = sorted(times)
        minimum = s[0]
        maximum = s[-1]
        s = s[int(executions*self.cut):int(executions*(1-self.cut))]
        avg = sum(s) / len(s)
        std = (sum((t - avg)**2 for t in s) / len(s))**.5
        med = s[int(len(s)/2)]
        itrps = len(s) / sum(s)
        itrps = int(itrps) if itrps > 10 else round(itrps,2)
        return {
            'avg': avg,
            'std': std,
            'median': med,
            'minimum': minimum,
            'maximum': maximum,
            'itr_ps': itrps,
            'iterations': executions,
            'counted_iterations': len(s),
        }
        
    def run(self) -> None:
        """
        Runs the benchmark tests in the suite and prints the results.
        """
        print(f'Running tests {[t.name for t in self.tests]}')
        self._setup()
        for func in self.tests:
            if self.disable_stdout:
                with io.StringIO() as buf, redirect_stdout(buf):
                    times, executions = self._run_test(func)
            else:
                times, executions = self._run_test(func)
            details = self._get_output_details(times, executions)
            print(f'{func.name}: {self._pretty_time(details["avg"])}/itr | {details["itr_ps"]} itr/s')
            if self.verbose:
                if func.args or func.kwargs:
                    print(f'  args: {func.args}')
                    print(f'  kwargs: {func.kwargs}')
                print(f'  std: {self._pretty_time(details["std"])}')
                print(f'  median: {self._pretty_time(details["median"])}')
                print(f'  minimum: {self._pretty_time(details["minimum"])}')
                print(f'  maximum: {self._pretty_time(details["maximum"])}')
                print(f'  iterations: {details["iterations"]}')
                print(f'  counted iterations: {details["counted_iterations"]}')
                print(f'  total time: {self._pretty_time(sum(times))}')
