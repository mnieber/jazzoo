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

All values are strings. There are no integers.
Unquoted values are treated as bare strings: `🐆.x = hello` is equivalent to `🐆.x = "hello"`.

### Truthiness

In ternary expressions, a string value is falsy if its lowercased form is in `["0", "false", "no", ""]`. All other strings are truthy. This allows natural use of env-var-style boolean flags.

### System variables

Jazzoo provides built-in variables in the `⚙️` namespace. All of them are read-only — a `.jaz` file can never assign to `⚙️`.

These are constant for the lifetime of a run:

| Variable                  | Value                                                          |
| ------------------------- | -------------------------------------------------------------- |
| `⚙️.module.basename`      | Filename of the current module (e.g. `index.jaz`)              |
| `⚙️.module.path`          | Absolute path of the current module file                       |
| `⚙️.module.dirname`       | Absolute path of the directory containing the current module   |
| `⚙️.root_module.basename` | Filename of the entry-point `.jaz` file invoked by `jaz`       |
| `⚙️.root_module.path`     | Absolute path of the entry-point `.jaz` file                   |
| `⚙️.root_module.dirname`  | Absolute path of the directory containing the entry-point file |

These are read-only but **not** constant — jazzoo updates them as a function body runs (see section 6):

| Variable      | Value                                                        |
| ------------- | ------------------------------------------------------------ |
| `⚙️.stdout`   | Stdout of the last shebang block in the current function     |
| `⚙️.output`   | `⚙️.stdout` minus its trailing newline, if it has one        |

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

Braces without sigils in it are ignored by jazzoo.

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

Chaining is right-associative: `A if C1 else (B if C2 else C)`. Only string equality (`==`) is supported as a condition, plus bare variable truthiness testing.

### Path expressions

The `/` operator joins two string values as path segments, producing a new string:

```
🐭.config = 🐭.get_base_path() / "../config.json"
🐆.out = ⚙️.module.dirname / "build/output"
```

Path joins are a **pure string join** — `..`, symlinks, and redundant separators are left untouched. Path expressions can be chained: `a / b / c` is left-associative. Joining never canonicalizes on its own; the only way to canonicalize is to pipe to ⚙️.abs:

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

## 6. Shebang Blocks

### The default jazzoo execution mode

In the default jazzoo execution mode, every line runs in its own shell shebang block (see next section).
Therefore, this jazzoo code:

```
help:
    echo "hello"
    ls -al
```

is equivalent to

```
help:
    #!/usr/bin/env bash
    echo "hello"

    #!/usr/bin/env bash
    ls -al
```

Each line is therefore its own subprocess, and **nothing carries over from one line to the next** — not the working directory, not shell variables, not `set` options:

```
broken:
    cd /tmp          # affects only this line's subprocess
    ls               # still runs in the original directory
    FOO=bar          # sets a variable in a shell that then exits
    echo $FOO        # prints nothing

works:
    #!/usr/bin/env bash
    cd /tmp
    ls               # one subprocess, so the cd applies
```

Use an explicit shebang block whenever lines need to share state.

### The ⚙️.stdout and ⚙️.output values

The ⚙️.stdout captures what the last shebang block in the current function wrote to stdout.
The ⚙️.output value equals ⚙️.stdout minus the trailing newline (if it exists).

The value of ⚙️.stdout is not affected by calls to other jazzoo functions (it's local to that function).

### Alternative shebang blocks and bare #!

A function or local function body can use a shebang block to run an alternative interpreter.
A bare shebang means that the previous shebang block ended and that we return to the default "jazzoo" execution mode.

```
help:
    #!/usr/bin/env python3
    print("Tracing is: 🐭.tracing, fyi")

    #!
    echo "We just wrote ⚙️.stdout"
    echo "Test"
    echo "Last message was: ⚙️.output"

test:
    🐭.help()  # The last echo will write "Last message was: Test"
```

### Sweeping

Before execution, jazzoo sweeps the shebang block top to bottom, processing each line in order:

1. Trim the line. If it matches `<sigil>.<name> = <expression>` (a Jazzoo assignment), evaluate the RHS as a Jazzoo expression.
2. Otherwise, substitute all Jazzoo references in the line using the current namespace state.

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

## 7. Functions

### Basic function

```
debug(name="me"):
    🐆.dry-run = "--dry-run" if 🐐.log-level == "high" else ""
    echo "Running test with log level: 🐐.log-level for user: 🐆.name"
    docker compose up --log-level=🐐.log-level 🐆.dry-run
```

### Return values

The return value is represented by 🐆.retval. As long as a function has not assigned it, it has no value of its own and falls back to ⚙️.output — so by default a function returns the output of its last shebang block.

Assigning 🐆.retval gives it a value, and the fallback no longer applies: from that point on it holds what was assigned, and later blocks no longer change it.

```
debug(name="me"):
    echo "Test 🐆.name"

doit():
    echo "123"             # 🐆.retval changes to "123"
    🐭.test()              # 🐆.retval is still "123"
    🐆.retval = 🐭.test()  # 🐆.retval changes to "Test me"
    echo "123"             # 🐆.retval stays at "Test me"
```

Note that the last line would have changed 🐆.retval if the assignment above it had not run. Whether a shebang block affects the return value depends on whether the body has assigned 🐆.retval yet.

### Parameters

A function declares *parameters*; a caller supplies *arguments* for them. A parameter may have a default value or be required (no default). Arguments are always named:

```
build(target, mode="release"):
    cargo build --target=🐆.target --profile=🐆.mode

test():
    🐭.build(target="dev")   # correct
    🐭.build("dev")          # raises an error, arguments are always named
```

### Currying

Square brackets are used to create a curried function:

```
🐭.build_in_dev = 🐭.build[mode="dev"]
```

You can think of this as creating a new function in which the `mode` parameter is bound to "dev". The caller may no longer supply an argument for `mode`.
The function symbol itself is equivalent to applying empty square brackets to that function (which means that no parameters are bound):

```
🐭.foo = 🐭.build[]   # okay
🐭.foo = 🐭.build     # okay, same as above
🐭.foo = 🐭.build()   # error, because we're trying to execute `build` without passing any arguments
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

Calls to imported modules use the module alias:

```
    🐭.docker.build(target="myapp")
```

All function calls block until completion.

### Function pipe

Functions can also be applied postfix using the pipe operator:

```
🐆.full-path = "input.json" | 🐭.make-full-path[style="linux"] | 🐭.drop-config-dir-part | 🐭.clean_up[name, max_length=3]
```

This requires that exactly one parameter is left unbound for each function in the pipe.

---

## 8. Local Functions

A function can define local functions scoped to `🐆`. These are structurally identical to `🐭` functions but are only accessible within the enclosing function.

```
help(who="me"):
    🐆.dump(who):
        echo "Hello 🐆.who! Tracing is: 🐭.tracing"

    🐆.retval = 🐆.dump(who=🐆.who)
```

Local functions have their own fresh `🐆` namespace — variables set inside do not leak to the parent. Arguments are passed explicitly. Local functions support the same body forms as regular functions: shell lines, assignments, shebang blocks, and nested local functions.

They declare parameters and are called with named arguments exactly like `🐭` functions.

### Suppress console output

In the above example, `jazzoo` will print the echo statement itself to the console so the caller can see what is being executed.
This can be suppressed using `@echo "Hello 🐆.who! Tracing is: 🐭.tracing"`.

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

As a convenience, an argument for the first declared parameter of a target may be passed positionally at the CLI:

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
- **`Function`** is a `Scope` and can contain local functions, but not sub-modules.
- **Parameters** are the static call signature. At call time, jazzoo validates the caller's arguments against `parameters`, then populates `variables` with the resolved values. The function body only ever reads from `variables`.
- **Targets** are functions with `is_target = True` — i.e. all functions not marked `[private]`. Only targets are callable from the CLI and visible in `jaz --list`.

---

## 13. Open Questions

- **`set shell`**: Should jazzoo support configuring the default shell (e.g. bash vs sh vs fish)? Currently unspecified.
- **Circular imports**: Circular imports are allowed. Modules are cached by resolved file path after first load; a circular import receives the cached partially-initialized module. Circular references used only at call time (mid-body function calls) are safe. Circular references at load time — module-level variable assignments that call into a module not yet fully initialized — are a runtime error. This is the same model as TypeScript (live bindings resolved at access time), which is more predictable than Python's approach (copied values resolved at import time, where failures depend on statement order).
