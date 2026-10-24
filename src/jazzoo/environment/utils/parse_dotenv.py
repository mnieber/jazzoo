import typing as T


def parse_dotenv(source: str) -> T.Dict[str, str]:
    """Read `KEY=VALUE` lines, skipping blank lines and `#` comments."""
    values: T.Dict[str, str] = {}
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        # Surrounding quotes delimit the value and are not part of it.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values
