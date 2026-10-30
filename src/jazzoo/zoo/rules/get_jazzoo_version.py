import importlib.metadata


def get_jazzoo_version() -> str:
    # A jazzoo that pip did not install (e.g. a source tree on PYTHONPATH) has no
    # package metadata
    try:
        return importlib.metadata.version("jazzoo")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"
