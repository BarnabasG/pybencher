from datetime import datetime as dt
from timeit import default_timer as timer

class _Function:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.name = func.__name__
    
    def __call__(self):
        return self.func(*self.args, **self.kwargs)
    
    def __hash__(self):
        return hash(tuple([self.name, self.args, tuple(self.kwargs.items())]))
    
    def pretty(self):
        return f'{self.name}({", ".join([str(a) for a in self.args])}{", " if self.args and self.kwargs else ""}{", ".join([f"{k}={v}" for k, v in self.kwargs.items()])})'


class Suite:
    """
    A class representing a suite of benchmark tests.
    """

    def __init__(self):
        self.tests = []
        self.units = {
            'ps': 1e-12,
            'ns': 1e-9,
            'μs': 1e-6,
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
    
    def __hash__(self):
        return hash(tuple([t.__hash__() for t in self.tests]))

    def set_timeout(self, t):
        self.timeout = t
    
    def set_max_itr(self, n):
        self.max_itr = n

    def set_min_itr(self, n):
        self.min_itr = n
    
    def set_cut(self, n):
        self.cut = n

    def add(self, func, *args, **kwargs):
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
    
    def clear(self):
        """
        Clears the list of benchmark test functions in the suite.
        """
        self.tests = []
    
    def get_suite(self):
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
            'cut percentage': self.cut
        }
    
    def _run_test(self, func):
        times = []
        total_time = 0
        executions = 0
        actual_max_runs = int(self.max_itr / (1-(2*self.cut)))
        for _ in range(actual_max_runs):
            start = timer()
            func()
            end = timer()
            times.append(end - start)
            total_time += end - start
            executions += 1
            if total_time > self.timeout and executions >= self.min_itr:
                break
        return times, executions
    
    def _pretty_time(self, t):
        for unit, ratio in self.units.items():
            factor = 59.95 if unit == 's' else 999.5
            if t < factor * ratio:
                num = f'{t/ratio:#.3g}'.rstrip('.')
                return f'{num}{unit}'
        return str(dt.timedelta(seconds=int(round(t)))).removeprefix('0:')
    
    def _get_output_details(self, times, executions):
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
        
    def run(self, verbose=False):
        """
        Runs the benchmark tests in the suite and prints the results.
        
        Args:
            verbose (bool, optional): If True, prints additional details for each benchmark test. 
                                    Defaults to False.
        """
        print(f'Running tests {[t.name for t in self.tests]}')
        for func in self.tests:
            times, executions = self._run_test(func)
            details = self._get_output_details(times, executions)
            print(f'{func.name}: {self._pretty_time(details["avg"])}/itr | {details['itr_ps']} itr/s')
            if verbose:
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
