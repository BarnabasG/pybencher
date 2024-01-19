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

#### Methods

- `add(func, *args, **kwargs)`: Adds a benchmark test function to the suite.
- `clear()`: Clears the list of benchmark test functions in the suite.
- `set_timeout(t)`: Sets the timeout value for each function in the suite.
- `set_max_itr(n)`: Sets the maximum number of iterations to run each function.
- `set_min_itr(n)`: Sets the minimum number of iterations to run each function.
- `set_cut(n)`: Sets the percentage of iterations to cut off from each end when calculating average time.
- `get_suite()`: Returns a dictionary containing the details of the suite.

## 5. Examples

### Example 1: Adding and running benchmark tests

```python
from pybencher import Suite

# Create a new suite
suite = Suite()

# Define benchmark test functions
def test_func1():
    # Code to be benchmarked
    pass

def test_func2():
    # Code to be benchmarked
    pass

# Add benchmark test functions to the suite
suite.add(test_func1)
suite.add(test_func2)

# Run the benchmark tests
suite.run(verbose=True)
```

This example demonstrates how to create a suite, define benchmark test functions, add them to the suite, and run the tests. The `verbose` parameter is set to `True` to print additional details for each benchmark test.
