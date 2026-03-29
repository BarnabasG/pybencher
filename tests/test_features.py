import pytest
from pybencher import Suite

def test_warmup_increments_calls() -> None:
    """Verify that warmup_itr actually calls the function unmeasured."""
    call_count = 0
    
    def tracked_func() -> None:
        nonlocal call_count
        call_count += 1
        
    suite = Suite()
    suite.set_warmup_itr(5)
    suite.set_max_itr(1)
    suite.set_cut(0.0)
    suite.add(tracked_func)
    
    suite.run()
    # 5 warmup + 1 measured = 6
    assert call_count == 6

def test_validate_responses_success() -> None:
    """Verify that matching sequences pass validation."""
    def f1() -> int: return 1
    def f2() -> int: return 1
    
    suite = Suite()
    suite.set_validate_responses(True)
    suite.set_max_itr(5)
    suite.add(f1)
    suite.add(f2)
    
    # Should not raise
    suite.run()

def test_validate_responses_failure() -> None:
    """Verify that mismatching sequences raise ValueError."""
    def f1() -> int: return 1
    def f2() -> int: return 2
    
    suite = Suite()
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
        # Returns a different sequence
        return 0
    
    suite = Suite()
    suite.set_validate_responses(True)
    suite.set_max_itr(3)
    suite.add(f1)
    suite.add(f2)
    
    with pytest.raises(ValueError, match="Response validation failed"):
        suite.run()

def test_validate_responses_warning_on_mismatch_args() -> None:
    """Verify that inconsistent args trigger a RuntimeWarning."""
    def foo(a: int) -> int: return a
    
    suite = Suite()
    suite.set_validate_responses(True)
    suite.add(foo, 1)
    suite.add(foo, 2) # Different arg
    
    with pytest.warns(RuntimeWarning, match="different arguments"):
        try:
            suite.run()
        except ValueError:
            # We expect a ValueError because 1 != 2, 
            # but we want to check the warning was emitted first.
            pass

def test_validate_limit_efficiency() -> None:
    """Verify that large runs don't crash and validation still works (smoke test)."""
    def f1() -> int: return 1
    def f2() -> int: return 1
    
    suite = Suite()
    suite.set_validate_responses(True)
    suite.set_validate_limit(10)
    suite.set_max_itr(20) # Beyond limit
    suite.set_cut(0.0)
    suite.add(f1)
    suite.add(f2)
    
    # Should pass (both have same sequence and same length -> same hash)
    suite.run()
