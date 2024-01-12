from datetime import datetime as dt
from timeit import default_timer as timer

class Function:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.name = func.__name__
    
    def __call__(self):
        return self.func(*self.args, **self.kwargs)
    
    def __hash__(self):
        return hash(tuple([self.func.__name__, self.args, self.kwargs.items()]))
    
    def pretty(self):
        return f'{self.name}({", ".join([str(a) for a in self.args])}{", " if self.args and self.kwargs else ""}{", ".join([f"{k}={v}" for k, v in self.kwargs.items()])})'


class Suite:
    def __init__(self):
        self.tests = []
        self.units = {
            'ps': 1e-12,
            'ns': 1e-9,
            'μs': 1e-6,
            'ms': 1e-3,
            's': 1,
        }
        self.timeout = 10
        self.max_itr = 1000
        self.min_itr = 3
        # self.function_inputs = {}
    
    def __hash__(self):
        return hash(tuple(self.tests))
    
    def hash_func(self, func, args, kwargs):
        return hash(tuple([func.__name__, args, kwargs]))

    def set_timeout(self, t):
        self.timeout = t
    
    def set_max_itr(self, n):
        self.max_itr = n

    def set_min_itr(self, n):
        self.min_itr = n

    def add(self, func, *args, **kwargs):
        if not callable(func):
            raise TypeError('must be a function')
        # if args or kwargs:
        #     self.function_inputs[self.hash_func(func, args, kwargs.items())] = (args, kwargs)
        self.tests.append(Function(func, *args, **kwargs))
    
    def get_suite(self):
        return {
            'tests': [t.pretty() for t in self.tests],
            'timeout': self.timeout,
            'max_itr': self.max_itr,
            'min_itr': self.min_itr,
        }
    
    def run_test(self, func):
        times = []
        total_time = 0
        executions = 0
        for _ in range(self.max_itr):
            start = timer()
            func()
            end = timer()
            times.append(end - start)
            total_time += end - start
            executions += 1
            if total_time > self.timeout:
                break
        return times, executions
    
    def pretty_time(self, t):
        for unit, ratio in self.units.items():
            factor = 59.95 if unit == 's' else 999.5
            if t < factor * ratio:
                num = f'{t/ratio:#.3g}'.rstrip('.')
                return f'{num}{unit}'
        return str(dt.timedelta(seconds=int(round(t)))).removeprefix('0:')
    
    def get_output_details(self, times, executions):
        times.sort()
        # remove top and bottom 10%
        times = times[int(executions*.1):int(executions*.9)]
        avg = sum(times) / len(times)
        std = (sum((t - avg)**2 for t in times) / len(times))**.5
        med = times[int(len(times)/2)]
        minimum = times[0]
        maximum = times[-1]
        return {
            'avg': avg,
            'std': std,
            'median': med,
            'minimum': minimum,
            'maximum': maximum,
            'iterations': executions
        }
        
    def run(self, verbose=False):
        print(f'Running tests {[t.name for t in self.tests]}')
        for func in self.tests:
            times, executions = self.run_test(func)
            details = self.get_output_details(times, executions)
            print(f'{func.name}: {self.pretty_time(details["avg"])}/itr ({details["iterations"]} itr)')
            if verbose:
                if func.args or func.kwargs:
                    print(f'  args: {func.args}')
                    print(f'  kwargs: {func.kwargs}')
                print(f'  std: {self.pretty_time(details["std"])}')
                print(f'  median: {self.pretty_time(details["median"])}')
                print(f'  minimum: {self.pretty_time(details["minimum"])}')
                print(f'  maximum: {self.pretty_time(details["maximum"])}')
                print(f'  iterations: {details["iterations"]}')

