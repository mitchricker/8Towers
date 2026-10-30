import sys

from .errors import (
    Crash,
    IllegalTowerState,
    RealmSymmetryViolation,
    UnmatchedLoop,
)
from .syntax import Operation, Program
from .tower import Tower, validate


class Machine:
    def __init__(
        self,
        program: Program,
        *,
        realms_expansion: bool = False,
        input_stream=None,
        output_stream=None,
    ):
        self.program = program
        self.realms_expansion = realms_expansion

        self.input = input_stream or sys.stdin.buffer
        self.output = output_stream or sys.stdout.buffer

        self.towers = {0: [Tower() for _ in range(8)]}

        self.realm = 0
        self.tower = 0

        self.lowest_realm = 0
        self.highest_realm = 0

        self.pc = 0
        self.loop_stack = []

    @property
    def active(self) -> Tower:
        return self.towers[self.realm][self.tower]

    @property
    def current_towers(self) -> list[Tower]:
        return self.towers[self.realm]

    def run(self) -> None:
        while self.pc < len(self.program):
            self.step()

        if self.loop_stack:
            raise Crash("EOF reached inside an active loop")

    def step(self) -> None:
        operation = self.program[self.pc].operation

        if operation is Operation.MOVE_ANTICLOCKWISE:
            self._move_anticlockwise()

        elif operation is Operation.MOVE_CLOCKWISE:
            self._move_clockwise()

        elif operation is Operation.INCREASE:
            self.active.increase()
            self._validate()

        elif operation is Operation.DECREASE:
            self.active.decrease()
            self._validate()

        elif operation is Operation.RECEIVE:
            self._receive()

        elif operation is Operation.GIVE:
            self._give()

        elif operation is Operation.BEGIN_LOOP:
            self._begin_loop()
            return

        elif operation is Operation.END_LOOP:
            self._end_loop()
            return

        self.pc += 1

    def _move_clockwise(self) -> None:
        if self.tower < 7:
            self.tower += 1
            return

        if not self.realms_expansion:
            self.tower = 0
            return

        realm = self.realm + 1
        self._enter_realm(realm)

        self.realm = realm
        self.tower = 0

    def _move_anticlockwise(self) -> None:
        if self.tower > 0:
            self.tower -= 1
            return

        if not self.realms_expansion:
            self.tower = 7
            return

        realm = self.realm - 1
        self._enter_realm(realm)

        self.realm = realm
        self.tower = 7

    def _enter_realm(self, realm: int) -> None:
        if self.lowest_realm <= realm <= self.highest_realm:
            return

        lowest = min(self.lowest_realm, realm)
        highest = max(self.highest_realm, realm)

        if abs(lowest) - highest not in (-1, 0, 1):
            raise RealmSymmetryViolation(
                f"cannot establish R{realm}; "
                f"established interval is "
                f"[{self.lowest_realm}, {self.highest_realm}]"
            )

        self.towers[realm] = [Tower() for _ in range(8)]
        self.lowest_realm = lowest
        self.highest_realm = highest

    def _receive(self) -> None:
        data = self.input.read(1)

        if not data:
            raise Crash("Receive encountered input EOF")

        if isinstance(data, str):
            data = data.encode("latin-1")

        self.active.set_byte(data[0])
        self._validate()

    def _give(self) -> None:
        value = bytes([self.active.byte()])

        self.output.write(value)
        self.output.flush()

    def _begin_loop(self) -> None:
        if self.active.value == 0:
            self.pc = self.program.matching_end(self.pc) + 1
            return

        self.loop_stack.append(self.pc)
        self.pc += 1

    def _end_loop(self) -> None:
        if not self.loop_stack:
            raise UnmatchedLoop(
                f"unmatched loop end at trigram {self.pc}"
            )

        if self.active.value == 0:
            self.loop_stack.pop()
            self.pc += 1
        else:
            self.pc = self.loop_stack[-1] + 1

    def _validate(self) -> None:
        try:
            validate(self.current_towers)
        except ValueError as exc:
            raise IllegalTowerState(
                f"illegal tower state in R{self.realm}"
            ) from exc


    def final_state(self) -> bytes:
        if not self.realms_expansion:
            if any(tower.value != 0 for tower in self.towers[0]):
                return b"1"
            return b""

        bits = []

        for realm in range(
            self.lowest_realm,
            self.highest_realm + 1,
        ):
            nonzero = any(
                tower.value != 0
                for tower in self.towers[realm]
            )
            bits.append("1" if nonzero else "0")

        return "".join(bits).strip("0").encode("ascii")
