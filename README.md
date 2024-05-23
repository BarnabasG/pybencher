# PyBencher - Python Bechmarker

## 1. Introduction

PyBencher is a Python package that provides a suite of benchmark tests for measuring the performance of code snippets or functions. It allows you to easily define and run benchmark tests, and provides detailed timing information for analysis and comparison.

The `Suite` class represents a suite of benchmark tests. It allows you to add benchmark test functions, set various parameters, and run the tests.

## 2. Installation

To install PyBencher, you can use pip, the Python package manager. Open a terminal or command prompt and run the following command:

```
pip install pybencher
```

## 3. Usage

To use the `Suite` class in your Python script or module, you need to import it first. Here's an example:

```python
from pybencher import Suite
```

Once you have imported the `Suite` class, you can create an instance of it as follows:

```python
suite = Suite()
```

## 4. Class Reference

### `Suite`

#### Attributes

- `timeout` (float): The number of seconds to run each function before exiting early. Timout is only checked after the end of a function call, a long running or infinite functions will not time out.
- `max_itr` (int): The maximum number of iterations to run each function. Maximum iterations is recorded function calls after cutting fastest and slowest. `max_itr=1000` with `cut=0.1` will run the function 1250 times and cut the top and bottom 125. Defaults to 1000 runs.
- `min_itr` (int): The minimum number of iterations to run each function. Takes priority over timeout and defaults to 3 runs.
- `cut` (float): The percentage of iterations to cut off from each end when calculating average time.
- `disable_stdout` (bool): If `True`, disables stdout. Defaults to `False`.
- `verbose` (bool): If `True`, prints additional details for each benchmark test. Defaults to `False`.


#### Methods

- `add(func, *args, **kwargs)`: Adds a benchmark test function to the suite.
- `before(func, *args, **kwargs)`: Provide a function to run before each test.
- `after(func, *args, **kwargs)`: Provide a function to run after each test.
- `clear()`: Clears the list of benchmark test functions in the suite.
- `set_timeout(t)`: Sets the timeout value for each function in the suite.
- `set_max_itr(n)`: Sets the maximum number of iterations to run each function.
- `set_min_itr(n)`: Sets the minimum number of iterations to run each function.
- `set_cut(n)`: Sets the percentage of iterations to cut off from each end when calculating average time.
- `get_suite()`: Returns a dictionary containing the details of the suite.

## 5. Code Example

```python
from src.pybencher import Suite

# Define some functions to benchmark
def foo():
    x = 0
    for _ in range(10000):
        x+=1

def bar():
    print('hi')

def baz():
    pass

def quux():
    x = ''
    for i in range(10000):
        x += chr(i%256)

def quuz():
    x = []
    for i in range(10000):
        x.append(i)

def argskwargs(*args, **kwargs):
    total = sum(args)
    for value in kwargs.values():
        total += value
    return total

from random import random
from time import sleep
def random_sleep():
    sleep(random()/1000)


shared_list_1 = ["hi", 0.5]*10000
shared_list_2 = [True, 9999999]*10000

def cleanup():
    shared_list_1.append("ho")
    shared_list_2.append(False)
    print(f"Shared list 1 length: {len(shared_list_1)}, Shared list 2 length {len(shared_list_2)}")
    return shared_list_1.extend(shared_list_2)

def beforeSetup():
    global shared_list_1, shared_list_2
    shared_list_1 = ["hi", 0.5]*10000
    shared_list_2 = [True, 9999999]*10000

def afterCleanup():
    global shared_list_1, shared_list_2
    shared_list_1 = []
    shared_list_2 = []

# Create a new suite
suite1 = Suite()

# Disable stdout
suite1.disable_stdout = True

# Add the functions to the suite
suite1.add(foo)
suite1.add(bar)
suite1.add(baz)
suite1.add(quux)
suite1.add(quuz)
suite1.add(argskwargs, 1, 2, 3, a=4, b=5, c=6)
suite1.add(argskwargs, 1, 2, 3)
suite1.add(argskwargs, a=4, b=5, c=6)
suite1.add(argskwargs)
suite1.add(random_sleep)

# Create a second suite
suite2 = Suite()

# Set the maximum number of iterations for the suite
suite2.set_max_itr(5)

# Set the verbose flag to True to print additional details for each benchmark test
suite2.verbose = True

# Add the functions to the suite
suite2.add(cleanup)

# Set functions to run before and after each test function execution
suite2.before(beforeSetup)
suite2.after(afterCleanup)

print(suite1.get_suite())
suite1.run()

print()

print(suite2.get_suite())
suite2.run()
```
