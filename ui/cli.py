import argparse
import io
import sys

from eight_towers.errors import Crash
from eight_towers.machine import Machine
from eight_towers.syntax import  Program


def parse_byte(value: str) -> int:
    value = value.strip()

    if not value:
        raise argparse.ArgumentTypeError("empty byte value")

    # Character literal: 'A', '\n', '\xFF', etc.
    if len(value) >= 2 and value[0] == value[-1] == "'":
        literal = value[1:-1]

        try:
            decoded = bytes(literal, "utf-8").decode("unicode_escape")
        except UnicodeDecodeError as exc:
            raise argparse.ArgumentTypeError(
                f"invalid character literal: {value}"
            ) from exc

        if len(decoded) != 1:
            raise argparse.ArgumentTypeError(
                f"character literal must contain exactly one character: {value}"
            )

        number = ord(decoded)

        if number > 255:
            raise argparse.ArgumentTypeError(
                f"character is not a byte: {value}"
            )

        return number

    try:
        number = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid byte: {value}"
        ) from exc

    if not -128 <= number <= 255:
        raise argparse.ArgumentTypeError(
            f"byte must be between -128 and 255: {value}"
        )

    return number & 0xFF


def parse_input(values: list[str]) -> bytes:
    return bytes(parse_byte(value) for value in values)


class InteractiveInput:
    def __init__(self, input_stream=None, output_stream=None):
        self.input = input_stream or sys.stdin
        self.output = output_stream or sys.stderr
        self.buffer = bytearray()

    def read(self, size: int = 1) -> bytes:
        if size != 1:
            raise ValueError("8 Towers input reads exactly one byte")

        while not self.buffer:
            self.output.write("Input byte: ")
            self.output.flush()

            line = self.input.readline()

            if line == "":
                return b""

            values = line.split()

            try:
                self.buffer.extend(parse_input(values))
            except argparse.ArgumentTypeError as exc:
                self.output.write(f"Invalid input: {exc}\n")

        return bytes([self.buffer.pop(0)])


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="8towers",
        description="Reference implementation of 8 Towers",
    )

    parser.add_argument(
        "program",
        help="8 Towers source file",
    )

    parser.add_argument(
        "--realms",
        action="store_true",
        help="enable the 2.0 Realm Extension",
    )

    parser.add_argument(
        "--input",
        action="append",
        type=parse_byte,
        metavar="BYTE",
        help=(
            "provide an input byte; may be specified multiple times. "
            "Accepts signed/unsigned decimal, hexadecimal, binary, "
            "octal, and character literals."
        ),
    )

    parser.add_argument(
        "--output",
        choices=("raw", "hex", "text"),
        default="raw",
        help="output representation (default: raw)",
    )

    parser.add_argument(
        "--final-state",
        action="store_true",
        help="write the final-state encoding",
    )

    args = parser.parse_args()

    try:
        program = Program.from_file(args.program)

        if args.input is None:
            input_stream = InteractiveInput()
        else:
            input_stream = io.BytesIO(bytes(args.input))

        if args.output == "raw":
            output_stream = sys.stdout.buffer
        else:
            output_stream = io.BytesIO()

        machine = Machine(
            program,
            realms_expansion=args.realms,
            input_stream=input_stream,
            output_stream=output_stream,
        )

        machine.run()

        if args.final_state:
            data = machine.final_state()
        elif args.output != "raw":
            data = output_stream.getvalue()
        else:
            data = None

        if data is not None:
            if args.output == "hex":
                sys.stdout.write(data.hex().upper())
                sys.stdout.write("\n")
            elif args.output == "text":
                sys.stdout.write(data.decode("utf-8", errors="replace"))
            else:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

        return 0

    except Crash as exc:
        print(f"8 Towers crashed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
