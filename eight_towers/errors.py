class Crash(Exception):
    """Base class for an 8 Towers machine crash."""


class IllegalTowerState(Crash):
    pass


class UnmatchedLoop(Crash):
    pass


class UnexpectedEOF(Crash):
    pass


class RealmSymmetryViolation(Crash):
    pass
