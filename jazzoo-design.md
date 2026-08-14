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

### Truthiness

In ternary expressions, a string value is falsy if its lowercased form is in `["0", "false", "no", ""]`. All other strings are truthy. This allows natural use of env-var-style boolean flags.

### System variables

Jazzoo provides built-in read-only variables:

| Variable                  | Value                                                          |
| ------------------------- | -------------------------------------------------------------- |
| `⚙️.module.basename`      | Filename of the current module (e.g. `index.jaz`)              |
| `⚙️.module.path`          | Absolute path of the current module file                       |
| `⚙️.module.dirname`       | Absolute path of the directory containing the current module   |
| `⚙️.root_module.basename` | Filename of the entry-point `.jaz` file invoked by `jaz`       |
| `⚙️.root_module.path`     | Absolute path of the entry-point `.jaz` file                   |
| `⚙️.root_module.dirname`  | Absolute path of the directory containing the entry-point file |

### Environment variables

⚙️.env.SOME_ALL_CAPS_VALUE refers to an environment variable.

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
🐆.out = ⚙️.module.dirname / "build/output"
```

Path joins are a **pure string join** — `..`, symlinks, and redundant separators are left untouched. Path expressions can be chained: `a / b / c` is left-associative. Joining never canonicalizes on its own; the only way to canonicalize is the explicit goat marker below.

#### Explicit resolution: `| ⚙️.abs`

Placing `| ⚙️.abs` as a path segment pipes the left side of the path to the ⚙️.abs function — resolving `..`, `.`, symlinks, and redundant separators — at the point where it appears. It is left-associative, like `| ⚙️.abs`, and reads as "resolve everything so far":

```
🐭.config = 🐭.get_base_path() / "../config.json" | ⚙️.abs   # resolve the whole join
🐭.config = 🐭.get_base_path() | ⚙️.abs / "../config.json"   # resolve the prefix, then join "../config.json" as a raw string
```

Other pipe operators are:

- ⚙️.basename: yields the basename
- ⚙️.dirname: yields the dirname
- ⚙️.ext: yields the extension
- ⚙️.stem: yields the path except for the extension

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

foo(name="me"): \
        _helper(name=🐆.name) \
        _helper(name=🐭.bar)
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

A function returns `🐆.retval` as it stands when the body finishes. Since every step of a body — shell line, shebang block, or function call — sets `🐆.retval` from its stdout (see section 8), a function returns **the output of the last step that ran**, with a single trailing newline removed:

```
make-full-path(input):
    echo "/data/🐆.input"
```

The caller captures it via assignment:

```
🐆.full-path = 🐭.make-full-path(input="input.json")   # "/data/input.json"
```

This is the same rule as for shebang blocks, applied one level up: a function is a shell tool, and what it writes is what it returns.

A body may also assign `🐆.retval` explicitly. This is how a function returns something other than its last step's output — a literal, a computed expression, or the output of an earlier step:

```
make-full-path(input):
    🐆.retval = "/data/🐆.input"          # no subprocess involved

check(path):
    ls -l 🐆.path
    🐆.listing = 🐆.retval                # keep it before the next step overwrites
    echo "done"                          # this would otherwise be the value
    🐆.retval = 🐆.listing
```

Because each step overwrites `🐆.retval`, an explicit assignment only sticks if no later step runs after it.

Return values are always strings. A function whose body never runs a step and never assigns `🐆.retval` returns the empty string. Statement calls (not assigned) silently discard the value.

### Function pipe

Functions can also be applied postfix using the pipe operator:

```
🐆.full-path = "input.json" | 🐭.make-full-path(style="linux) | 🐭.drop-config-dir-part
```

This requires that exactly one parameter is left unbound.

---

## 7. Local Functions

A function can define local functions scoped to `🐆`. These are structurally identical to `🐭` functions but are only accessible within the enclosing function.

```
help(who="me"):
    🐆.dump(who):
        echo "Hello 🐆.who! Tracing is: 🐭.tracing"

    🐆.retval = 🐆.dump(who=🐆.who)
```

Here `🐆.dump` returns the output of its `echo` — the same return-value rule as any other function — and the caller assigns it to its own `🐆.retval` to return it onwards.

Local functions have their own fresh `🐆` namespace — variables set inside do not leak to the parent. This includes `🐆.retval` and `🐆.stdout`: a local function's steps overwrite its own, not the caller's. Parameters are passed explicitly. Local functions support the same body forms as regular functions: shell lines, assignments, shebang blocks, and nested local functions.

### Suppress console output

In the above example, `jazzoo` will print the echo statement itself to the console so the caller can see what is being executed.
This can be suppressed using `@echo "Hello 🐆.who! Tracing is: 🐭.tracing"`.

---

## 8. Shebang Blocks

A function or local function body can use a shebang block to run an alternative interpreter:

```
help:
    #!/usr/bin/env python3
    print("Tracing is: 🐭.tracing, fyi")
    return "done"

    #!
    echo "Last return value was 🐆.retval"

test:
    🐆.result = 🐭.help()  # will contain "done"
```

### Bare #!

A bare shebang means that the previous shebang block ended and that we return to the default "jazzoo" execution mode.

### Sweeping

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

### Return values

Jazzoo is a shell tool, and shell tools communicate through stdout. A shebang block has no separate return channel: **whatever the block writes to stdout is its value**, exactly as it would be if you ran the same program on the command line and captured its output. There is no `return` statement and no marker line.

```
read-config():
    #!/usr/bin/env bash
    echo "/etc/jazzoo.conf"

test():
    🐆.config = 🐭.read-config()          # "/etc/jazzoo.conf"
```

This holds for every interpreter — a Python block returns what it `print`s, a bash block returns what it `echo`s:

```
read-config():
    #!/usr/bin/env python3
    print("/etc/jazzoo.conf")
```

The consequence is that stdout is both the value channel and the human-visible output channel. A line written for the reader's benefit becomes part of the value if the call is assigned:

```
debug(name="me"):
    #!/usr/bin/env bash
    echo "Running debug for: 🐆.name"     # this is the value too
```

For output that should *not* end up in the value, write to stderr — jazzoo never captures it:

```
    echo "still working..." >&2
```

Note that `@` (see section 7) suppresses the echo of the *command itself*, not its output; it has no effect on the value.

Statement calls discard the value (see section 6), so this only matters for calls whose result is assigned or piped.

If a shebang block exits with a non-zero exit code then jazzoo treats it as an error (it prints the error and exits).

### `🐆.retval` and `🐆.stdout`

Both hold the output of the last thing that ran, and differ only in trailing-newline handling:

| Variable     | Value                                                          |
| ------------ | -------------------------------------------------------------- |
| `🐆.stdout`  | The raw stdout, byte for byte                                  |
| `🐆.retval`  | The same, with a single trailing newline removed if one is present |

`🐆.retval` is what a call evaluates to, so it is the one you get from `🐆.x = 🐭.f()`. Stripping one trailing newline matches shell `$(...)`, and means the common `echo "value"` yields `"value"` rather than `"value\n"`. Only one newline is removed — a block that deliberately ends in a blank line keeps it in `🐆.retval`, and `🐆.stdout` always has everything.

They also differ in lifetime: `🐆.stdout` and `🐆.retval` are overwritten by the next step that runs, whereas a value captured by assignment is bound at the point of assignment and is unaffected by later steps.

### Stdout capture

After any shell line, shebang block, or function call completes, jazzoo sets both `🐆.stdout` and `🐆.retval` from its stdout. This makes them uniformly "the output of the last thing that ran."

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

Both are overwritten after each such step and are not set before the first one runs.

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
from ./foo.jaz export (bar, okay)                   # 🐭.bar(), 🐭.okay()
from ./foo.jaz export (bar as hello,)               # 🐭.hello()
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
