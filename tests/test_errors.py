import pytest
from eight_towers.errors import (
    Crash,
    IllegalTowerState,
    RealmSymmetryViolation,
    UnexpectedEOF,
    UnmatchedLoop,
)


@pytest.mark.parametrize(
    "exception_cls",
    [
        IllegalTowerState,
        UnmatchedLoop,
        UnexpectedEOF,
        RealmSymmetryViolation,
    ],
)
def test_exceptions_inherit_from_crash(exception_cls):
    """Verifies that all sub-exceptions subclass the base Crash class."""
    assert issubclass(exception_cls, Crash)
    assert issubclass(exception_cls, Exception)


@pytest.mark.parametrize(
    "exception_cls",
    [
        Crash,
        IllegalTowerState,
        UnmatchedLoop,
        UnexpectedEOF,
        RealmSymmetryViolation,
    ],
)
def test_exceptions_can_be_raised_and_caught_by_crash_base(exception_cls):
    """Ensures catching Crash handles any machine runtime error."""
    with pytest.raises(Crash) as exc_info:
        raise exception_cls("Execution halted")

    assert "Execution halted" in str(exc_info.value)