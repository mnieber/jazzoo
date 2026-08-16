class _Absent:
    """Sentinel for 'this name is not defined', distinct from an empty value.

    A single shared instance, because resolution compares by identity.
    """

    def __repr__(self) -> str:
        return "<absent>"

    def __bool__(self) -> bool:
        return False


ABSENT = _Absent()
