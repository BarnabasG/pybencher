from typing import Callable
import pytest

from pybencher import Suite


def test_initialization() -> None:
    """Default values test."""
    suite = Suite()
    assert suite.tests == []
    assert suite.timeout == 10
    assert suite.max_itr == 1000


def test_add_function() -> None:
    """Manual function registration."""

    def foo() -> None:
        pass

    suite = Suite()
    suite.add(foo)
    assert len(suite.tests) == 1
    assert suite.tests[0].func_name == "foo"


def test_decorator_registration() -> None:
    """Decorator registration."""
    suite = Suite()

    @suite.bench()
    def foo() -> None:
        pass

    assert len(suite.tests) == 1
    assert suite.tests[0].func_name == "foo"


def test_name_override() -> None:
    """Custom benchmark name."""
    suite = Suite()

    @suite.bench(name="Custom Name")
    def foo() -> None:
        pass

    results = suite.run()
    assert results[0].name == "Custom Name"


def test_decorator_arguments() -> None:
    """Passing positional and keyword arguments."""
    suite = Suite()

    @suite.bench(args=(1, 2), kwargs={"c": 3})
    def foo(a: int, b: int, c: int) -> int:
        return a + b + c

    results = suite.run()
    assert "foo" in results[0].name


def test_config_override() -> None:
    """Per-test configuration priority."""
    suite = Suite(max_itr=100)

    @suite.bench(max_itr=5, cut=0.0)
    def foo() -> None:
        pass

    results = suite.run()
    assert results[0].iterations == 5


def test_function_args_separated_from_config() -> None:
    """Ensure function args and config are cleanly separated."""
    suite = Suite()
    suite.set_max_itr(1)

    @suite.bench(kwargs={"timeout": 0.123}, timeout=5.0)
    def foo(timeout: float) -> float:
        return timeout

    results = suite.run()
    assert results[0].iterations == 1


def test_stdout_suppression(capsys: pytest.CaptureFixture[str]) -> None:
    """Stdout muting."""
    suite = Suite()
    suite.set_max_itr(1)

    @suite.bench(disable_stdout=True)
    def noisy() -> None:
        print("SECRET")

    suite.run()
    assert "SECRET" not in capsys.readouterr().out


def test_run_data_return() -> None:
    """Programmatic results access."""
    suite = Suite()
    suite.set_max_itr(5)
    suite.set_cut(0.0)

    def foo() -> int:
        return 1

    suite.add(foo)
    results = suite.run()

    assert len(results) == 1
    assert "foo" in results[0].name
    assert results[0].iterations == 5


def test_before_after_hooks(results_list: list[str]) -> None:
    """Global and per-test setup/teardown hooks."""

    def before() -> None:
        results_list.append("before")

    def after() -> None:
        results_list.append("after")

    def foo() -> None:
        results_list.append("foo")

    suite = Suite()
    suite.set_max_itr(1)
    suite.set_cut(0.0)
    suite.before(before)
    suite.after(after)
    suite.add(foo)
    suite.run()

    assert results_list == ["before", "foo", "after"]


def test_get_suite_metadata() -> None:
    """Suite configuration inspection."""
    suite = Suite()

    def foo() -> None:
        pass

    suite.add(foo)
    details = suite.get_suite()
    assert details["tests"] == ["foo()"]
    assert details["max_itr"] == 1000


def test_result_serialization() -> None:
    """to_dict, to_list, to_json, and repr."""
    suite = Suite()
    suite.set_max_itr(3)
    suite.set_cut(0.0)
    suite.add(lambda: 1, name="ser")
    results = suite.run()

    d = results[0].to_dict()
    assert d["name"] == "ser"

    lst = results.to_list()
    assert isinstance(lst, list) and lst[0]["name"] == "ser"

    j = results.to_json()
    assert '"ser"' in j

    assert "ser" in repr(results[0])


def test_results_iteration() -> None:
    """__iter__ and __len__."""
    suite = Suite()
    suite.set_max_itr(1)
    suite.set_cut(0.0)
    suite.add(lambda: 1, name="a")
    suite.add(lambda: 2, name="b")
    results = suite.run()

    names = [r.name for r in results]
    assert names == ["a", "b"]
    assert len(results) == 2


def test_print_output(capsys: pytest.CaptureFixture[str]) -> None:
    """print() with verbose and non-verbose."""
    suite = Suite()
    suite.set_max_itr(3)
    suite.set_cut(0.0)
    suite.add(lambda: 1, name="p", verbose=True)
    results = suite.run()

    results.print()
    out = capsys.readouterr().out
    assert "p:" in out
    assert "std:" in out
    assert "median:" in out

    # Non-verbose
    suite2 = Suite()
    suite2.set_max_itr(3)
    suite2.set_cut(0.0)
    suite2.add(lambda: 1, name="q")
    results2 = suite2.run()
    results2.print()
    out2 = capsys.readouterr().out
    assert "q:" in out2
    assert "std:" not in out2


def test_print_verbose_override(capsys: pytest.CaptureFixture[str]) -> None:
    """print(verbose=True) overrides per-result setting."""
    suite = Suite()
    suite.set_max_itr(3)
    suite.set_cut(0.0)
    suite.add(lambda: 1, name="v")
    results = suite.run()

    results.print(verbose=True)
    out = capsys.readouterr().out
    assert "std:" in out


def test_set_timeout_and_min_itr() -> None:
    """set_timeout and set_min_itr setters."""
    suite = Suite()
    suite.set_timeout(0.001)
    suite.set_min_itr(1)
    suite.set_cut(0.0)
    suite.add(lambda: 1)
    results = suite.run()
    assert results[0].iterations >= 1


def test_clear() -> None:
    """clear() empties the test list."""
    suite = Suite()
    suite.add(lambda: 1)
    assert len(suite.tests) == 1
    suite.clear()
    assert len(suite.tests) == 0


def test_add_non_callable() -> None:
    """Passing a non-callable raises TypeError."""
    suite = Suite()
    with pytest.raises(TypeError, match="callable"):
        suite.add(42)  # type: ignore[arg-type]


def test_timeout_exit() -> None:
    """Benchmark stops when timeout is reached."""
    import time

    def slow() -> None:
        time.sleep(0.01)

    suite = Suite()
    suite.set_timeout(0.03)
    suite.set_max_itr(10000)
    suite.set_min_itr(1)
    suite.set_cut(0.0)
    suite.add(slow)
    results = suite.run()
    assert results[0].iterations < 100


def test_hash_methods() -> None:
    """_Function and _BeforeAfter are hashable."""
    from pybencher.core import _BeforeAfter, _Function

    def foo() -> None:
        pass

    f = _Function(foo, args=(1,))
    assert isinstance(hash(f), int)

    ba = _BeforeAfter(foo, 1, 2)
    assert isinstance(hash(ba), int)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(65, "01:05"), (3665, "1:01:05")],
)
def test_format_time_large(seconds: float, expected: str) -> None:
    """_format_time for values >= 60s."""
    from pybencher.core import BenchmarkResults

    assert BenchmarkResults._format_time(seconds) == expected


def test_empty_times_branch() -> None:
    """_get_output_details when no runs were performed."""
    suite = Suite()
    from pybencher.core import _Function

    func = _Function(lambda: 1)
    res = suite._get_output_details(func, [], 0)
    assert res.avg == 0.0
    assert res.iterations == 0


def test_empty_stats_branch() -> None:
    """_get_output_details when the cut removes all iterations."""
    suite = Suite()
    suite.set_max_itr(1)
    suite.set_cut(0.6)
    suite.add(lambda: 1)
    results = suite.run()
    assert results[0].avg == 0.0
    assert results[0].counted_iterations == 0


def test_validate_responses_tail_hash_failure() -> None:
    """Verify that tail hash mismatch raises ValueError."""

    def get_func(deviate_at: int) -> Callable[[], int]:
        state = {"c": 0}

        def f() -> int:
            state["c"] += 1
            return -1 if state["c"] > deviate_at else state["c"]

        return f

    suite = Suite()
    suite.set_validate_responses(True)
    suite.set_validate_limit(5)
    suite.set_max_itr(20)
    suite.set_cut(0.0)

    suite.add(get_func(100), name="f1")
    suite.add(get_func(10), name="f2")

    with pytest.raises(ValueError, match="tail hashes do not match"):
        suite.run()


@pytest.fixture
def results_list() -> list[str]:
    return []
