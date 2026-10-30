import importlib.metadata
import json
import os
import urllib.parse
import urllib.request


def get_jazzoo_version(linked_dir: str) -> str:
    # Only the metadata of the linked jazzoo counts, not of another jazzoo that
    # python also sees. A jazzoo that pip did not install (e.g. a source tree on
    # PYTHONPATH) has no package metadata.
    for dist in importlib.metadata.distributions(name="jazzoo"):
        if _describes(dist, os.path.realpath(linked_dir)):
            return dist.version
    return "0.0.0"


def _describes(dist: importlib.metadata.Distribution, linked_dir: str) -> bool:
    # A regular install has its package next to its metadata
    if os.path.realpath(dist.locate_file("jazzoo")) == linked_dir:
        return True

    # An editable install points to the linked directory, or to a directory that
    # contains it
    direct_url = json.loads(dist.read_text("direct_url.json") or "{}")
    if not direct_url.get("dir_info", {}).get("editable"):
        return False
    path = urllib.request.url2pathname(urllib.parse.urlparse(direct_url["url"]).path)
    root = os.path.realpath(path)
    return linked_dir == root or linked_dir.startswith(root + os.sep)
