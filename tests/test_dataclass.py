import dataclasses
import typing as T

import pytest

# The decorator is written after its tests: until it exists, these tests are skipped.
dataclass = pytest.importorskip("jazzoo.utils.dataclass").dataclass


def test_an_empty_list_default_is_not_shared():
    @dataclass
    class Block:
        mode: str
        lines: T.List[str] = []

    first = Block(mode="shell")
    second = Block(mode="shell")
    first.lines.append("echo hello")

    assert first.lines == ["echo hello"]
    assert second.lines == []
    assert Block(mode="shell").lines == []


def test_a_non_empty_list_default_is_cloned():
    @dataclass
    class Block:
        lines: T.List[str] = ["echo hello"]

    first = Block()
    second = Block()
    first.lines.append("echo bye")

    assert first.lines == ["echo hello", "echo bye"]
    assert second.lines == ["echo hello"]
    assert Block().lines == ["echo hello"]


def test_a_dict_default_is_cloned():
    @dataclass
    class Module:
        namespace: T.Dict[str, T.Any] = {}
        settings: T.Dict[str, str] = {"log-level": "high"}

    first = Module()
    second = Module()
    first.namespace["name"] = "jane"
    first.settings["log-level"] = "low"

    assert second.namespace == {}
    assert second.settings == {"log-level": "high"}


def test_a_set_default_is_cloned():
    @dataclass
    class Scope:
        seen: T.Set[str] = set()
        reserved: T.Set[str] = {"module"}

    first = Scope()
    second = Scope()
    first.seen.add("name")
    first.reserved.add("env")

    assert second.seen == set()
    assert second.reserved == {"module"}


def test_a_nested_default_is_cloned_deeply():
    @dataclass
    class Module:
        layers: T.List[T.List[str]] = [[]]
        exports: T.Dict[str, T.List[str]] = {"fe": []}

    first = Module()
    second = Module()
    first.layers[0].append("build")
    first.exports["fe"].append("build")

    assert second.layers == [[]]
    assert second.exports == {"fe": []}


def test_an_explicit_value_is_not_copied():
    @dataclass
    class Block:
        lines: T.List[str] = []

    lines = ["echo hello"]
    block = Block(lines=lines)

    assert block.lines is lines


def test_other_defaults_are_shared_as_in_the_standard_library():
    class Marker:
        pass

    default_marker = Marker()

    @dataclass
    class Block:
        name: str = "build"
        marker: Marker = default_marker

    assert Block().name == "build"
    assert Block().marker is default_marker


def test_an_explicit_field_is_left_alone():
    @dataclass
    class Block:
        lines: T.List[str] = dataclasses.field(default_factory=lambda: ["echo hello"])
        line: T.Optional[int] = dataclasses.field(default=None, compare=False)

    assert Block().lines == ["echo hello"]
    assert Block(line=1) == Block(line=2)


def test_a_subclass_inherits_cloned_defaults():
    @dataclass
    class Scope:
        variables: T.List[str] = []

    @dataclass
    class Function(Scope):
        name: str = ""
        parameters: T.List[str] = []

    first = Function(name="build")
    second = Function(name="test")
    first.variables.append("target")
    first.parameters.append("name")

    assert second.variables == []
    assert second.parameters == []
    assert Scope().variables == []


def test_the_result_is_a_standard_library_dataclass():
    @dataclass
    class Block:
        mode: str
        lines: T.List[str] = []

    block = Block(mode="shell", lines=["echo hello"])

    assert dataclasses.is_dataclass(Block)
    assert [field.name for field in dataclasses.fields(Block)] == ["mode", "lines"]
    assert dataclasses.asdict(block) == {"mode": "shell", "lines": ["echo hello"]}
    assert dataclasses.replace(block, mode="python").lines == ["echo hello"]
    assert block == Block(mode="shell", lines=["echo hello"])
    assert repr(block).endswith("Block(mode='shell', lines=['echo hello'])")


def test_keyword_arguments_are_passed_to_the_standard_library():
    @dataclass(frozen=True)
    class Reference:
        parts: T.List[str] = []

    reference = Reference()

    with pytest.raises(dataclasses.FrozenInstanceError):
        reference.parts = ["name"]  # type: ignore[misc]
    assert Reference().parts is not reference.parts
