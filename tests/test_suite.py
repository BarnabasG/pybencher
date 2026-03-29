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
    assert suite.tests[0].name == "foo"


def test_decorator_registration() -> None:
    """Decorator registration."""
    suite = Suite()

    @suite.bench()
    def foo() -> None:
        pass

    assert len(suite.tests) == 1
    assert suite.tests[0].name == "foo"


def test_name_override() -> None:
    """Custom benchmark name."""
    suite = Suite()

    @suite.bench(bench_name="Custom Name")
    def foo() -> None:
        pass

    results = suite.run()
    assert results[0].name == "Custom Name"


def test_decorator_arguments() -> None:
    """Passing positional and keyword arguments."""
    suite = Suite()

    @suite.bench(1, 2, c=3)
    def foo(a: int, b: int, c: int) -> int:
        return a + b + c

    results = suite.run()
    assert "foo" in results[0].name


def test_config_override() -> None:
    """Per-test configuration priority."""
    suite = Suite(max_itr=100)

    @suite.bench(bench_max_itr=5, bench_cut=0.0)
    def foo() -> None:
        pass

    results = suite.run()
    assert results[0].iterations == 5


def test_shadowing_prevention() -> None:
    """Ensure 'timeout' can be used as a function parameter."""
    suite = Suite()
    suite.set_max_itr(1)

    @suite.bench(timeout=0.123)
    def foo(timeout: float) -> float:
        return timeout

    results = suite.run()
    assert results[0].iterations == 1


def test_stdout_suppression(capsys: pytest.CaptureFixture[str]) -> None:
    """Stdout muting."""
    suite = Suite()
    suite.set_max_itr(1)

    @suite.bench(bench_disable_stdout=True)
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


@pytest.fixture
def results_list() -> list[str]:
    return []
