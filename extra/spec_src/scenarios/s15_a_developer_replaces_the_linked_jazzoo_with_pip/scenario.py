import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s15_a_developer_replaces_the_linked_jazzoo_with_pip")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.python = c.External.Actors.Python
    r.pip = c.External.Actors.Pip
    r.create_venv_action = c.Zoo.Actions.CreateVenv

    with goal().import_the(r.linked_jazzoo).in_the(r.venv):
        with the(r.python).of_the(r.venv).starts():
            it().runs_the(r.link_pth_file).in_its(r.site_packages)
            it().adds_the(r.import_hook).to_the_end_of(r.meta_path)
        with the(r.python).imports(r.jazzoo_package):
            it().finds_a(r.real_install).in_its(r.site_packages).if_there_is_one()
            it().finds_the(r.jazzoo_package).in_the(r.linked_dir).through_the(
                r.import_hook
            )

    with goal().see_the(r.linked_jazzoo).in_pip():
        with the(r.developer).runs(r.pip).with_the(r.list_command):
            it().reads_the(r.package_metadata).that(r.create_venv_action).wrote()
            it().lists_the(r.linked_jazzoo).as_an(r.editable_install).of_the(
                r.linked_dir
            )

    with goal().replace_the(r.linked_jazzoo).with_a(r.jazzoo_release):
        with the(r.developer).runs(r.pip).with_the(r.install_command):
            with it().uninstalls_the(r.linked_jazzoo):
                it().removes_the(r.files).in_its(r.record)
            it().installs_the(r.jazzoo_release).into_the(r.venv)


markdown_node = sunya.add_markdown_node(
    scenario, "A developer replaces the linked jazzoo with pip"
)

markdown_node.markdown = """
A venv that `zoo env --init --create-venv` creates uses the jazzoo that runs `zoo`
(e.g. a development checkout) without copying it. pip sees this linked jazzoo as an
editable install, so the developer can replace it, or remove it, with pip, and pip
never touches the linked directory.

### Steps

#### It imports the linked jazzoo

When the python of the venv starts, it runs `_jazzoo_link.pth` in its site-packages,
which adds the import hook of `_jazzoo_link.py` to the end of `sys.meta_path`.</br>
On `import jazzoo`, python first looks in `sys.path`, so a real install of jazzoo in
the venv wins. Otherwise the hook finds the package in the linked directory. The hook
only answers for `jazzoo`: the other packages next to the linked directory stay
out of the venv.</br>

#### It shows the linked jazzoo in pip

The developer runs `pip list`.</br>
pip reads the dist-info that `create_venv` wrote, and shows jazzoo with the version of
the linked jazzoo, and the linked directory as its location:
`jazzoo  0.1.0  /home/me/projects/jazzoo/src/src/jazzoo`.</br>

#### It replaces the linked jazzoo with a release

The developer runs `pip install jazzoo==0.2.0`.</br>
pip uninstalls the linked jazzoo by removing the files in its `RECORD`: the
`_jazzoo_link` files, the dist-info and the console scripts. These are only the files
that `create_venv` wrote, so the linked directory is not touched. Then pip installs the
release. `pip uninstall jazzoo` removes the link in the same way.</br>
To replace the link with a release of the same version, the developer adds
`--force-reinstall`: otherwise pip sees that version installed.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Python as python (venv)
    participant Hook as _jazzoo_link (import hook)
    participant Pip as pip

    Note over Python,Hook: Import the linked jazzoo
    Python->>Hook: run _jazzoo_link.pth at startup
    Hook->>Hook: add finder to the end of sys.meta_path
    Python->>Python: import jazzoo: look in sys.path first
    Python->>Hook: find jazzoo
    Hook-->>Python: the package in the linked directory

    Note over Developer,Pip: See the linked jazzoo in pip
    Developer->>Pip: pip list
    Pip->>Pip: read the dist-info of the link
    Pip-->>Developer: jazzoo 0.1.0 (editable, linked directory)

    Note over Developer,Pip: Replace the linked jazzoo with a release
    Developer->>Pip: pip install jazzoo==0.2.0
    Pip->>Pip: remove the files in RECORD
    Pip->>Pip: install jazzoo 0.2.0
```
"""
