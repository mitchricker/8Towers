import pytest
from eight_towers.errors import UnexpectedEOF, UnmatchedLoop
from eight_towers.syntax import Operation, Program, Trigram


# ----------------------------------------------------------------------
# 1. Trigram & Operation Mapping
# ----------------------------------------------------------------------

@pytest.mark.parametrize(
    "bits, expected_op",
    [
        ("000", Operation.MOVE_ANTICLOCKWISE),
        ("001", Operation.INCREASE),
        ("010", Operation.RECEIVE),
        ("011", Operation.BEGIN_LOOP),
        ("100", Operation.END_LOOP),
        ("101", Operation.GIVE),
        ("110", Operation.DECREASE),
        ("111", Operation.MOVE_CLOCKWISE),
    ],
)
def test_trigram_enum_mapping(bits, expected_op):
    trigram = Trigram(bits)
    assert trigram.operation is expected_op


def test_trigram_invalid_bits_raises_value_error():
    with pytest.raises(ValueError):
        _ = Trigram("112").operation


# ----------------------------------------------------------------------
# 2. Program Construction & Parsing
# ----------------------------------------------------------------------

def test_from_source_filters_non_binary_characters():
    # Source contains spaces, newlines, and commentary text
    source = "000 001\n# Comment\n 010 xyz 011"
    program = Program.from_source(source)

    assert len(program) == 4
    assert [t.bits for t in program] == ["000", "001", "010", "011"]


def test_from_source_incomplete_trigram_raises_unexpected_eof():
    # 5 binary bits (not divisible by 3)
    source = "000 01"
    with pytest.raises(UnexpectedEOF, match="incomplete trigram at EOF"):
        Program.from_source(source)


def test_from_file_loads_correctly(tmp_path):
    file_path = tmp_path / "test_program.8t"
    file_path.write_text("000001010 -- sample program -- 011100", encoding="utf-8")

    program = Program.from_file(str(file_path))
    assert len(program) == 5
    assert program[0].operation is Operation.MOVE_ANTICLOCKWISE
    assert program[4].operation is Operation.END_LOOP


def test_program_dunder_methods():
    program = Program.from_source("000001")
    assert len(program) == 2
    assert program[0] == Trigram("000")
    assert program[1] == Trigram("001")


# ----------------------------------------------------------------------
# 3. Matching End Loop Pointer Logic
# ----------------------------------------------------------------------

def test_matching_end_nested_loops():
    # Index: 0=BEGIN(1), 1=BEGIN(2), 2=END(2), 3=END(1)
    # Bits:  011        011        100       100
    program = Program.from_source("011 011 100 100")

    assert program.matching_end(0) == 3  # Outer loop end
    assert program.matching_end(1) == 2  # Inner loop end


def test_matching_end_not_a_loop_start_raises_value_error():
    program = Program.from_source("000 100")
    with pytest.raises(ValueError, match="not a loop start"):
        program.matching_end(0)


def test_matching_end_missing_closing_trigram_raises_unexpected_eof():
    program = Program.from_source("011 000 001")  # Missing 100
    with pytest.raises(UnexpectedEOF, match="loop beginning at trigram 0 has no matching end"):
        program.matching_end(0)


# ----------------------------------------------------------------------
# 4. Program Loop Validation
# ----------------------------------------------------------------------

def test_validate_loops_success():
    program = Program.from_source("000 011 001 100 011 100 111")
    # Should complete without raising any exceptions
    program.validate_loops()


def test_validate_loops_unmatched_end_first_raises_unmatched_loop():
    program = Program.from_source("100 011 100")  # Starts with 100
    with pytest.raises(UnmatchedLoop, match="unmatched loop end at trigram 0"):
        program.validate_loops()


def test_validate_loops_unclosed_start_raises_unmatched_loop():
    program = Program.from_source("011 001")  # Missing 100 at end
    with pytest.raises(UnmatchedLoop, match="unmatched loop start"):
        program.validate_loops()