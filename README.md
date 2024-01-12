### python-benchmarker - Python Benchmarking Suite

python-benchmarker exposes a class 'Suite' that allows adding functions and arguments to a benchmark suite which can then be run to benchmark performance.
After adding your functions and arguments to the suite instance, call suite.run() to trigger the benchmark tests.


verbose=True on suite.run() provides additional ececution information including standard deviation, minimum and maximum execuion times, and total execution time.

maximum iterations, minimum iterations, run timeout, and percentage of times to cut (fastest and slowest) can be modifies and viewed with suite.get_suite()
 - maximum iterations is recorded function calls after cutting fastest and slowest - max_itr=1000 with cut=0.1 will run the function 1250 times and cut the top and bottom 125
 - minimum iterations takes priority over timeout and defaults to 3 runs
 - timout is only checked after the end of a function call, a long running or infinite function will not time out
