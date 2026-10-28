import copy
import dataclasses
import typing as T

if T.TYPE_CHECKING:
    from typing_extensions import dataclass_transform
else:

    def dataclass_transform(**kwargs):
        return lambda f: f


_T = T.TypeVar("_T")


def _clone_factory(value: T.Any) -> T.Callable[[], T.Any]:
    return lambda: copy.deepcopy(value)


@dataclass_transform(field_specifiers=(dataclasses.field,))
def dataclass(cls: T.Optional[T.Type[_T]] = None, **kwargs: T.Any) -> T.Any:
    def wrap(cls: T.Type[_T]) -> T.Type[_T]:
        # Give every instance its own copy of a list, dict or set default
        for name in cls.__dict__.get("__annotations__", {}):
            value = cls.__dict__.get(name)
            if isinstance(value, (list, dict, set)):
                setattr(
                    cls,
                    name,
                    dataclasses.field(default_factory=_clone_factory(value)),
                )
        return dataclasses.dataclass(cls, **kwargs)

    return wrap if cls is None else wrap(cls)
