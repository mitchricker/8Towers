import pytest
from eight_towers.tower import Tower, validate


# ----------------------------------------------------------------------
# 1. Tower Initialization Tests
# ----------------------------------------------------------------------

def test_tower_init_valid_range():
    assert Tower(0).value == 0
    assert Tower(-128).value == -128
    assert Tower(127).value == 127


@pytest.mark.parametrize("invalid_val", [-129, 128, 500, -200])
def test_tower_init_invalid_range_raises_value_error(invalid_val):
    with pytest.raises(ValueError, match="tower value must be signed 8-bit"):
        Tower(invalid_val)


# ----------------------------------------------------------------------
# 2. Increment & Decrement Overflow/Underflow (Signed 8-bit Wrapping)
# ----------------------------------------------------------------------

def test_increase_normal():
    tower = Tower(5)
    tower.increase()
    assert tower.value == 6


def test_increase_overflow_wraps_to_negative():
    tower = Tower(127)
    tower.increase()
    assert tower.value == -128


def test_decrease_normal():
    tower = Tower(5)
    tower.decrease()
    assert tower.value == 4


def test_decrease_underflow_wraps_to_positive():
    tower = Tower(-128)
    tower.decrease()
    assert tower.value == 127


# ----------------------------------------------------------------------
# 3. Byte Conversion Operations
# ----------------------------------------------------------------------

@pytest.mark.parametrize(
    "byte_in, expected_signed",
    [
        (0, 0),
        (127, 127),
        (128, -128),
        (255, -1),
    ],
)
def test_set_byte_valid(byte_in, expected_signed):
    tower = Tower()
    tower.set_byte(byte_in)
    assert tower.value == expected_signed


@pytest.mark.parametrize("invalid_byte", [-1, 256, 1000])
def test_set_byte_invalid_raises_value_error(invalid_byte):
    tower = Tower()
    with pytest.raises(ValueError, match="byte must be between 0 and 255"):
        tower.set_byte(invalid_byte)


@pytest.mark.parametrize(
    "signed_val, expected_byte",
    [
        (0, 0),
        (127, 127),
        (-128, 128),
        (-1, 255),
    ],
)
def test_byte_representation(signed_val, expected_byte):
    tower = Tower(signed_val)
    assert tower.byte() == expected_byte


# ----------------------------------------------------------------------
# 4. Realm Validation Rules
# ----------------------------------------------------------------------

def test_validate_valid_realm_ordering():
    """
    Validates rules:
    t[0] <= t[1] <= t[6] <= t[7]
    t[0] <= t[2] <= t[5] <= t[7]
    t[0] <= t[3] <= t[4] <= t[7]
    """
    # All equal (valid)
    towers = [Tower(10) for _ in range(8)]
    validate(towers)

    # Compliant hierarchy
    # Indexes:  0   1   2   3   4   5   6   7
    vals =    [-5,  0,  1,  2,  3,  4,  5, 10]
    validate([Tower(v) for v in vals])


def test_validate_invalid_tower_count():
    with pytest.raises(ValueError, match="must contain exactly eight towers"):
        validate([Tower() for _ in range(7)])

    with pytest.raises(ValueError, match="must contain exactly eight towers"):
        validate([Tower() for _ in range(9)])


@pytest.mark.parametrize(
    "invalid_values",
    [
        # Violates t[0] <= t[1]
        [10, 5, 0, 0, 0, 0, 0, 20],
        # Violates t[1] <= t[6]
        [0, 15, 0, 0, 0, 0, 10, 20],
        # Violates t[6] <= t[7]
        [0, 5, 0, 0, 0, 0, 25, 20],
        # Violates t[3] <= t[4]
        [0, 0, 0, 10, 5, 0, 0, 20],
    ],
)
def test_validate_illegal_tower_state_raises_error(invalid_values):
    towers = [Tower(v) for v in invalid_values]
    with pytest.raises(ValueError, match="illegal tower state"):
        validate(towers)