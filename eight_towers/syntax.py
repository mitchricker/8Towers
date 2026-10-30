from dataclasses import dataclass
from enum import Enum

from .errors import UnexpectedEOF, UnmatchedLoop


class Operation(Enum):
    MOVE_ANTICLOCKWISE = "000"
    INCREASE = "001"
    RECEIVE = "010"
    BEGIN_LOOP = "011"
    END_LOOP = "100"
    GIVE = "101"
    DECREASE = "110"
    MOVE_CLOCKWISE = "111"


@dataclass(frozen=True)
class Trigram:
    bits: str

    @property
    def operation(self) -> Operation:
        return Operation(self.bits)


class Program:
    def __init__(self, trigrams: list[Trigram]):
        self.trigrams = trigrams

    @classmethod
    def from_source(cls, source: str) -> "Program":
        bits = "".join(c for c in source if c in "01")

        if len(bits) % 3:
            raise UnexpectedEOF("incomplete trigram at EOF")

        return cls([
            Trigram(bits[i:i + 3])
            for i in range(0, len(bits), 3)
        ])

    @classmethod
    def from_file(cls, path: str) -> "Program":
        with open(path, encoding="utf-8") as file:
            return cls.from_source(file.read())

    def __len__(self) -> int:
        return len(self.trigrams)

    def __getitem__(self, pc: int) -> Trigram:
        return self.trigrams[pc]

    def matching_end(self, start: int) -> int:
        """Find the 100 matching a 011."""
        if self[start].operation is not Operation.BEGIN_LOOP:
            raise ValueError("not a loop start")

        depth = 1

        for pc in range(start + 1, len(self)):
            operation = self[pc].operation

            if operation is Operation.BEGIN_LOOP:
                depth += 1
            elif operation is Operation.END_LOOP:
                depth -= 1
                if depth == 0:
                    return pc

        raise UnexpectedEOF(
            f"loop beginning at trigram {start} has no matching end"
        )

    def validate_loops(self) -> None:
        """Reject unmatched 100 and 011 instructions."""
        depth = 0

        for pc, trigram in enumerate(self.trigrams):
            operation = trigram.operation

            if operation is Operation.BEGIN_LOOP:
                depth += 1
            elif operation is Operation.END_LOOP:
                depth -= 1
                if depth < 0:
                    raise UnmatchedLoop(
                        f"unmatched loop end at trigram {pc}"
                    )

        if depth:
            raise UnmatchedLoop("program contains an unmatched loop start")
