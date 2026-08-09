# Jazzoo (🐐🐭🐆) — Design Document

Jazzoo is a task runner in the spirit of `just`, with a three-tier variable namespace system, emoji sigils, and a clean module/import model. The CLI is invoked as `jazzoo` or `jaz`. The tool can also be written as 🐐🐭🐆, which encodes its three namespace animals.

---

## 1. File Format

Jazzoo files use the `.jaz` extension. The default file is `jazzoo` (no extension) in the current directory, falling back to `jazzoo.jaz` if not found.

---

## 2. Namespaces

Jazzoo has three variable (and callable) namespaces, each identified by an emoji sigil:

| Sigil | Name    | Scope                                  |
| ----- | ------- | -------------------------------------- |
| 🐐    | Goat    | Global — shared across all modules     |
| 🐭    | Mouse   | Module — scoped to the defining file   |
| 🐆    | Leopard | Local — scoped to the current callable |

`🐐` variables are truly global and visible everywhere. `🐭` variables and functions are scoped to the file they are defined in — when a function from module B is called by module A, `🐭` resolves against B's scope, not A's. `🐆` variables are scoped to the function invocation and do not leak to the caller.

---

## 3. Variable Declaration and Types

### Global and module variables

Declared at the top level of a `.jaz` file:

```
🐐.log-level = "high"
🐭.tracing = True
```

### Types

All values are strings. There are no integers. Path expressions (see section 5) produce path values, which are strings that may be canonicalized — see below.
TODO: Can values be lists, dicts and sets?

### Truthiness

In ternary expressions, a string value is falsy if its lowercased form is in `["0", "false", "no", ""]`. All other strings are truthy. This allows natural use of env-var-style boolean flags.
TODO: If values can be lists, dicts and sets then we need falsy values for those.

### Magic variables

Jazzoo provides built-in read-only variables using uppercase snake_case names. Module-scoped magic variables reflect the file they appear in:

| Variable       | Scope | Value                                                          |
| -------------- | ----- | -------------------------------------------------------------- |
| `🐭.FILE_NAME` | 🐭    | Filename of the current module (e.g. `index.jaz`)              |
| `🐭.FILE_PATH` | 🐭    | Absolute path of the current module file                       |
| `🐭.DIR_PATH`  | 🐭    | Absolute path of the directory containing the current module   |
| `🐐.FILE_NAME` | 🐐    | Filename of the entry-point `.jaz` file invoked by `jaz`       |
| `🐐.FILE_PATH` | 🐐    | Absolute path of the entry-point `.jaz` file                   |
| `🐐.DIR_PATH`  | 🐐    | Absolute path of the directory containing the entry-point file |

`🐐.DIR_PATH` is particularly useful for resolving project-root-relative paths regardless of where `jaz` is invoked from.

---

## 4. Variable Substitution

### Bare references

Jazzoo variables can be referenced directly in shell lines and strings without any escaping:

```
echo "Running test with log level: 🐐.log-level for user: 🐆.name"
docker compose up --log-level=🐐.log-level 🐆.dry-run
```

The `-` character is valid in variable names. This means `--log-level=🐐.log-level` resolves naturally, so the shell option name and the variable name can be identical.

### Braced references

Use `{{ }}` when a variable reference is adjacent to other text:

```
echo "Running test with log level: {{ 🐐.log-level }}-setting"
```

### Escaping

Prefix the emoji sigil with `\` to suppress substitution:

```
echo "Running test with \🐭.tracing set to: 🐭.tracing"
echo "Running test with \🐭.tracing set to: 🐭.tracing\.com"  # prints .com after the value of 🐭.tracing
```

This prints the literal emoji and `.tracing` text for the escaped reference, and substitutes the unescaped one.

To produce a literal `{{ 🐐.log-level }}` string:

```
echo "Jazzoo supports the {{ \🐐.log-level }}-setting syntax"
```

### Substitution rules summary

| Syntax                | Result                       |
| --------------------- | ---------------------------- |
| `🐐.log-level`        | Substituted (bare)           |
| `{{ 🐐.log-level }}`  | Substituted (braced)         |
| `\🐐.log-level`       | Literal emoji + `.log-level` |
| `{{ \🐐.log-level }}` | Literal `{{ 🐐.log-level }}` |

---

## 5. Expressions

### Assignment

```
🐆.dry-run = "--dry-run" if 🐐.log-level == "high" else ""
```

### Ternary expressions

Jazzoo supports chained ternary expressions modelled on Python syntax:

```
🐆.x = "a" if 🐐.log-level == "high" else "b" if 🐐.log-level == "low" else ""
```

Chaining is right-associative: `A if C1 else (B if C2 else C)`. Only string equality (`==`) is supported as a condition, plus bare variable truthiness testing (see section 3).

### Path expressions

The `/` operator joins two string values as path segments, producing a new string:

```
🐭.config = 🐭.get_base_path() / "../config.json"
🐆.out = 🐭.DIR_PATH / "build/output"
```

Path joins are a **pure string join** — `..`, symlinks, and redundant separators are left untouched. Path expressions can be chained: `a / b / c` is left-associative. Joining never canonicalizes on its own; the only way to canonicalize is the explicit goat marker below.

#### Explicit resolution: `/ 🐐`

Placing `🐐` as a path segment canonicalizes the path accumulated **to its left** — resolving `..`, `.`, symlinks, and redundant separators — at the point where it appears. It is left-associative, like `/`, and reads as "resolve everything so far":

```
🐭.config = 🐭.get_base_path() / "../config.json" / 🐐   # resolve the whole join
🐭.config = 🐭.get_base_path() / 🐐 / "../config.json"   # resolve the prefix, then join "../config.json" as a raw string
```

Semantics:

- **Left-fold trigger.** In `a / b / 🐐 / c / d`, the prefix `a / b` is canonicalized first, then `c` and `d` are joined onto the result as raw strings. A trailing `/ 🐐` resolves the entire expression.
- **Presence is the sole trigger.** A join with no `🐐` is _always_ a pure string join and is never canonicalized, regardless of whether the result is absolute or relative.
- **Repeatable.** `🐐` may appear more than once; each occurrence canonicalizes the path accumulated up to that point. This makes "resolve a base, append, then re-resolve" expressible: `base / 🐐 / "../x" / 🐐`.
- **Relative prefixes resolve against CWD.** If the accumulated prefix is relative when `🐐` is applied, it is canonicalized relative to the current working directory (the directory `jaz` was invoked from), matching `pathlib.Path.resolve()`.

Note that `🐐` in path position is a resolution marker, not a namespace reference — it is the one context where the bare goat sigil does not denote the global namespace.

---

## 6. Functions

### Basic function

```
debug(name="me"):
    🐆.dry-run = "--dry-run" if 🐐.log-level == "high" else ""
    echo "Running test with log level: 🐐.log-level for user: 🐆.name"
    docker compose up --log-level=🐐.log-level 🐆.dry-run
```

### Parameters

Parameters are always named. A parameter may have a default value or be required (no default):

```
build(target, mode="release"):
    cargo build --target=🐆.target --profile=🐆.mode
```

### Function attributes

Attributes are declared on the line before the function:

```
[private]
_helper(name):
    echo "Internal helper: 🐆.name"
```

`[private]` functions are not targets — they do not appear in `jaz --list` and cannot be invoked from the CLI, but are callable from within `.jaz` files.

### Function dependencies

Dependencies are declared after the colon, before the body:

```
debug(name="me"): _helper(name=🐆.name)
    echo "Running debug for: 🐆.name"
```

Dependencies run before the function body. Dependency arguments may reference `🐐`, `🐭`, and the function's own parameters — but not local `🐆` assignments, since those don't exist yet.

### Mid-body calls

Functions in the current module can be called mid-body using the `🐭` sigil:

```
debug(name="me"):
    🐭._helper(name="anonymous")
    echo "Done"
```

Calls to imported modules use the module alias (see section 10):

```
    🐭.docker.build(target="myapp")
```

All function calls block until completion.

### Return values

A function can return a value by setting `🐆.retval`:

```
make-full-path(input):
    🐆.retval = "/data/🐆.input"
```

The caller captures it via assignment:

```
🐆.full-path = 🐭.make-full-path(input="input.json")
```

Return values must be strings or booleans (booleans are auto-converted to `"true"` / `"false"`). Statement calls (not assigned) silently discard any return value.

---

## 7. Local Functions

A function can define local functions scoped to `🐆`. These are structurally identical to `🐭` functions but are only accessible within the enclosing function.

```
help(who="me"):
    🐆.dump(who):
        echo "Hello 🐆.who! Tracing is: 🐭.tracing"

    🐆.retval = 🐆.dump(who=🐆.who)
```

Local functions have their own fresh `🐆` namespace — variables set inside do not leak to the parent. Parameters are passed explicitly. Local functions support the same body forms as regular functions: shell lines, assignments, shebang blocks, and nested local functions.

---

## 8. Shebang Blocks

A function or local function body can use a shebang block to run an alternative interpreter:

```
help:
    #!/usr/bin/env python3
    print("Tracing is: 🐭.tracing, fyi")
    return "done"

test:
    🐆.result = 🐭.help()  # will contain "done"
```

Before execution, jazzoo sweeps the shebang block top to bottom, processing each line in order:

1. Trim the line. If it matches `<sigil>.<name> = <expression>` (a Jazzoo assignment), evaluate the RHS as a full Jazzoo expression (string literal, ternary, path expression, recipe call — same grammar as outside shebang blocks). Unquoted RHS values are treated as bare strings: `🐆.x = hello` is equivalent to `🐆.x = "hello"`. Update the namespace and remove the line.
2. Otherwise, substitute all Jazzoo references in the line using the current namespace state, and keep the line.

The resulting block — with all Jazzoo assignments removed and all references substituted — is then executed once as a single subprocess.

```
info:
    #!/usr/bin/env python3
    🐆.config = "hello.json"

    import json
    with open("🐆.config") as f:
        cfg = json.load(f)
    print(cfg)

    🐆.config = "bye.json"

    with open("🐆.config") as f:
        cfg = json.load(f)
    print(cfg)

    #!/usr/bin/env bash
    echo "The 🐆.config file was used in our Python shebang block"
```

Sweeps to:

```python
import json
with open("hello.json") as f:
    cfg = json.load(f)
print(cfg)

with open("bye.json") as f:
    cfg = json.load(f)
print(cfg)
```

and

```bash
    echo "The bye.json file was used in our Python shebang block"
```

Because trimming determines whether a line is a Jazzoo assignment, indentation makes no difference — `🐆.x = foo` inside a Python `for` loop is still extracted. This means Jazzoo assignments inside loops or conditionals behave as static substitutions, not dynamic ones. Use Python variables for dynamic in-block logic.

To assign a Python variable whose _name_ comes from a Jazzoo value, use a braced reference — this is not a leading sigil so it passes through the sweep as a regular line:

```python
{{ 🐭.variable }} = "bar"   # e.g. foo = "bar"
```

### Python shebang blocks

The swept block is dedented and wrapped implicitly in a function, so `return` works naturally:

```python
# Generated by jazzoo:
def __jazzoo_block__():
    import json
    with open("hello.json") as f:
        cfg = json.load(f)
    print(cfg)
    ...
__jazzoo_result__ = __jazzoo_block__()
```

The return value must be a string or bool; other types raise an error at runtime.

### Shell shebang blocks

The exit code of a shell block is used as the return value. There is no `return` statement. The same sweep applies — Jazzoo assignments are extracted and references substituted before the block is handed to the shell.

### Stdout capture

After any shell line, shebang block, or function call completes, jazzoo sets `🐆.stdout` to its full stdout output. This makes `🐆.stdout` uniformly "the stdout of the last thing that ran."

```
bar:
    #!/bin/bash
    echo "one"
    echo "two"
    echo "three"

debug(name="me"):
    echo "hello from shell"
    echo "shell line said: 🐆.stdout"

    🐆.foo = 🐭.bar()
    echo "last function outputted: 🐆.stdout"
```

`🐆.stdout` is overwritten after each such step and is not set before the first one runs.

---

## 9. Imports

Paths are always explicit relative or absolute — no search path resolution.

### Importing into a namespace (private)

Imported functions are always placed under a namespace alias and are private — not visible to outside importers.

```
from ./foo.jaz import bar as baz                    # 🐭.baz.bar()
from ./foo.jaz import (bar, okay) as baz            # 🐭.baz.bar(), 🐭.baz.okay()
from ./foo.jaz import (bar as hello, okay) as baz   # 🐭.baz.hello(), 🐭.baz.okay()
from ./foo.jaz import * as foo                      # 🐭.foo.<all exported functions>()
```

The trailing `as <namespace>` is mandatory. Without a tuple, the single symbol is placed under the namespace: `import bar as baz` makes the function callable as `🐭.baz.bar()`, not `🐭.baz()`.

The imported module's `🐭` variables resolve against the imported file's scope, not the caller's. `🐐` globals are shared across all modules.

### Exporting into the module namespace (public)

Exported functions land flat in `🐭` and become targets — visible to outside importers, the CLI, and `jaz --list`.

```
from ./foo.jaz export bar                           # 🐭.bar()
from ./foo.jaz export bar as hello                  # 🐭.hello()
from ./foo.jaz export (bar, okay)                   # 🐭.bar(), 🐭.okay()
from ./foo.jaz export (bar as hello, okay)          # 🐭.hello(), 🐭.okay()
from ./foo.jaz export *                             # 🐭.<all exported functions from foo>()
```

`export *` includes only functions that `foo.jaz` itself exports — it does not transitively pull in functions that `foo.jaz` imported privately.

### Import/export semantics summary

| Form                                 | Callable as              | CLI / `jaz --list` |
| ------------------------------------ | ------------------------ | ------------------ |
| `from ./foo.jaz import bar as ns`    | `🐭.ns.bar()`            | ✗                  |
| `from ./foo.jaz import (a, b) as ns` | `🐭.ns.a()`, `🐭.ns.b()` | ✗                  |
| `from ./foo.jaz import * as ns`      | `🐭.ns.<function>()`     | ✗                  |
| `from ./foo.jaz export bar`          | `🐭.bar()`               | ✓                  |
| `from ./foo.jaz export bar as hello` | `🐭.hello()`             | ✓                  |
| `from ./foo.jaz export *`            | `🐭.<function>()`        | ✓                  |

---

## 10. CLI

```
jaz <target> [arg=value ...]   # run a target
jaz --list                     # list available targets
jaz --dry-run <target>         # show what would execute without running
```

### Argument passing

Arguments are always named:

```
jaz debug name=maarten
```

As a convenience, the first declared parameter of a target may be passed positionally at the CLI:

```
jaz build myapp        # equivalent to: jaz build target=myapp
```

Passing the same argument both positionally and by name is an error. If mixing positional and named, the positional argument must come first.

Within `.jaz` files, all arguments must be named — positional shorthand is CLI-only.

### Default behaviour

Running `jaz` with no arguments lists available targets.

---

## 11. Two-Phase Execution

Jazzoo processes `.jaz` files in two phases:

**Phase 1 — Jazzoo parser (Lark/PEG):** Parses the full file structure — global/module declarations, function definitions, attributes, dependencies, imports, assignments, and expressions.

**Phase 2 — Template substitution:** Before each shell line or shebang block is executed, jazzoo performs variable substitution: bare references, braced references, and escape sequences are resolved against the current namespace state.

Shell lines and shebang blocks are otherwise treated as opaque strings by phase 1.

---

## 12. Scope and Object Model

Jazzoo's parse tree is structured as nested scopes. The entry-point `.jaz` file is the root module. Imported modules are sub-modules of the module that imports them.

```python
class Variable:
    name: str
    value: str

class Scope:
    variables: T.List[Variable]
    functions: T.List[Function]

class Module(Scope):
    filename: str
    modules: T.List[Module]

class Parameter:
    name: str
    default: T.Optional[str]    # None = required

class Function(Scope):
    parameters: T.List[Parameter]
    is_target: bool              # False for [private] functions
```

Key properties:

- **`Module`** is a `Scope` and can contain sub-modules (from imports) and functions.
- **`Function`** is a `Scope` and can contain local functions (section 7), but not sub-modules.
- **Parameters** are the static call signature. At call time, jazzoo validates the arguments against `parameters`, then populates `variables` with the resolved values. The function body only ever reads from `variables`.
- **Targets** are functions with `is_target = True` — i.e. all functions not marked `[private]`. Only targets are callable from the CLI and visible in `jaz --list`.

---

## 13. Open Questions

- **`set shell`**: Should jazzoo support configuring the default shell (e.g. bash vs sh vs fish)? Currently unspecified.
- **Circular imports**: Circular imports are allowed. Modules are cached by resolved file path after first load; a circular import receives the cached partially-initialized module. Circular references used only at call time (mid-body function calls) are safe. Circular references at load time — module-level variable assignments that call into a module not yet fully initialized — are a runtime error. This is the same model as TypeScript (live bindings resolved at access time), which is more predictable than Python's approach (copied values resolved at import time, where failures depend on statement order).
- **Module-qualified CLI calls**: How to invoke a private function directly by CLI for debugging purposes (e.g. `jaz --module docker.build`)? Currently not supported.
