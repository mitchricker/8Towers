import io
import pytest
from eight_towers.machine import Machine, IllegalTowerState, RealmSymmetryViolation
from eight_towers.syntax import Program


@pytest.fixture
def empty_program():
    """Provides an empty program instance for testing isolated machine methods."""
    return Program.from_source("")


def test_clockwise_navigation_within_single_realm(empty_program):
    machine = Machine(empty_program)
    assert machine.tower == 0

    machine._move_clockwise()
    assert machine.tower == 1

    machine.tower = 7
    machine._move_clockwise()
    assert machine.tower == 0


def test_anticlockwise_navigation_within_single_realm(empty_program):
    machine = Machine(empty_program)
    assert machine.tower == 0

    machine._move_anticlockwise()
    assert machine.tower == 7

    machine.tower = 1
    machine._move_anticlockwise()
    assert machine.tower == 0


def test_realms_expansion_clockwise_transitions(empty_program):
    machine = Machine(empty_program, realms_expansion=True)
    assert machine.realm == 0
    assert machine.tower == 0

    # Expand into Realm -1
    machine._move_anticlockwise()
    assert machine.realm == -1
    assert machine.tower == 7
    assert machine.lowest_realm == -1

    # Return to Realm 0
    machine._move_clockwise()
    assert machine.realm == 0
    assert machine.tower == 0


def test_realm_symmetry_violation_via_valid_movement(empty_program):
    """
    Expands realms symmetrically to [-1, 1], then attempts to move further into 
    positive realms without expanding negative realms, triggering RealmSymmetryViolation.
    """
    machine = Machine(empty_program, realms_expansion=True)

    # 1. Expand into Realm -1 by moving anticlockwise from tower 0
    machine._move_anticlockwise()  # Realm 0, T0 -> Realm -1, T7
    assert machine.lowest_realm == -1
    assert machine.highest_realm == 0

    # 2. Move back to Realm 0, T7, then step clockwise into Realm 1
    machine._move_clockwise()      # Realm -1, T7 -> Realm 0, T0
    machine.tower = 7
    machine._move_clockwise()      # Realm 0, T7 -> Realm 1, T0
    assert machine.lowest_realm == -1
    assert machine.highest_realm == 1

    # 3. Step into Realm 2 (interval becomes [-1, 2], valid since abs(-1) - 2 = -1)
    machine.tower = 7
    machine._move_clockwise()      # Realm 1, T7 -> Realm 2, T0
    assert machine.lowest_realm == -1
    assert machine.highest_realm == 2

    # 4. Attempting Realm 3 (interval [-1, 3] yields abs(-1) - 3 = -2, violating symmetry)
    machine.tower = 7
    with pytest.raises(RealmSymmetryViolation, match="cannot establish R3"):
        machine._move_clockwise()


def test_receive_reads_byte_from_input_stream(empty_program):
    input_stream = io.BytesIO(b"A")
    machine = Machine(empty_program, input_stream=input_stream)

    # Active tower T0 will receive ASCII 'A' (65).
    # To satisfy the independent paths (T0 <= T1 <= T6 <= T7, T0 <= T2 <= T5 <= T7, T0 <= T3 <= T4 <= T7),
    # update T1..T7 to 65 or higher.
    for tower in machine.towers[0][1:]:
        tower.value = 65

    machine._receive()
    assert machine.active.byte() == ord("A")


def test_receive_eof_raises_crash(empty_program):
    input_stream = io.BytesIO(b"")
    machine = Machine(empty_program, input_stream=input_stream)

    with pytest.raises(Exception):
        machine._receive()


def test_give_writes_byte_to_output_stream(empty_program):
    output_stream = io.BytesIO()
    machine = Machine(empty_program, output_stream=output_stream)
    machine.active.value = 65

    # Align T1..T7 so initial state passes validation if triggered
    for tower in machine.towers[0][1:]:
        tower.value = 65

    machine._give()
    assert output_stream.getvalue() == b"A"


def test_begin_loop_skips_when_active_tower_is_zero():
    # Concrete Program trigrams: BEGIN_LOOP (011), DECREASE (110), END_LOOP (100), GIVE (101)
    prog = Program.from_source("011 110 100 101")
    machine = Machine(prog)

    # Active tower is 0 by default; skips past matching END_LOOP (index 2) to PC 3
    machine._begin_loop()

    assert machine.pc == 3
    assert len(machine.loop_stack) == 0


def test_begin_loop_enters_when_active_tower_is_nonzero():
    prog = Program.from_source("110 011 001 100")
    machine = Machine(prog)
    machine.active.value = 1

    # Keep parallel paths valid
    for tower in machine.towers[0][1:]:
        tower.value = 1

    machine._begin_loop()

    assert machine.pc == 1
    assert len(machine.loop_stack) == 1
    assert machine.loop_stack[0] == 0


def test_end_loop_unmatched_raises_exception(empty_program):
    machine = Machine(empty_program)

    with pytest.raises(Exception):
        machine._end_loop()


def test_run_eof_inside_active_loop_raises_crash():
    # Unclosed loop at EOF
    prog = Program.from_source("011 001")
    machine = Machine(prog)
    machine.active.value = 1

    for tower in machine.towers[0][1:]:
        tower.value = 1

    with pytest.raises(Exception):
        machine.run()


def test_validate_failure_raises_illegal_tower_state(empty_program, mocker):
    mocker.patch("eight_towers.machine.validate", side_effect=ValueError("Invalid state"))
    machine = Machine(empty_program)

    with pytest.raises(IllegalTowerState, match="illegal tower state in R0"):
        machine._validate()


@pytest.mark.parametrize(
    "realms_expansion,tower_values,expected_pc",
    [
        (False, [0] * 8, 0),
        (False, [1] * 8, 0),
    ],
)
def test_final_state_non_realms(realms_expansion, tower_values, expected_pc, empty_program):
    machine = Machine(empty_program, realms_expansion=realms_expansion)

    for i, val in enumerate(tower_values):
        machine.towers[0][i].value = val

    assert machine.pc == expected_pc