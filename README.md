# PyBencher

![GitHub Release](https://img.shields.io/github/v/release/BarnabasG/pybencher) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/pybencher?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/pybencher) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/BarnabasG/pybencher/pipeline.yml)

PyBencher is a simple, decorator-based benchmarking suite for Python. It provides detailed timing statistics (average, median, standard deviation) and supports per-test configuration overrides.

## Installation

```bash
pip install pybencher
```

## Basic Usage

```python
from pybencher import Suite

suite = Suite()

# Quick registration
@suite.bench()
def my_function():
    return sum(range(10000))

# Per-benchmark configuration
@suite.bench(name="Fast Math", max_itr=5000)
def fast():
    return 1 + 1

# Function arguments via args / kwargs
@suite.bench(args=(10, 20), name="Add")
def add(a, b):
    return a + b

# Manual registration (equivalent to @suite.bench)
def manual_func(n):
    return sum(range(n))

suite.add(manual_func, args=(1000,), name="Manual Register")

# Run and print results
results = suite.run()
results.print()
```

## Configuration Overrides

Any setting in the `Suite` can be overridden per-benchmark via keyword arguments to `bench()` or `add()`. Function inputs are separated cleanly into the `args` and `kwargs` parameters.

| Override | Type | Description |
| --- | --- | --- |
| `name` | `str` | Display name in reports |
| `timeout` | `float` | Per-test time limit in seconds |
| `max_itr` | `int` | Maximum execution count |
| `min_itr` | `int` | Minimum execution count |
| `cut` | `float` | Percentage of outliers to trim (0.0 to 0.5) |
| `disable_stdout` | `bool` | Mute `print()` output inside the target |
| `verbose` | `bool` | Include extra stats in `results.print()` |
| `before` | `callable` | Local setup hook |
| `after` | `callable` | Local teardown hook |
| `args` | `tuple` | Positional arguments for the target function |
| `kwargs` | `dict` | Keyword arguments for the target function |

## Reference

### `Suite`

- `timeout` (float): Default time limit (10s).
- `max_itr` (int): Default max runs (1000).
- `min_itr` (int): Default min runs (3).
- `cut` (float): Default outlier threshold (0.05).
- `warmup_itr` (int): Number of unmeasured runs to perform before benchmarking (0).
- `validate_responses` (bool): Enable cross-test output consistency checks (False).
- `validate_limit` (int): Max number of iterations to store for full sequence validation (10,000).
- `disable_stdout` (bool): Global stdout suppressor.
- `verbose` (bool): Global verbosity flag.

### `BenchmarkResults`

- `print(verbose=None)`: Print results to console. 
- `to_json(indent=4)`: Export results to JSON.
- `to_list()`: Export results to list of dicts.

### `BenchmarkResult`

Dataclass containing:
- `name`: Target name or custom override.
- `avg`, `std`, `median`, `minimum`, `maximum`: Timing stats in seconds.
- `itr_ps`: Iterations per second.
- `iterations`: Total runs.
- `counted_iterations`: Runs used for stats after trimming outliers.

## Example

```python
from pybencher import Suite

suite = Suite()

# 'timeout' here is a benchmark config override, not a function param
@suite.bench(args=(0.1,), name="Sleepy", verbose=True)
def test_sleep(duration):
    import time
    time.sleep(duration)

# Function kwargs stay separate from benchmark config
@suite.bench(kwargs={"timeout": 0.1}, name="Sleepy Alt", verbose=True)
def test_args(timeout):
    import time
    time.sleep(timeout)

results = suite.run()
results.print()
```

### Output:
```text
Sleepy: 100ms/itr | 10.0 itr/s
  std:     120us
  median:  100ms
  min/max: 99ms / 101ms
  runs:    10 (10 counted)
  total:   1.01s
```

## CI/CD Pipeline

PyBencher uses an automated GitHub Actions pipeline:
- **Testing**: Every push to any branch triggers a full test suite across Linux, Windows, and macOS for Python 3.10–3.14.
- **Publishing**: Pushes to `main` automatically publish to PyPI **if and only if** all tests pass.