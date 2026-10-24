# Jazzoo — Implementation Plan

This plan turns `jazzoo-design.md` and the test suite in `tests/` into an ordered
build. It fixes the module/function structure, decides which features are built in
which stage, and says exactly which tests are enabled or skipped at each stage.

The code structure follows `instructions/index.md` and the `python_lib` skills:
one code unit per file, snake*case filenames, models under `models/`, rules under
`rules/`, actions under `actions/`, utils under `utils/`, entrypoint under
`runtime/entrypoints/`. Those layer directories sit inside \_feature packages*
(`expressions`, `functions`, `blocks`, `modules`) rather than one flat `modules`
package — see §2.

---

## 1. The API the tests pin down

| Name                   | Kind       | Lives at                                      | Contract                                                                                                                           |
| ---------------------- | ---------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| errors module          | module     | `jazzoo.errors`                               | `JazzooError`, `ParseError`, `ResolutionError`, `ArgumentError`, `ModuleImportError`, `ExecutionError`                             |
| `parse_module`         | action     | `jazzoo.modules.actions.parse_module`         | `parse_module(path) -> Module`; loads, parses, resolves imports, runs every parse-time check and executes module-level assignments |
| `evaluate`             | action     | `jazzoo.expressions.actions.evaluate`         | `evaluate(module, expression_source) -> str`                                                                                       |
| `get_targets`          | rule       | `jazzoo.functions.rules.get_targets`          | `get_targets(module) -> T.List[Function]`                                                                                          |
| `get_function_by_path` | rule       | `jazzoo.functions.rules.get_function_by_path` | `get_function_by_path(module, "a.b") -> T.Optional[Function]`                                                                      |
| `get_module_by_path`   | rule       | `jazzoo.modules.rules.get_module_by_path`     | `get_module_by_path(module, "a.b") -> T.Optional[Module]`                                                                          |
| `main`                 | entrypoint | `jazzoo.runtime.entrypoints.jazzoo`           | `main(argv) -> int`; never raises for user errors, prints `<file>:<line>: error: <msg>` to stderr                                  |
| `save_fixture`         | util       | `jazzoo.runtime.utils.test_utils`             | **already exists, do not touch**                                                                                                   |

There are two path-walkers, `get_module_by_path` and
`get_function_by_path`, and they should agree on their edge cases: an unresolvable
segment returns `None` rather than raising (the tests assert `is None` for
`"baz.bar"`, `"foo.secret"` and `"other"`), the walk descends through sub-modules for
every segment but the last, and only the last segment is looked up as a function.
Writing them as a shared walk plus a differing final lookup is the obvious
implementation.

Two facts about these signatures deserve emphasis, because they shape everything
downstream:

**`evaluate` is the single execution entry point.** It takes a _source string_, not
a `Function`. `evaluate(root_module, '🐭.build(target="myapp")')` parses that string
as a jazzoo expression in the context of `module`, evaluates it, and returns the
resulting string. That means the same expression evaluator used for right-hand sides
of assignments inside a body is also the public test API. Tests call it with:

- a call: `🐭.go()`, `🐭.help(who="jane")`, `🐭.h.report()`
- a bare variable: `🐐.test`, `🐭.test`, `🐭.also-bare`

So `evaluate` must not special-case calls. It evaluates an expression; a call is one
kind of expression.

**`parse_module` does far more than parse — it executes.** Per design §12, everything
decidable from the parse tree is raised at load time. `parse_module` therefore also:
resolves imports and exports (recursively, with a path-keyed cache), evaluates
module-level variable assignments, and validates every call site, curry expression and
pipe stage in the file. A large share of the error tests call `parse_module` alone and
expect a raise. This is the single most load-bearing function in the system.

Crucially, evaluating a module-level assignment can **spawn subprocesses**, because the
right-hand side may be a function call whose body is a shebang block.
So merely importing a module can fire shebang blocks. Two consequences:

1. **`parse_module` is an action, not a rule** (see §2), and so is `evaluate`.
2. Import resolution must be **depth-first with a cycle-aware cache**: the cache entry
   is created _before_ the module's assignments run, so a re-entrant import gets the
   partially-initialized module (design §14). A call into a module whose assignments
   have not finished is the `ModuleImportError` that
   `test_load_time_circular_imports_are_a_module_import_error` expects — the `Module`
   model needs an `is_initialized` flag to detect it.

---

## 2. Code structure

Four feature packages, split by what they are about rather than by layer:
`expressions` (the value language), `functions` (callables and their invocation),
`blocks` (shebang bodies and substitution), and `modules` (files, scopes, imports).

```
src/jazzoo/
├── __init__.py                       # ← public façade: re-exports the public names (see below)
├── settings.py                       # FALSY_VALUES, DEFAULT_FILENAMES, DEFAULT_SHEBANG
├── errors.py                         # ← public: the six exception classes
├── enums.py                          # Sigil, BlockMode
├── grammar/jazzoo.lark               # phase-1 grammar
│
├── expressions/                      # the value language: refs, ternaries, paths, pipes
│   ├── models/
│   │   ├── reference.py              # Reference: sigil, parts, optional, default
│   │   ├── ternary.py                # Ternary: value, condition, otherwise
│   │   ├── path_join.py              # PathJoin: left, right
│   │   └── pipe.py                   # Pipe: value, stages
│   ├── rules/
│   │   ├── parse_expression.py       # source → expression tree
│   │   ├── resolve_reference.py      # Reference + context → str, honours ? and :-
│   │   ├── parse_references.py       # scan a line for bare/braced refs, honour \
│   │   ├── substitute_references.py  # textual substitution in one line
│   │   └── is_truthy.py              # the falsy-string rule
│   ├── actions/
│   │   ├── evaluate.py               # ← public: source string + module → str
│   │   └── evaluate_expression.py    # tree + context → str; may call functions
│   └── utils/
│       ├── join_path.py              # pure string path join
│       ├── shell_quote.py            # ⚙️.sh-quote
│       └── strip_one_newline.py      # ⚙️.stdout → ⚙️.output
│
├── functions/                        # callables: signatures, currying, invocation
│   ├── models/
│   │   ├── parameter.py              # Parameter: name, default
│   │   ├── function.py               # Function(Scope): parameters, is_target, dependencies, body
│   │   ├── curried_function.py       # CurriedFunction: function, bound, unbound
│   │   └── call_site.py              # CallSite: target_path, arguments, filename, line
│   ├── rules/
│   │   ├── get_targets.py            # ← public
│   │   ├── get_function_by_path.py   # ← public
│   │   ├── bind_arguments.py         # args + parameters + curry → 🐆 variables
│   │   ├── validate_call_site.py     # arity/name checks → ArgumentError
│   │   └── validate_pipe_stage.py    # exactly-one-unbound → ArgumentError
│   └── actions/
│       └── call_function.py          # run dependencies, run body, resolve 🐆.retval
│
├── blocks/                           # shebang bodies: sweeping and execution
│   ├── models/
│   │   └── block.py                  # Block: shebang, lines, first_line_no
│   ├── rules/
│   │   └── sweep_block.py            # extract assignments, substitute the rest
│   └── actions/
│       └── run_block.py              # execute one swept block → stdout
│
├── modules/                          # files, scopes, imports
│   ├── models/
│   │   ├── variable.py               # Variable
│   │   ├── scope.py                  # Scope (variables, functions)
│   │   ├── module.py                 # Module(Scope): filename, modules, is_initialized
│   │   ├── import_statement.py       # ImportStatement: path, symbols, alias, is_export
│   │   └── context.py                # Context: module, root_module, function_scope
│   ├── rules/
│   │   └── get_module_by_path.py     # ← public; single-segment is just the 1-iteration case
│   └── actions/
│       ├── parse_module.py           # ← public: parse + wire imports + run module-level assignments
│       └── resolve_import.py         # one import/export statement → Module wiring
│
└── runtime/
    ├── entrypoints/jazzoo.py         # main(argv) -> int
    └── utils/test_utils.py           # exists
```

### The jazzoo/**init**.py file

**A top-level façade in `jazzoo/__init__.py`.** Deep paths are right for the
implementation and wrong for the caller: nobody outside the package should have to know
that `evaluate` lives under `expressions.actions`. So `__init__.py` re-exports the
public names, and the tests import from there:

```python
# jazzoo/__init__.py
from jazzoo.errors import (
    ArgumentError, ExecutionError, JazzooError,
    ModuleImportError, ParseError, ResolutionError,
)
from jazzoo.expressions.actions.evaluate import evaluate
from jazzoo.functions.rules.get_function_by_path import get_function_by_path
from jazzoo.functions.rules.get_targets import get_targets
from jazzoo.modules.actions.parse_module import parse_module
from jazzoo.modules.rules.get_module_by_path import get_module_by_path

__all__ = [...]
```

Every test import then collapses to `from jazzoo import parse_module, evaluate`, which
is both shorter than the original and stable against any future re-layout — moving a
unit becomes a one-line edit in `__init__.py` and touches no test at all. This is worth
more than the shim it superficially resembles: a shim duplicates a _path_, whereas the
façade defines the package's public surface in one place, which is a thing worth having
on its own terms.

### Line numbers

**Why `Block` carries `first_line_no`.** `test_a_run_time_error_carries_its_source_location`
asserts `excinfo.value.line == 3` for a failing line in a body, and
`test_an_error_is_attributed_to_the_module_that_contains_it` asserts the failure is
attributed to the _imported_ file, not the caller. Line numbers must be threaded
through the parse tree from the very first commit — retrofitting them later means
touching every model. Every model that can appear in an error message carries
`filename` and `line`.

---

## 3. Stages

Each stage ends with a green test run. Tests not yet in scope are skipped with a
module- or function-level marker (see §4).

### Stage 0 — Skeleton and errors

**Build, as two separate commits:**

1. _Import rewrite only._ Move the test imports to the §2 paths — 50 lines across 11
   files, no other edit. This commit must not add a single line of implementation, so
   that it can be reviewed as a pure rename.
2. _Skeleton._ `errors.py`, `enums.py`, `settings.py`, the `models/` of all four
   feature packages, `__init__.py` with the full façade, and stubs for every public
   name that raise `NotImplementedError` _from the body_ (never at import — see §4).
   Add `pytest.ini`/`pyproject` config so `tests/` is on the path. Register the `jaz`
   alias alongside `jazzoo` in `[project.scripts]`.

   Add one guard test that enforces the no-`from jazzoo import` rule mechanically, so
   the façade cannot rot:

   ```python
   def test_no_submodule_imports_from_the_package_root():
       root = pathlib.Path(jazzoo.__file__).parent
       offenders = [
           p.relative_to(root)
           for p in root.rglob("*.py")
           if p.name != "__init__.py"
           and re.search(r"^from jazzoo import ", p.read_text(), re.M)
       ]
       assert offenders == []
   ```

**Enables:** `test_errors.py::test_every_error_derives_from_jazzoo_error`,
`test_no_error_shadows_a_python_builtin`. Everything else stays skipped.

**Why first:** these two tests need nothing but the exception hierarchy, and every
later stage imports it. It is a short stage that de-risks the import graph — and after
commit 1, every test file imports something that exists, which is what makes the skip
mechanism in §4 work at collection time.

### Stage 1 — Parse, list, run a flat file

This is the biggest single stage and the one that makes the tool exist.

**Build:**

- `grammar/jazzoo.lark` covering: module-level assignments, function definitions with
  parameters and defaults, `[private]`, dependencies after the colon (including the
  `\`-continued form), bodies as indented line groups, and shebang-block boundaries.
  Bodies are captured as opaque lines (design §11) — the grammar must _not_ try to
  parse shell.
- `parse_module` for a single file: build `Module`, `Function`, `Parameter`, `Block`;
  enforce the name-uniqueness rule (§13); evaluate module-level assignments.
- `run_block` (default bash mode, one subprocess per line; explicit shebang mode, one
  subprocess per block) and `call_function` (bind arguments, run dependencies, run
  body, resolve `🐆.retval`).
- `substitute_references` / `parse_references` / `resolve_reference` for `🐐`, `🐭`,
  `🐆` bare and braced, with `\` escaping and `\` as name terminator.
- `evaluate` handling: a bare reference, and a call with named arguments.
- `get_targets`, `get_function_by_path` (single-segment paths only).
- The `@` marker for suppressed console echo, and the normal echo of each command.

**Enables (fully):** `test_shebang_blocks.py`, `test_substitutions.py` minus the
`⚙️.env` and marker tests, and the non-import, non-curry parts of `test_functions.py`.

**Why here:** every remaining feature is expressed in terms of "run a body and get
its stdout". Sweeping, `⚙️.stdout`/`⚙️.output` and per-line subprocess isolation are
the core semantics; if they are wrong, every later test is debugging two things at
once.

**Ordering caution:** implement `⚙️.stdout`/`⚙️.output` and the `🐆.retval` fallback in
this stage even though they look like "system variables". `test_functions.py`'s return-value
tests depend on them, and deferring them would mean skipping half of `test_functions.py`
for no gain.

### Stage 2 — Expressions

**Build:** `parse_expression` + `evaluate_expression` covering ternaries
(right-associative, `==` and bare truthiness), `is_truthy` with the falsy-string set,
the `/` path operator (left-associative, pure string join), and the `⚙️` pipe
operators `abs`, `basename`, `dirname`, `ext`, `stem`, `sh-quote`. Precedence: `|`
binds looser than `/`, so `a / b | ⚙️.abs` resolves the whole join and
`a | ⚙️.abs / b` resolves the prefix (`test_abs_applies_after_the_whole_join_or_to_the_prefix_only`
pins this exactly).

**Enables:** `test_expressions.py` in full; `test_sh_quote_renders_a_value_as_one_shell_word`.

### Stage 3 — System variables and reference markers

**Build:** the `⚙️` namespace — `module.{basename,path,dirname}`,
`root_module.{basename,path,dirname}`, `env.*`; rejection of any assignment whose LHS
sigil is `⚙️` (a grammar-level rejection, which makes it a `ParseError` — the test
only pins `JazzooError`); and the `?`, `:-`, `?:-` markers in `resolve_reference`,
including bare vs. quoted defaults and the `\`-terminates-before-a-marker rule.

**Enables:** `test_system_variables.py` in full; the remaining `test_substitutions.py`
tests.

**Ordering caution:** `⚙️.module.*` must resolve against the module the _line_ lives
in, not the module that started the run. That is a property of the execution context
object, so decide the context's shape in stage 1 (`{module, function_scope, root_module}`)
rather than bolting `root_module` on here.

### Stage 4 — Imports and exports

**Build:** `resolve_import`, the module cache keyed by resolved absolute path, the
`import ... as ns` (private) and `export ...` (public) forms including tuples,
aliases and `*`; `get_module_by_path`, and multi-segment
paths in `get_function_by_path`; `🐭.ns.fn()` call resolution; per-module `🐭` scoping
with a shared `🐐`; and `ModuleImportError` for a missing file, an unknown symbol, a
privately-imported symbol, and a load-time cycle.

**Enables:** `test_imports.py`, `test_exports.py`,
`test_cli.py::test_imported_targets_are_not_listed_but_exported_ones_are`,
`test_functions.py::test_mid_body_call_to_imported_module`, and the per-module system
variable tests.

**Why after stage 3:** `test_the_module_variables_are_per_module` and
`test_root_module_system_variables_name_the_entry_point` are import tests wearing a
system-variable hat. Doing imports first would force stubbing `⚙️.module`; doing
system variables first means the import stage validates them for free.

**Ordering caution — load-time execution.** This is the stage where "importing a module
runs code" becomes visible, so `parse_module` must be written in this precise order per
file: (1) parse, (2) insert the `Module` into the cache with `is_initialized = False`,
(3) recursively load each import, (4) run this file's module-level assignments, (5) set
`is_initialized = True`. Step 2 before step 3 is what makes a cycle terminate; step 4
after step 3 is what makes `🐭.eager = 🐭.r.value()` resolve. A call that reaches a
module still sitting at `is_initialized = False` is the load-time cycle, and raises
`ModuleImportError`.

Note this means stage 4 is the first stage where a _parse_ test can fail because a
_subprocess_ failed. Budget debugging time accordingly; the error location has to
survive the trip out of the nested load.

### Stage 5 — Currying and pipes

**Build:** `CurriedFunction` values, `f[...]` with bound values and bare unbound
names, the bare-symbol-equals-`f[]` equivalence, calling a variable that holds a
function, function-valued pipe stages, and `validate_pipe_stage` /
`validate_call_site` for the five `ArgumentError` cases in
`test_pipes_and_currying.py`.

**Enables:** `test_pipes_and_currying.py` in full;
`test_functions.py::test_a_curried_function_may_not_shadow_an_existing_name`.

**Why late:** currying is the only feature that makes a `Variable`'s value
polymorphic. Every earlier stage can assume `value: str`, which keeps resolution
simple; widening the type once, at a point where the rest is green, is cheaper than
carrying the union from the start.

### Stage 6 — Local functions

**Build:** `🐆.name(params):` definitions inside a body, nesting, a fresh `🐆` scope
per invocation (including a fresh `retval` and `stdout`), lexical scoping so a local
is invisible to sibling functions, and `ResolutionError` for an out-of-scope local.

**Enables:** `test_local_functions.py` in full;
`test_functions.py::test_a_local_function_does_not_overwrite_the_callers_retval`.

**Note:** the `@`-marker tests live in `test_local_functions.py` but do not depend on
local functions (`test_the_at_marker_suppresses_console_output` uses plain targets).
They are enabled back in stage 1; only `test_the_at_marker_applies_inside_a_local_function`
waits for this stage.

### Stage 7 — CLI and error presentation

**Build:** `runtime/entrypoints/jazzoo.py` with `_parse_args()` per the entrypoint
skill: `--file`, `--list`, `--trace`, a target name, `name=value` arguments, and the
first-parameter positional shorthand with its two error cases. Default-file discovery
(`jazzoo`, then `jazzoo.jaz`). Bare `jaz` lists targets. `main` catches `JazzooError`,
prints `<file>:<line>: error: <message>` to stderr, returns non-zero, and adds the
traceback only under `--trace`.

**Enables:** `test_cli.py` in full; the presentation half of `test_errors.py`.

**Why last:** `main` is a thin shell over `parse_module` + `evaluate` + `get_targets`.
Written first it would be a mock harness; written last it is roughly 120 lines with
no logic of its own.

---

## 4. Skip mechanism

**Decision: `pytest.ini` markers plus a `conftest.py` autoskip, driven by one
`IMPLEMENTED_STAGE` constant.**

Do _not_ comment tests out and do not edit assertions. The suite is the spec; a
commented-out test is invisible, and a diff that touches assertion text is a diff
that can silently weaken the spec. Instead, add exactly one line per test file or
test function and one small `conftest.py`:

```python
# tests/conftest.py
import pytest

# Bump this as each stage lands; everything above it is skipped.
IMPLEMENTED_STAGE = 0


def pytest_collection_modifyitems(config, items):
    for item in items:
        marker = item.get_closest_marker("stage")
        if marker is None:
            continue
        stage = marker.args[0]
        if stage > IMPLEMENTED_STAGE:
            item.add_marker(
                pytest.mark.skip(reason=f"stage {stage} not implemented yet")
            )
```

```ini
# pytest.ini  (or [tool.pytest.ini_options] in pyproject.toml)
[pytest]
markers =
    stage(n): the implementation stage that makes this test pass
testpaths = tests
```

Marking is then one decorator per test, or `pytestmark = pytest.mark.stage(N)` at the
top of a file where the whole file belongs to one stage.

Why this over the alternatives:

- **vs. `@pytest.mark.skip` per test:** those have to be hand-removed one by one, and
  it is easy to leave one behind. A single integer flips a whole stage on.
- **vs. `--deselect` in the pytest invocation:** invisible in the source, and it does
  not survive someone running `pytest` bare.
- **vs. `xfail`:** `xfail` runs the test, and a stage-6 test on a stage-1 codebase
  fails inside a subprocess or hangs. Skip is the honest signal here.

`IMPLEMENTED_STAGE` reaching `7` with no markers left firing is the definition of
done, and the flag itself should be deleted in the final commit along with the
`conftest.py` hook.

### Stage assignment per file

| File                         | Stage(s)                                                                                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_errors.py`             | 0 for the two class-hierarchy tests; 1 for `test_syntax_that_does_not_parse_is_a_parse_error`; 4 for the imported-module attribution test; 7 for the rest |
| `test_shebang_blocks.py`     | 1 (whole file)                                                                                                                                            |
| `test_functions.py`          | 1, except: currying test → 5, local-function retval test → 6, imported-module call → 4                                                                    |
| `test_substitutions.py`      | 1, except the `⚙️.env`, `?`, `:-` and read-only tests → 3                                                                                                 |
| `test_expressions.py`        | 2 (whole file)                                                                                                                                            |
| `test_system_variables.py`   | 3, except `test_the_module_variables_are_per_module` → 4                                                                                                  |
| `test_imports.py`            | 4 (whole file)                                                                                                                                            |
| `test_exports.py`            | 4 (whole file)                                                                                                                                            |
| `test_pipes_and_currying.py` | 5 (whole file)                                                                                                                                            |
| `test_local_functions.py`    | 6, except the two `@`-marker tests → 1 and 6                                                                                                              |
| `test_cli.py`                | 7 (whole file)                                                                                                                                            |

Note that `test_pipes_and_currying.py` and `test_imports.py` call `save_fixture` at
_module import time_ to build their library fixtures. That runs even when every test
in the file is skipped, which is harmless — but it means those files must not import
anything that does not exist yet at collection time. Keeping every stub importable
from stage 0 onward (raising `NotImplementedError` from the body, never at import)
is what makes the skip mechanism work at all.

---

## 5. Deliberate gaps

Two things in the design have no test and are not built:

- **`set shell`** — design §14 lists it as unspecified. Not implemented; the default
  interpreter is `#!/usr/bin/env bash`, held in `settings.py` so it is one edit if
  the question is settled later.
