class Tower:
    def __init__(self, value: int = 0):
        if not -128 <= value <= 127:
            raise ValueError("tower value must be signed 8-bit")

        self.value = value

    def increase(self) -> None:
        self.value = (self.value + 1 + 128) % 256 - 128

    def decrease(self) -> None:
        self.value = (self.value - 1 + 128) % 256 - 128

    def set_byte(self, value: int) -> None:
        if not 0 <= value <= 255:
            raise ValueError("byte must be between 0 and 255")

        self.value = value if value < 128 else value - 256

    def byte(self) -> int:
        return self.value & 0xFF


def validate(towers: list[Tower]) -> None:
    if len(towers) != 8:
        raise ValueError("a realm must contain exactly eight towers")

    t = [tower.value for tower in towers]

    if not (
        t[0] <= t[1] <= t[6] <= t[7]
        and t[0] <= t[2] <= t[5] <= t[7]
        and t[0] <= t[3] <= t[4] <= t[7]
    ):
        raise ValueError("illegal tower state")
