import pytest
from pybencher import Suite


def test_warmup_increments_calls() -> None:
    """Verify that warmup_samples actually calls the function unmeasured."""
    call_count = 0

    def tracked_func() -> None:
        nonlocal call_count
        call_count += 1

    suite = Suite()
    suite.set_batch_size(1)
    suite.set_warmup_samples(5)
    suite.set_max_samples(1)
    suite.set_cut(0.0)
    suite.add(tracked_func)

    suite.run()
    assert call_count == 6


def test_validate_responses_success() -> None:
    """Verify that matching sequences pass validation."""

    def f1() -> int:
        return 1

    def f2() -> int:
        return 1

    suite = Suite()
    suite.set_batch_size(1)
    suite.set_validate_responses(True)
    suite.set_max_samples(5)
    suite.add(f1)
    suite.add(f2)

    suite.run()


def test_validate_responses_failure() -> None:
    """Verify that mismatching sequences raise ValueError."""

    def f1() -> int:
        return 1

    def f2() -> int:
        return 2

    suite = Suite()
    suite.set_batch_size(1)
    suite.set_validate_responses(True)
    suite.add(f1)
    suite.add(f2)

    with pytest.raises(ValueError, match="Response validation failed"):
        suite.run()


def test_validate_responses_sequence_drift() -> None:
    """Verify that different sequences (stateful) raise ValueError."""
    state = {"count": 0}

    def f1() -> int:
        state["count"] += 1
        return state["count"]

    def f2() -> int:
        return 0

    suite = Suite()
    suite.set_batch_size(1)
    suite.set_validate_responses(True)
    suite.set_max_samples(3)
    suite.add(f1)
    suite.add(f2)

    with pytest.raises(ValueError, match="Response validation failed"):
        suite.run()


def test_validate_responses_warning_on_mismatch_args() -> None:
    """Verify that inconsistent args trigger a RuntimeWarning."""

    def foo(a: int) -> int:
        return a

    suite = Suite()
    suite.set_batch_size(1)
    suite.set_validate_responses(True)
    suite.add(foo, args=(1,))
    suite.add(foo, args=(2,))

    with pytest.warns(RuntimeWarning, match="different arguments"):
        try:
            suite.run()
        except ValueError:
            pass


def test_validate_limit_efficiency() -> None:
    """Verify that large runs don't crash and validation still works (smoke test)."""

    def f1() -> int:
        return 1

    def f2() -> int:
        return 1

    suite = Suite()
    suite.set_batch_size(1)
    suite.set_validate_responses(True)
    suite.set_validate_limit(10)
    suite.set_max_samples(20)
    suite.set_cut(0.0)
    suite.add(f1)
    suite.add(f2)

    suite.run()


def test_auto_batch_calibration() -> None:
    """Test auto batching calibration."""
    suite = Suite()
    # explicitly set to 0 (auto) just in case
    suite.set_batch_size(0)
    suite.set_max_samples(1)
    suite.set_cut(0.0)

    @suite.bench()
    def extremely_fast() -> None:
        pass

    results = suite.run()
    # Because it is extremely fast, the calibration should scale up batch size to 100+
    assert results[0].iterations > 10


def test_live_output_coverage() -> None:
    """Verify set_live_output and batch_size=0 fallback in _Function."""
    suite = Suite()
    suite.set_live_output(True)
    suite.set_max_samples(1)
    suite.set_cut(0.0)

    @suite.bench(batch_size=0)
    def test_func() -> None:
        pass

    from pybencher.core import _Function

    f = _Function(test_func)
    # testing the batch_size == 0 fallback in __call__
    t, res = f(default_batch_size=0)
    assert t >= 0
