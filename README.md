### pybencher - Python Benchmarking Suite

pybencher exposes a class `Suite` that allows adding functions and arguments to a benchmark suite which can then be run to benchmark performance.
To use pybencher, simply create a `Suite` instance and `Suite.add` your functions and arguments. Then call `Suite.run()` to trigger the benchmark tests.


By setting `verbose=True` on `Suite.run()`, additional ececution information including standard deviation, minimum and maximum execuion times, and total execution time is displayed.

maximum iterations, minimum iterations, run timeout, and percentage of times to cut (fastest and slowest) can be modified and viewed with `Suite.get_suite()`
 - maximum iterations is recorded function calls after cutting fastest and slowest - `max_itr=1000` with `cut=0.1` will run the function 1250 times and cut the top and bottom 125
 - minimum iterations takes priority over timeout and defaults to 3 runs
 - timout is only checked after the end of a function call, a long running or infinite functions will not time out
