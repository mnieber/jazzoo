# Jazzoo (🐐🐭🐆) — Design Document

Jazzoo is a task runner in the spirit of `just`, with a three-tier variable namespace system, emoji sigils, and a clean module/import model. The CLI is invoked as `jazzoo` or `jz`. The tool can also be written as 🐐🐭🐆, which encodes its three namespace animals.

---

## 1. File Format

Jazzoo files use the `.jz` extension. The default file is `jazzoo` (no extension) in the current directory, falling back to `jazzoo.jz` if not found.

---

## 2. Namespaces

Jazzoo has three variable (and callable) namespaces, each identified by an emoji sigil:

| Sigil | Name    | Scope                                  |
| ----- | ------- | -------------------------------------- |
| 🐐    | Goat    | Global — shared across all modules     |
| 🐭    | Mouse   | Module — scoped to the defining file   |
| 🐆    | Leopard | Local — scoped to the current callable |

`🐐` variables are truly global and visible everywhere. `🐭` variables and recipes are scoped to the file they are defined in — when a recipe from module B is called by module A, `🐭` resolves against B's scope, not A's. `🐆` variables are scoped to the callable invocation and do not leak to the caller.

---

## 3. Variable Declaration and Types

### Global and module variables

Declared at the top level of a `.jazz` file:

```
🐐.log-level = "high"
🐭.tracing = True
```

### Types

All values are strings. There are no integers. Path expressions (see section 5) produce path values, which are strings that may be canonicalized — see below.

### Truthiness

In ternary expressions, a string value is falsy if its lowercased form is in `["0", "false", "no", ""]`. All other strings are truthy. This allows natural use of env-var-style boolean flags.

### Magic variables

Jazzoo provides built-in read-only variables using uppercase snake_case names. Module-scoped magic variables reflect the file they appear in:

| Variable        | Scope | Value                                                   |
| --------------- | ----- | ------------------------------------------------------- |
| `🐭.FILE_NAME`  | 🐭    | Filename of the current module (e.g. `index.jz`)        |
| `🐭.FILE_PATH`  | 🐭    | Absolute path of the current module file                |
| `🐭.DIR_PATH`   | 🐭    | Absolute path of the directory containing the current module |
| `🐐.FILE_NAME`  | 🐐    | Filename of the entry-point `.jz` file invoked by `jz`  |
| `🐐.FILE_PATH`  | 🐐    | Absolute path of the entry-point `.jz` file             |
| `🐐.DIR_PATH`   | 🐐    | Absolute path of the directory containing the entry-point file |

`🐐.DIR_PATH` is particularly useful for resolving project-root-relative paths regardless of where `jz` is invoked from.

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

Canonicalization (resolving `..`, symlinks, etc.) is applied only when the result is an absolute path. Relative results are kept as-is — a simple string join with `/`.

Path expressions can be chained: `a / b / c` is left-associative.

---

## 6. Recipes

### Basic recipe

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

### Recipe attributes

Attributes are declared on the line before the recipe:

```
[private]
_helper(name):
    echo "Internal helper: 🐆.name"
```

`[private]` recipes do not appear in `jz --list` but are still callable from within `.jazz` files.

### Recipe dependencies

Dependencies are declared after the colon, before the body:

```
debug(name="me"): _helper(name=🐆.name)
    echo "Running debug for: 🐆.name"
```

Dependencies run before the recipe body. Dependency arguments may reference `🐐`, `🐭`, and the recipe's own parameters — but not local `🐆` assignments, since those don't exist yet.

### Mid-recipe calls

Recipes in the current module can be called mid-body using the `🐭` sigil:

```
debug(name="me"):
    🐭._helper(name="anonymous")
    echo "Done"
```

Calls to imported modules use the module alias (see section 9):

```
    🐭.docker.build(target="myapp")
```

All recipe calls block until completion.

### Return values

A recipe can return a value by setting `🐆.retval`:

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

## 7. Local Callables

A recipe can define local callables scoped to `🐆`. These are structurally identical to `🐭` recipes but are only accessible within the enclosing recipe.

```
help(who="me"):
    🐆.dump(who):
        echo "Hello 🐆.who! Tracing is: 🐭.tracing"

    🐆.retval = 🐆.dump(who=🐆.who)
```

Local callables have their own fresh `🐆` namespace — variables set inside do not leak to the parent. Parameters are passed explicitly. Local callables support the same body forms as regular recipes: shell lines, assignments, shebang blocks, and nested local callables.

---

## 8. Shebang Blocks

A recipe or local callable body can use a shebang block to run an alternative interpreter:

```
help:
    #!/usr/bin/env python3
    print("Tracing is: 🐭.tracing, fyi")
    return "done"
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

Because trimming determines whether a line is a Jazzoo assignment, indentation makes no difference — `🐆.x = foo` inside a Python `for` loop is still extracted. This means Jazzoo assignments inside loops or conditionals behave as static substitutions, not dynamic ones. Use Python variables for dynamic in-block logic.

To assign a Python variable whose *name* comes from a Jazzoo value, use a braced reference — this is not a leading sigil so it passes through the sweep as a regular line:

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

After any shell line, shebang block, or recipe call completes, jazzoo sets `🐆.stdout` to its full stdout output. This makes `🐆.stdout` uniformly "the stdout of the last thing that ran."

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
    echo "last recipe outputted: 🐆.stdout"
```

`🐆.stdout` is overwritten after each such step and is not set before the first one runs.

---

## 9. Imports

Paths are always explicit relative or absolute — no search path resolution.

### Importing into a namespace (private)

Imported recipes are always placed under a namespace alias and are private — not visible to outside importers.

```
from ./foo.jz import bar as baz                    # 🐭.baz.bar()
from ./foo.jz import (bar, okay) as baz            # 🐭.baz.bar(), 🐭.baz.okay()
from ./foo.jz import (bar as hello, okay) as baz   # 🐭.baz.hello(), 🐭.baz.okay()
from ./foo.jz import * as foo                      # 🐭.foo.<all exported recipes>()
```

The trailing `as <namespace>` is mandatory. Without a tuple, the single symbol is placed under the namespace: `import bar as baz` makes the recipe callable as `🐭.baz.bar()`, not `🐭.baz()`.

The imported module's `🐭` variables resolve against the imported file's scope, not the caller's. `🐐` globals are shared across all modules.

### Exporting into the module namespace (public)

Exported recipes land flat in `🐭` and are public — visible to outside importers, the CLI, and `jz --list`.

```
from ./foo.jz export bar                           # 🐭.bar()
from ./foo.jz export bar as hello                  # 🐭.hello()
from ./foo.jz export (bar, okay)                   # 🐭.bar(), 🐭.okay()
from ./foo.jz export (bar as hello, okay)          # 🐭.hello(), 🐭.okay()
from ./foo.jz export *                             # 🐭.<all exported recipes from foo>()
```

`export *` includes only recipes that `foo.jz` itself exports — it does not transitively pull in recipes that `foo.jz` imported privately.

### Import/export semantics summary

| Form                                    | Callable as         | CLI / `jz --list` |
| --------------------------------------- | ------------------- | ----------------- |
| `from ./foo.jz import bar as ns`        | `🐭.ns.bar()`       | ✗                 |
| `from ./foo.jz import (a, b) as ns`     | `🐭.ns.a()`, `🐭.ns.b()` | ✗            |
| `from ./foo.jz import * as ns`          | `🐭.ns.<recipe>()`  | ✗                 |
| `from ./foo.jz export bar`              | `🐭.bar()`          | ✓                 |
| `from ./foo.jz export bar as hello`     | `🐭.hello()`        | ✓                 |
| `from ./foo.jz export *`               | `🐭.<recipe>()`     | ✓                 |

---

## 10. CLI

```
jz <recipe> [arg=value ...]   # run a recipe
jz --list                     # list available recipes
jz --dry-run <recipe>         # show what would execute without running
```

### Argument passing

Arguments are always named:

```
jz debug name=maarten
```

As a convenience, the first declared parameter of a recipe may be passed positionally at the CLI:

```
jz build myapp        # equivalent to: jz build target=myapp
```

Passing the same argument both positionally and by name is an error. If mixing positional and named, the positional argument must come first.

Within `.jazz` files, all arguments must be named — positional shorthand is CLI-only.

### Default recipe

Running `jz` with no arguments lists available recipes.

---

## 11. Two-Phase Execution

Jazzoo processes `.jz` files in two phases:

**Phase 1 — Jazzoo parser (Lark/PEG):** Parses the full file structure — global/module declarations, recipe definitions, attributes, dependencies, imports, assignments, and expressions.

**Phase 2 — Template substitution:** Before each shell line or shebang block is executed, jazzoo performs variable substitution: bare references, braced references, and escape sequences are resolved against the current namespace state.

Shell lines and shebang blocks are otherwise treated as opaque strings by phase 1.

---

## 12. Open Questions

- **`set shell`**: Should jazzoo support configuring the default shell (e.g. bash vs sh vs fish)? Currently unspecified.
- **Circular imports**: Behaviour on circular imports is undefined — likely a load-time error.
- **Module-qualified CLI calls**: How to invoke a non-re-exported recipe directly by CLI for debugging purposes (e.g. `jz --debug docker.build`)? Currently not supported.
