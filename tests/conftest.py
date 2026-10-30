# tests/conftest.py

import io
import pytest

from eight_towers.machine import Machine
from eight_towers.syntax import Operation, Program, Trigram
from eight_towers.tower import Tower


# ----------------------------------------------------------------------
# Tower & State Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def empty_tower():
    """Provides a default Tower instance with value 0."""
    return Tower(0)


@pytest.fixture
def default_realm_towers():
    """Provides a valid list of 8 initialized towers for a single realm."""
    return [Tower(0) for _ in range(8)]


# ----------------------------------------------------------------------
# Program & Instruction Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def empty_program():
    """Provides a empty Program instance."""
    return Program([])


@pytest.fixture
def simple_program():
    """
    Provides a simple valid Program sequence:
    INCREASE (001), GIVE (101)
    """
    return Program([
        Trigram("001"),
        Trigram("101"),
    ])


@pytest.fixture
def loop_program():
    """
    Provides a valid loop program:
    BEGIN_LOOP (011), DECREASE (110), END_LOOP (100)
    """
    return Program([
        Trigram("011"),
        Trigram("110"),
        Trigram("100"),
    ])


# ----------------------------------------------------------------------
# I/O Stream & Machine Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def io_streams():
    """Provides binary input and output streams for I/O testing."""
    stdin = io.BytesIO()
    stdout = io.BytesIO()
    return stdin, stdout


@pytest.fixture
def machine_builder(io_streams):
    """
    Factory fixture to create Machine instances with custom programs,
    realms expansion settings, or populated input data.
    """
    stdin, stdout = io_streams

    def _create_machine(
        program: Program | None = None,
        input_data: bytes = b"",
        realms_expansion: bool = False,
    ) -> tuple[Machine, io.BytesIO, io.BytesIO]:
        
        if program is None:
            program = Program([])

        stdin.write(input_data)
        stdin.seek(0)

        machine = Machine(
            program,
            realms_expansion=realms_expansion,
            input_stream=stdin,
            output_stream=stdout,
        )
        return machine, stdin, stdout

    return _create_machine