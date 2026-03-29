# PyBencher

![GitHub Release](https://img.shields.io/github/v/release/BarnabasG/pybencher) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/pybencher?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/pybencher) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/BarnabasG/pybencher/ci.yml)

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

# Custom configuration using 'bench_' prefix
@suite.bench(bench_name="Fast Math", bench_max_itr=5000)
def fast():
    return 1 + 1

# Positional and keyword arguments are passed directly
@suite.bench(10, 20, bench_name="Add")
def add(a, b):
    return a + b

# Run and print results
results = suite.run()
results.print()

# Manual registration (equivalent to @suite.bench)
def manual_func(n):
    return sum(range(n))

suite.add(manual_func, 1000, bench_name="Manual Register")
```

## Configuration Overrides

Any setting in the `Suite` can be overridden for a specific benchmark by prefixing it with `bench_`. This ensures that benchmark configuration does not interfere with your function's own parameters (e.g., using `timeout=0.5` as a function argument while setting `bench_timeout=5.0` for the suite).

| Override | Type | Description |
| --- | --- | --- |
| `bench_name` | `str` | Display name in reports |
| `bench_timeout` | `float` | Per-test time limit in seconds |
| `bench_max_itr` | `int` | Maximum execution count |
| `bench_min_itr` | `int` | Minimum execution count |
| `bench_cut` | `float` | Percentage of outliers to trim (0.0 to 0.5) |
| `bench_disable_stdout` | `bool` | Mute `print()` output inside the target |
| `bench_verbose` | `bool` | Include extra stats in `results.print()` |
| `bench_before` | `callable` | Local setup hook |
| `bench_after` | `callable` | Local teardown hook |

## Reference

### `Suite`

- `timeout` (float): Default time limit (10s).
- `max_itr` (int): Default max runs (1000).
- `min_itr` (int): Default min runs (3).
- `cut` (float): Default outlier threshold (0.05).
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

# 'timeout' here is a function param, not the benchmark limit
@suite.bench(timeout=0.1, bench_name="Sleepy", bench_verbose=True)
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