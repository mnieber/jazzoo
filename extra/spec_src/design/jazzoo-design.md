# The Jazzoo Language Specification

Jazzoo is a task runner in the spirit of `just`. A Jazzoo file defines **functions**
whose bodies run shell commands and scripts; functions that are not private are
**targets** that can be invoked from the command line. Jazzoo adds three scoped
variable namespaces, JSON values, expressions, currying and pipes, and a module
system with explicit imports and exports.

The command is `jazzoo`, abbreviated `jaz`. The name may also be written 🐐🐭🐆, after
the three namespace sigils.

---

## How do I…

| Goal                                                     | Section                                                                       |
| -------------------------------------------------------- | ----------------------------------------------------------------------------- |
| write a first task and run it                            | [1](#1-files-and-invocation), [8](#8-functions)                               |
| use a variable in a shell command                        | [5](#5-references-and-substitution)                                           |
| choose between a global, per-file or local variable      | [3](#3-namespaces-and-scope)                                                  |
| read an environment variable, with a fallback            | [5.4](#54-optional-references-and-defaults), [7.2](#72-environment-variables) |
| load a `.env` file                                       | [7.3](#73-loading-a-dotenv-file)                                              |
| load YAML config files                                   | [7.4](#74-loading-config-files)                                               |
| read config values from a Python script                  | [13](#13-config-files)                                                        |
| compute a value conditionally                            | [6.3](#63-conditional-expressions)                                            |
| capture the output of a command or function              | [9.4](#94-stdout-output-and-return-values)                                    |
| work with JSON                                           | [4.4](#44-structured-values), [7.5](#75-pipe-operators)                       |
| build and manipulate file paths                          | [6.5](#65-path-joins), [7.5](#75-pipe-operators)                              |
| run several lines in one shell, or run Python            | [9.2](#92-shebang-blocks)                                                     |
| show a command's output live, or prompt the user         | [9.7](#97-interactive-functions)                                              |
| run commands from a Python script                        | [14](#14-running-commands)                                                    |
| hide a command's echo, or silence a function             | [9.6](#96-console-output)                                                     |
| make a task depend on another                            | [8.5](#85-dependencies)                                                       |
| pre-fill some arguments of a function                    | [8.8](#88-currying)                                                           |
| chain functions together                                 | [8.9](#89-function-pipes)                                                     |
| pass untrusted input to the shell safely                 | [5.5](#55-substitution-safety)                                                |
| split tasks across files                                 | [10](#10-modules)                                                             |
| group targets as `jaz fe.build`                          | [10.4](#104-exports)                                                          |
| find out what targets exist and what arguments they take | [11.2](#112-listing-targets)                                                  |
| understand an error message                              | [12](#12-errors)                                                              |

---

## 1. Files and Invocation

### 1.1 Source files

Jazzoo source files use the extension `.jaz`. When `jaz` is run without `--file`, it
loads `jazzoo` (no extension) from the current directory, or `jazzoo.jaz` if `jazzoo`
does not exist. The file that `jaz` loads is the **root module**.

### 1.2 A minimal example

```
🐐.log-level = "high"

debug(name="me"):
    🐆.dry-run = "--dry-run" if 🐐.log-level == "high" else ""
    echo "Running test with log level: 🐐.log-level for user: 🐆.name"
    docker compose up --log-level=🐐.log-level 🐆.dry-run
```

```
$ jaz debug name=jane
```

The full command-line interface is described in section 11.

### 1.3 Processing model

A Jazzoo file is processed in two phases:

1. **Parse.** The whole file is parsed when it is loaded: declarations, function
   definitions, attributes, dependencies, imports, assignments and expressions,
   including expressions inside `{{ }}`. Shell lines and shebang block bodies are
   opaque text to the parser. Every error that can be detected from the parse tree is
   raised in this phase (section 12.2).
2. **Substitute and run.** Immediately before each shell line or shebang block runs,
   Jazzoo substitutes the references in it against the current variable state
   (section 5) and executes the result.

Because substitution is textual and the parser never inspects command text, Jazzoo
does not know the syntactic context a value lands in and never escapes substituted
values (section 5.5).

---

## 2. Lexical Structure

### 2.1 Sigils

Every Jazzoo name begins with a sigil that selects its namespace:

| Sigil | Name    | Namespace           |
| ----- | ------- | ------------------- |
| 🐐    | Goat    | global              |
| 🐭    | Mouse   | module              |
| 🐆    | Leopard | local               |
| ⚙️    | System  | built-in, read-only |

Namespaces are defined in section 3.

### 2.2 Names and paths

A reference is a sigil followed by one or more dot-separated segments:
`🐭.tracing`, `🐆.config.name`, `🐭.docker.build`, `🐆.hosts.0`.

- A segment begins with a letter, digit or underscore, and may contain `-`. So
  `--log-level=🐐.log-level` is a valid line in which the option name and the
  variable name are identical.
- A dot continues a reference only when the next character can begin a segment
  (letter, digit or underscore). Any other character after a dot is ordinary text.
- A reference ends at the first character that cannot continue it.

```
echo "Hello 🐆.name."              # "Hello jane."
echo "Hello 🐆.name. Welcome"      # "Hello jane. Welcome"
echo "🐆.dir./config"              # the value, then "./config"
echo 🐭.tracing/com                # the value, then "/com"
```

### 2.3 Escapes

A `\` before a sigil suppresses substitution of that reference; the sigil and name
are output literally:

```
echo "Running test with \🐭.tracing set to: 🐭.tracing"
```

A `\` after a reference terminates it. This is **required** before a literal dot that
is followed by a segment character, since that dot would otherwise be read as a field
lookup (section 4.4), and before a `?` or `:-` that is meant literally (section 5.4):

```
🐭.tracing\.com              # the value of 🐭.tracing, then ".com"
🐭.tracing.com               # the `com` field of 🐭.tracing
echo ⚙️.env.HOST\?:-literal  # the value of HOST, then "?:-literal"
```

### 2.4 Literals

In expression position (section 6), values are written as JSON:

- strings are double-quoted: `"jane"`
- `true`, `false`, `null`
- numbers: `8080`, `1.5`
- arrays and objects: `["a", "b"]`, `{"name": "jane"}`

**A string in an expression must be quoted.** An unquoted word that is not a JSON
literal is a `ParseError`:

```
🐆.flag = true       # the boolean true
🐆.flag = "true"     # the string "true"
🐆.name = "jane"     # a string
🐆.name = jane       # ParseError: strings must be quoted
```

Two positions have no expression grammar and accept bare words as strings:

- defaults in references: `⚙️.env.LOG_LEVEL?:-info` (section 5.4)
- command-line arguments: `jaz build myapp` (section 11.3)

### 2.5 Comments

In jazzoo-mode lines (section 9.1), a line whose first non-whitespace character is `#`
is a comment, except a line beginning with `#!`, which is a shebang (section 9.2).

```
build():
    # fetch the sources first
    git clone 🐆.url
```

Comments are discarded at parse time. Consequently a comment:

- is not substituted, so a reference inside it is plain text and never an error;
- is not echoed to the console;
- is not a block, so it does not change `⚙️.stdout`.

Only whole lines are comments. A `#` after other text belongs to the line:

```
grep '#define' 🐆.header      # this entire line, comment included, goes to the shell
```

Inside a shebang block, `#` lines belong to the block's interpreter and are passed
through unchanged, so interpreter comments and pragmas such as `# noqa` survive.

---

## 3. Namespaces and Scope

### 3.1 The three user namespaces

| Namespace   | Visible in                       | Lifetime        |
| ----------- | -------------------------------- | --------------- |
| `🐐` global | every module                     | the whole run   |
| `🐭` module | the module that defines the name | the whole run   |
| `🐆` local  | one function invocation          | that invocation |

- **`🐐`** names are shared by all modules.
- **`🐭`** names belong to the file that defines them. Code always resolves `🐭`
  against the module in which it is _written_: when module A calls a function defined
  in module B, `🐭` inside that function refers to B's module scope.
- **`🐆`** names belong to a single function invocation. Each call, including each call
  of a local function, gets a fresh `🐆` namespace. Local variables do not leak to the
  caller.

`🐭` and `🐆` also hold functions (sections 8 and 8.10), and `🐭` holds import
namespaces (section 10.2).

### 3.2 The system namespace

`⚙️` holds built-in values and operators (section 7). It is read-only: a `.jaz` file
can never assign to `⚙️`.

### 3.3 Name uniqueness

Within one scope, a variable, a function and an import namespace may not share a
name, in any order. A reference such as `🐭.foo` names only a sigil and a name, so it
must have exactly one meaning. A violation is a `ParseError` attributed to whichever
declaration comes second in the file.

```
🐭.foo = "bar"

foo():              # ParseError: `foo` is already defined in this scope
    echo "hello"
```

```
build(target, mode="release"):
    cargo build --target=🐆.target --profile=🐆.mode

🐭.build = 🐭.build[mode="dev"]   # ParseError: `build` is already defined
```

```
from ./docker.jaz import build as docker

🐭.docker = "x"           # ParseError: `docker` is already a namespace
🐭.docker.port = "8080"   # ParseError: the first segment collides
```

Because of this rule, the first segment of a dotted `🐭` name — field path or
namespace call — can be resolved from the file alone.

The rule is subject to the following:

- **Reassignment is not redeclaration.** `🐭.cfg = "x"` followed by
  `🐭.cfg.name = "y"` is a reassignment; only the first mention declares `cfg`.
- **It applies per scope.** A local `🐆.foo` may coexist with a module-level `🐭.foo`.
  Names inside an import namespace form their own scope, so `🐭.docker.build` does not
  collide with a module-level `🐭.build`.
- **The same function bound twice is one name.** A function that reaches a module
  along several import or export paths is declared once, provided every binding traces
  back to the same definition (section 10.5).
- **Export layers are exempt.** A layer is not part of any scope a `.jaz` file can
  name, so it may share its name with an import namespace, variable or function
  (section 10.6).

---

## 4. Values

### 4.1 Types

A variable holds a JSON value: a string, number, boolean, `null`, array or object.

Jazzoo performs no arithmetic. There is no `+`, and `==` compares rendered strings
(section 4.3). Numbers exist so that JSON documents round-trip unchanged.

Only `🐐`, `🐭` and `🐆` hold structured values. `⚙️.env` values are always strings.

### 4.2 Declaring and assigning variables

An assignment has the form `<sigil>.<path> = <expression>`.

`🐐` and `🐭` variables may be assigned at the top level of a module, where the
assignment runs when the module is loaded, or from any function body:

```
🐐.log-level = "high"
🐭.tracing = true
```

`🐆` variables are assigned in function bodies and exist for the remainder of the
invocation.

### 4.3 Rendering

Whenever a value is substituted into text (section 5) it is rendered as a string:

| Value         | Rendering                    |
| ------------- | ---------------------------- |
| string        | the string itself, unquoted  |
| number        | its JSON form: `8080`, `1.5` |
| boolean       | `true` / `false`             |
| `null`        | the empty string             |
| array, object | compact JSON with no spaces  |

```
🐆.config.name = "jane"
🐆.config.port = 8080

echo 🐆.config.name    # jane
echo 🐆.config.port    # 8080
echo 🐆.config         # {"name":"jane","port":8080}
```

The rendering of a container is inserted as raw text, braces and quotes included, and
is not escaped (section 5.5). To obtain valid JSON for any value, including a quoted
string, use `⚙️.json` (section 7.5).

### 4.4 Structured values

A dotted path reaches into objects and, by index, into arrays:

```
🐆.config.name = "jane"
🐆.config.port = 8080
🐆.retval = 🐆.config.name        # "jane"

🐆.hosts = ["a.example.com", "b.example.com"]
🐆.first = 🐆.hosts.0
```

- Assigning to a path creates any missing intermediate objects, so the first two lines
  above build `{"name": "jane", "port": 8080}` without declaring `🐆.config`.
- Assigning to a path beneath a value that is not an object replaces that value.
- Reading a path that does not exist is a `ResolutionError`, unless the reference is
  marked with `?` (section 5.4):

```
🐆.maybe = 🐆.config.nickname?          # "" when absent
🐆.level = 🐆.config.log-level?:-info   # "info" when absent or empty
```

Structure enters Jazzoo from outside only through `⚙️.parse`. A command's output is
text until it is parsed (section 7.5).

### 4.5 Truthiness

Conditions (section 6.3) and the boolean operators (section 6.4) test truthiness. A
value is **falsy** if it is:

- `false` or `null`
- an empty array or empty object
- the number `0`
- a string whose lowercase form is `"0"`, `"false"`, `"no"` or `""`

Every other value is **truthy**. The string rule lets environment-style flags
(`CI=false`, `DEBUG=0`) work naturally.

Truthiness is decided on the value, not its rendering: `[]` is falsy although it
renders as the non-empty text `[]`.

### 4.6 Truthiness, `⚙️.bool` and `⚙️.empty`

Jazzoo offers three ways to ask about a value:

- **Truthiness** — used by conditions. Does the value mean _yes_?
- **`⚙️.bool`** — yields the truthiness decision as a real boolean that can be stored,
  passed or rendered. It accepts every value and never raises.
- **`⚙️.empty`** — yields `true` for `""`, `[]`, `{}` and `null`, otherwise `false`.
  Did anything come back at all?

| Value                    | Truthy? | `⚙️.bool` | `⚙️.empty` |
| ------------------------ | ------- | --------- | ---------- |
| `""`                     | no      | `false`   | `true`     |
| `null`                   | no      | `false`   | `true`     |
| `[]`, `{}`               | no      | `false`   | `true`     |
| `"no"`, `"false"`, `"0"` | no      | `false`   | `false`    |
| `0`                      | no      | `false`   | `false`    |
| `"yes"`, `"hello"`       | yes     | `true`    | `false`    |
| `["a"]`                  | yes     | `true`    | `false`    |

Use truthiness or `⚙️.bool` to read a flag; use `⚙️.empty` to ask whether a command
produced output. `⚙️.empty` is not the negation of `⚙️.bool`: a command that printed
`no` produced output.

```
🐆.ci = ⚙️.env.CI? | ⚙️.bool               # true / false, whatever spelling CI used
🐭.report(enabled=🐆.ci)

🐆.result = 🐭.check-status()
🐆.nothing-came-back = 🐆.result | ⚙️.empty
```

To require a genuine JSON boolean rather than an interpreted string, obtain it through
`⚙️.parse`.

---

## 5. References and Substitution

Substitution is how Jazzoo values reach commands. It applies to jazzoo-mode lines and
to shebang block bodies (section 9).

### 5.1 Bare references

A reference may appear directly in a line, without quoting or delimiters:

```
echo "Running test with log level: 🐐.log-level for user: 🐆.name"
docker compose up --log-level=🐐.log-level 🐆.dry-run
```

Where a reference ends is defined in section 2.2.

### 5.2 Braced expressions

`{{ <expression> }}` evaluates an expression (section 6) and substitutes its rendered
value. Use braces when a reference touches surrounding text, or to compute a value
inline:

```
echo "Running test with log level: {{ 🐐.log-level }}-setting"
echo "shell: {{ 🐆.cmd if 🐆.cmd else "bash" }}"
echo "fallback: {{ 🐆.cmd or "sh" }}"
echo "file: {{ 🐆.path | ⚙️.basename }}"
```

- Braces containing no sigil are left untouched.
- The quotes of a string literal inside braces belong to Jazzoo and are removed before
  the interpreter sees the line.
- Braced expressions are parsed when the file is loaded, so a malformed one such as
  `{{ 🐆.cmd if 🐆.cmd }}` is a `ParseError`.

### 5.3 Calls in substitution

A function call may be substituted inline; it is quiet (section 9.6):

```
echo "ip: 🐭.host-ip()"
```

### 5.4 Optional references and defaults

By default every reference must resolve; an unset variable, missing field or unset
environment variable is a `ResolutionError`. Two markers relax this, and apply equally
to `🐐`, `🐭`, `🐆` and `⚙️.env`:

- `?` — the reference **may be absent**; it then resolves to the empty string.
- `:-<default>` — the default is used when the value is **empty**.

| Syntax         | If absent         | If empty     |
| -------------- | ----------------- | ------------ |
| `⚙️.env.X`     | `ResolutionError` | empty string |
| `⚙️.env.X?`    | empty string      | empty string |
| `⚙️.env.X:-y`  | `ResolutionError` | `y`          |
| `⚙️.env.X?:-y` | `y`               | `y`          |

```
🐆.ci-flag = "--ci" if ⚙️.env.CI? else ""
echo {{ ⚙️.env.LOG_LEVEL?:-info }}-setting
```

A default is either a bare word, which ends at the first whitespace, or a quoted
string:

```
⚙️.env.GREETING?:-hello
⚙️.env.GREETING?:-"hello there"
```

The markers work in bare and braced positions. A `\` before them makes them literal
text (section 2.3).

> Rationale: `:-` is used rather than `:` because colons routinely follow references
> in shell lines (`⚙️.env.HOST:8080`, `-v ⚙️.env.HOME:/data`).

### 5.5 Substitution safety

Substitution inserts the rendered value as text. **Jazzoo does not quote or escape
it**, so a value containing interpreter syntax becomes interpreter syntax:

```
🐆.name = "; rm -rf ~ #"
echo "Hello 🐆.name"          # the shell sees a second command
```

This is the same exposure as in `just`, `make`, or an unquoted `$VAR` in a shell
script. Jazzoo cannot escape on the user's behalf, because the same mechanism
substitutes into shell words, Python source, JSON and arbitrary other interpreters,
each with different rules.

Values written in the `.jaz` file are as trusted as the file itself. Treat values from
these sources as **untrusted** and escape them for their destination:

- `⚙️.stdout` and `⚙️.output` — whatever the last block printed
- `⚙️.env.*` — environment variables, especially in CI
- command-line arguments

For shell destinations, use `⚙️.sh-quote`, which renders any value as exactly one
POSIX shell word by wrapping it in single quotes and escaping embedded single quotes
(equivalent to Python's `shlex.quote`):

```
list-branch(name):
    🐆.safe-name = 🐆.name | ⚙️.sh-quote
    git log 🐆.safe-name
```

`⚙️.sh-quote` is a Jazzoo pipe evaluated before the line runs, not a shell pipeline.
Its output is correct only for POSIX shells; in Python, JSON or other languages it
yields a literal `'…'` string.

Container renderings (section 4.3) are especially exposed, because their quotes and
braces are live shell syntax.

---

## 6. Expressions

Expressions appear on the right-hand side of assignments, inside `{{ }}`, as argument
and default values, and as curry bindings.

### 6.1 Operands

An operand is one of:

- a literal (section 2.4)
- a reference, optionally with `?` and `:-` (sections 2.2, 5.4)
- a function call: `🐭.build(target="dev")` (section 8.6)
- a curried function: `🐭.build[mode="dev"]` (section 8.8)
- a parenthesised expression

### 6.2 Precedence

From loosest to tightest binding:

| Level | Operator                     | Associativity |
| ----- | ---------------------------- | ------------- |
| 1     | `… if … else …`              | right         |
| 2     | `or`                         | left          |
| 3     | `and`                        | left          |
| 4     | `not`                        | prefix        |
| 5     | `==`                         | —             |
| 6     | `\|` (pipe), `/` (path join) | left          |
| 7     | call `()`, curry `[]`        | postfix       |

So `a or b and not c` reads as `a or (b and (not c))`. Pipe and path join share a
level and apply left to right, so `a / b | ⚙️.abs` reads as `(a / b) | ⚙️.abs`, and
`a | ⚙️.abs / b` reads as `(a | ⚙️.abs) / b`. Parentheses override precedence.

### 6.3 Conditional expressions

`A if C else B` yields `A` when `C` is truthy and `B` otherwise. Conditionals chain
to the right:

```
🐆.x = "a" if 🐐.log-level == "high" else "b" if 🐐.log-level == "low" else ""
# parsed as: "a" if … else ("b" if … else "")
```

`==` compares the rendered strings of its operands.

### 6.4 Boolean operators

`and`, `or` and `not` combine operands by truthiness:

```
🐆.doit = "yes" if 🐆.foo or (🐆.bar and not 🐭.test) else "no"
```

- `A or B` yields `A` if `A` is truthy, otherwise `B`.
- `A and B` yields `A` if `A` is falsy, otherwise `B`.
- `not A` yields the boolean `true` or `false`.

Because `or` yields an operand, it serves as a fallback:

```
🐆.name = 🐆.given or "anonymous"
```

`and` and `or` **short-circuit**: the right operand is not evaluated — not called,
not resolved — when the left operand decides the result. An unresolvable reference on
the skipped side raises nothing.

```
🐆.ok = 🐭.cheap-check() or 🐭.expensive-check()
```

**Functions as operands.** When the operands are functions, the result is a function
and may be called or piped into:

```
🐆.out = (🐭.fast or 🐭.slow)(input="x")
🐆.out = "x" | (🐭.fast or 🐭.slow)
```

Which operand wins is known only at run time, so a call through such a value is
checked at load time against **every** function it could yield, and must be valid
for all of them. Calling it is a `ParseError` if any branch is not a function. Such a
value may still be assigned, rendered and passed around without being called:

```
🐆.thing = 🐭.some-string or 🐭.runner   # allowed
🐆.thing(x="1")                          # ParseError: 🐭.some-string is not a function
```

### 6.5 Path joins

`A / B` joins two values as path segments, yielding a string:

```
🐭.config = 🐭.get_base_path() / "../config.json"
🐆.out = ⚙️.module.dirname / "build/output"
```

The join is purely textual: `..`, symlinks and redundant separators are kept. To
canonicalize, pipe to `⚙️.abs`:

```
🐭.config = 🐭.get_base_path() / "../config.json" | ⚙️.abs   # resolve the whole join
🐭.config = 🐭.get_base_path() | ⚙️.abs / "../config.json"   # resolve the prefix only
```

### 6.6 Pipes

`V | F` passes the value `V` to the function or operator `F` and yields its result.
`F` may be a built-in pipe operator (section 7.5) or a user function prepared for
piping (section 8.9). Pipes chain left to right.

---

## 7. Built-ins

### 7.1 System variables

All `⚙️` variables are read-only.

Constant for the run:

| Variable                  | Value                                            |
| ------------------------- | ------------------------------------------------ |
| `⚙️.module.basename`      | filename of the current module, e.g. `index.jaz` |
| `⚙️.module.path`          | absolute path of the current module              |
| `⚙️.module.dirname`       | absolute path of the current module's directory  |
| `⚙️.root_module.basename` | filename of the root module                      |
| `⚙️.root_module.path`     | absolute path of the root module                 |
| `⚙️.root_module.dirname`  | absolute path of the root module's directory     |

Updated as a function body runs (section 9.4):

| Variable    | Value                                                |
| ----------- | ---------------------------------------------------- |
| `⚙️.stdout` | stdout of the last block run in the current function |
| `⚙️.output` | `⚙️.stdout` without its trailing newline, if any     |

### 7.2 Environment variables

`⚙️.env.NAME` reads the environment variable `NAME`. Upper case is conventional, not
required. Environment variables can only be read by name; there is no way to
enumerate them.

An unset environment variable is a `ResolutionError` unless the reference is marked
with `?` (section 5.4). Values are always strings.

### 7.3 Loading a dotenv file

```
⚙️.load_env(path=⚙️.module.dirname / ".local.env")
⚙️.load_env(path=⚙️.module.dirname / "secrets.env", required=false)
```

`⚙️.load_env` reads a dotenv file and exports its variables into the process
environment. Afterwards they are visible through `⚙️.env` and inherited by every
subsequent subprocess as ordinary `$VAR`s.

- It is a statement and yields no value.
- At the top level of a module it runs when the module is loaded; in a function body
  it takes effect from that line on.
- The file contains `KEY=VALUE` lines. Blank lines and lines starting with `#` are
  ignored. Surrounding single or double quotes are removed from values.
- A variable **already set** in the environment keeps its value; the file only fills
  in missing ones. A caller can therefore override the file for one run:
  `BLOGS_SHELL_COMMAND=bash jaz shell`. (This matches `just` and Docker Compose.)
- By default a missing file is an `ExecutionError`, so a misspelled path is caught.
  With `required=false`, a missing file is silently skipped — suitable for optional
  per-developer overrides.

`⚙️.load_env` and `⚙️.load_config` (section 7.4) are the only built-ins with a side
effect. They change the process environment; they do not make `⚙️` assignable.

### 7.4 Loading config files

```
⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")
⚙️.load_config(path=⚙️.module.dirname / "config/local.yaml", required=false)
```

`⚙️.load_config` appends a YAML file to the **config list**. Jazzoo itself never reads
the config; a script that the file runs reads values from the merged config with
`get_config` (section 13).

- It is a statement and yields no value, like `⚙️.load_env`.
- At the top level of a module it runs when the module is loaded; in a function body
  it takes effect from that line on.
- A relative path is resolved against the current working directory, like the path
  of `⚙️.load_env`, and is stored as an absolute path, so a script that changes
  directory still finds the file. To anchor a path to a module, use
  `⚙️.module.dirname` or `⚙️.root_module.dirname`.
- Adding a path that is already in the list does nothing; the path keeps its
  original position.
- By default a missing file is an `ExecutionError`. With `required=false`, a missing
  file is silently skipped and not added to the list.
- It only checks that the file exists. The YAML is parsed by `get_config`, so loading
  config does not slow down every `jaz` run.
- The config list is exported to subprocesses in the environment variable
  `JAZZOO_CONFIG_FILES`, as absolute paths separated by `os.pathsep`. A subprocess
  sees the list as it was when the subprocess started.
- If `JAZZOO_CONFIG_FILES` is already set when `jaz` starts, its paths form the start
  of the list. A nested `jaz` call therefore inherits the config of its caller.

There is no way to select config files from inside a config file. The Jazzoo file is
the one place that decides which files are loaded; a conditional expression or path
join in `path=` covers the conditional case.

### 7.5 Pipe operators

| Operator      | Yields                                                        |
| ------------- | ------------------------------------------------------------- |
| `⚙️.abs`      | the canonical absolute path                                   |
| `⚙️.basename` | the final path component                                      |
| `⚙️.dirname`  | the path without its final component                          |
| `⚙️.ext`      | the extension                                                 |
| `⚙️.stem`     | the path without its extension                                |
| `⚙️.sh-quote` | the value as one safely quoted POSIX shell word (section 5.5) |
| `⚙️.parse`    | the value described by a JSON string                          |
| `⚙️.json`     | the value as JSON text; strings come back quoted              |
| `⚙️.bool`     | the value's truthiness as a boolean (section 4.6)             |
| `⚙️.empty`    | whether the value is empty (section 4.6)                      |

`⚙️.parse` raises an `ExecutionError` if its input is not valid JSON.

```
🐆.config = 🐭.load-config() | ⚙️.parse   # parse a function's output
🐆.name   = 🐆.config.name                # reach into it
🐆.text   = 🐆.config | ⚙️.json           # back to JSON text
```

---

## 8. Functions

### 8.1 Definition

```
<name>(<parameters>): <dependencies>
    <body>
```

A function is defined at the top level of a module and lives in its `🐭` namespace.
Its body is indented and consists of shell lines, assignments, calls, shebang blocks
and local function definitions (section 9).

```
debug(name="me"):
    🐆.dry-run = "--dry-run" if 🐐.log-level == "high" else ""
    echo "Running test with log level: 🐐.log-level for user: 🐆.name"
    docker compose up --log-level=🐐.log-level 🐆.dry-run
```

Every function not marked `[private]` is a **target**.

### 8.2 Parameters and arguments

A function declares parameters; a caller supplies arguments. A parameter without a
default is required. Inside the body each parameter is a `🐆` variable.

**Arguments are always named** in `.jaz` files. Positional shorthand exists only on
the command line (section 11.3).

```
build(target, mode="release"):
    cargo build --target=🐆.target --profile=🐆.mode

test():
    🐭.build(target="dev")   # correct
    🐭.build("dev")          # ArgumentError: arguments must be named
```

### 8.3 Default values

A default is an expression. It may reference `🐐`, `🐭` and `⚙️.env`:

```
🐭.default-mode = ⚙️.env.BUILD_MODE?:-release

build(target, mode=🐭.default-mode):
    cargo build --target=🐆.target --profile=🐆.mode
```

A default is evaluated **on every call** that omits the argument, in the scope of the
module that defines the function.

### 8.4 Attributes

Attributes appear on the lines before the function, one per line:

```
[private]
_helper(name):
    echo "Internal helper: 🐆.name"
```

| Attribute       | Effect                                                                             |
| --------------- | ---------------------------------------------------------------------------------- |
| `[private]`     | not a target: hidden from `jaz --list` and the CLI, but callable from `.jaz` files |
| `[interactive]` | its blocks are not captured, but use the terminal directly (section 9.7)           |

Several attributes may precede one function (`[private]` and `[interactive]`), in any
order. An unknown attribute is a `ParseError`. Local functions may have attributes too
(section 8.10).

### 8.5 Dependencies

Dependencies follow the colon and run, in order, before the body. Use `\` to continue
the list over several lines:

```
debug(name="me"): _helper(name=🐆.name)
    echo "Running debug for: 🐆.name"

foo(name="me"): \
        _helper(name=🐆.name) \
        _helper(name=🐭.bar)
    echo "Running debug for: 🐆.name"
```

Dependency arguments may reference `🐐`, `🐭` and the function's parameters, but not
`🐆` variables assigned in the body, which do not yet exist. Dependencies are resolved
in the module that defines the function (section 10.3).

### 8.6 Calls

A function is called with its sigil and named arguments, and blocks until it
completes:

```
debug(name="me"):
    🐭._helper(name="anonymous")
    🐭.docker.build(target="myapp")     # a function in an import namespace
    echo "Done"
```

A call yields the function's return value (section 9.4). A call used as a statement
prints its commands and output; a call whose value is used is quiet (section 9.6).

### 8.7 Functions as values

A function name without parentheses is a function value, which may be assigned,
passed and called later. It is equivalent to the function with empty brackets:

```
🐭.foo = 🐭.build[]   # a function value
🐭.foo = 🐭.build     # the same
🐭.foo = 🐭.build()   # a call: ArgumentError, `target` is required
```

### 8.8 Currying

`F[<bindings>]` yields a new function with some parameters bound:

```
🐭.build_in_dev = 🐭.build[mode="dev"]
```

- **`name=<expression>` binds** a parameter. A caller of the curried function may no
  longer supply it; doing so is an `ArgumentError`. Binding a parameter the function
  does not have is an `ArgumentError`.
- **A bare `name` marks a parameter as unbound.** Every parameter neither bound nor
  named bare must have a default. This is the form used to prepare a function for a
  pipe (section 8.9):

```
🐭.clean_up_name = 🐭.clean_up[name, max_length=3]
```

Bound values are expressions and may reference any variable in scope, including the
enclosing body's `🐆` locals. They are evaluated **once, where the brackets appear**:

```
build-for(user):
    🐆.build = 🐭.build[mode=🐭.default-mode, target=🐆.user]
```

Later reassigning `🐭.default-mode` does not affect `🐆.build`, and the captured
`🐆.user` outlives the invocation that bound it. Contrast parameter defaults, which are
re-evaluated on every call (section 8.3).

### 8.9 Function pipes

A function may be applied postfix with `|`:

```
🐆.full-path = "input.json" | 🐭.make-full-path[style="linux"] | 🐭.drop-config-dir-part | 🐭.clean_up[name, max_length=3]
```

Each stage must leave **exactly one parameter unbound**. The piped value is passed as
that parameter, and the stage's return value is piped to the next stage.

A parameter is unbound if the stage does not bind it — because it is named bare in the
brackets, or because brackets are absent or empty. Defaults play no part in this
decision. A stage with zero or more than one unbound parameter is an `ArgumentError`.

For `f(path, style="posix")`:

```
🐭.f[path]                # path is free; style takes its default
🐭.f[style="posix"]       # equivalent
🐭.f                      # ArgumentError: two parameters are unbound
```

Naming the free parameter is preferred: it also states that all other parameters take
their defaults.

### 8.10 Local functions

A function body may define local functions in its `🐆` namespace. They are visible
only within the enclosing function:

```
help(who="me"):
    🐆.dump(who):
        echo "Hello 🐆.who! Tracing is: 🐭.tracing"

    🐆.retval = 🐆.dump(who=🐆.who)
```

Local functions have the same parameters, call syntax and body forms as module
functions, including nested local functions. Each call gets its own fresh `🐆`
namespace; the enclosing function's locals are not visible and must be passed as
arguments.

A local function may be marked `[interactive]` (section 9.7), which makes it easy to
run one step of a function interactively:

```
deploy():
    [interactive]
    🐆.build():
        docker compose build

    🐆.build()                         # output streams to the console
    🐆.version = 🐭.read-version()     # captured, as usual
```

In a body, a `[name]` line is an attribute only when the next non-empty line (after
any further attributes) is a local function header; anywhere else it is an ordinary
shell line. `[private]` on a local function is a `ParseError`, since a local function
is never a target.

---

## 9. Function Bodies

### 9.1 Jazzoo mode

By default a body is in **jazzoo mode**. Each line is one of:

- an assignment: `🐆.x = <expression>`
- a statement call: `🐭.helper(name="x")`, `⚙️.load_env(...)`
- a local function definition (section 8.10)
- a comment (section 2.5)
- a shebang, which starts a shebang block (section 9.2)
- a shell line

**Each shell line runs as its own shell block**, as if preceded by
`#!/usr/bin/env bash`. So:

```
help:
    echo "hello"
    ls -al
```

is equivalent to:

```
help:
    #!/usr/bin/env bash
    echo "hello"

    #!/usr/bin/env bash
    ls -al
```

**Nothing carries over between shell lines** — not the working directory, shell
variables or `set` options:

```
broken:
    cd /tmp          # affects only this line's subprocess
    ls               # runs in the original directory
    FOO=bar
    echo $FOO        # prints nothing

works:
    #!/usr/bin/env bash
    cd /tmp
    ls               # same subprocess, so the cd applies
```

Use a shebang block whenever lines must share state.

### 9.2 Shebang blocks

A `#!<interpreter>` line starts a block that runs in that interpreter as a single
subprocess. A bare `#!` ends the block and returns to jazzoo mode:

```
help:
    #!/usr/bin/env python3
    print("Tracing is: 🐭.tracing, fyi")

    #!
    echo "We just wrote ⚙️.stdout"
    echo "Test"
    echo "Last message was: ⚙️.output"
```

### 9.3 Sweeping

Before a shebang block runs, Jazzoo **sweeps** it from top to bottom. For each line:

1. If the trimmed line has the form `<sigil>.<name> = <expression>`, it is a Jazzoo
   assignment: the expression is evaluated, the variable is updated, and the line is
   removed from the block.
2. Otherwise, all references in the line are substituted using the variable state at
   that point in the sweep.

The resulting text is executed once.

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

runs this Python:

```python
import json
with open("hello.json") as f:
    cfg = json.load(f)
print(cfg)

with open("bye.json") as f:
    cfg = json.load(f)
print(cfg)
```

and then this bash:

```bash
echo "The bye.json file was used in our Python shebang block"
```

Because the line is trimmed before matching, indentation is irrelevant: a Jazzoo
assignment inside a Python `for` loop or `if` is still extracted at sweep time. Jazzoo
assignments in a block are therefore static substitutions, not runtime logic; use the
interpreter's own variables for dynamic behaviour.

A line that begins with a braced expression is not an assignment and passes through
the sweep, which lets a Jazzoo value supply an interpreter-level name:

```python
{{ 🐭.variable }} = "bar"   # e.g. foo = "bar"
```

### 9.4 Stdout, output and return values

After each block — a jazzoo-mode shell line or a shebang block — runs, `⚙️.stdout`
holds what it wrote to stdout, and `⚙️.output` holds the same without one trailing
newline. These values are local to the function: calling another function does not
change them.

A function's return value is `🐆.retval`:

- Until the body assigns `🐆.retval`, it resolves to `⚙️.output`. By default a function
  therefore returns the output of its last block.
- Once assigned, it keeps the assigned value; later blocks do not change it.

In an interactive function (section 9.7), the output of a block is not captured, so
`⚙️.stdout` and `⚙️.output` are `""` after each block.

```
debug(name="me"):
    echo "Test 🐆.name"

doit():
    echo "123"             # 🐆.retval is "123"
    🐭.debug()             # still "123": calls do not change ⚙️.output
    🐆.retval = 🐭.debug() # "Test me"
    echo "123"             # still "Test me": 🐆.retval has been assigned
```

### 9.5 Failure

If any block exits with a non-zero status, the run aborts with an `ExecutionError`
(section 12.3). Its message includes the block's stderr; in an interactive function,
where stderr is not captured, it says `command failed: <command>` instead.

### 9.6 Console output

**Echo.** A jazzoo-mode shell line is printed to the console before it runs, followed
by its output. Prefixing the line with `@` suppresses the echo but not the output:

```
build():
    echo "starting"      # prints the command, then "starting"
    @echo "starting"     # prints only "starting"
```

Shebang blocks are never echoed; only their output is shown.

**Quiet calls.** A call whose value is used is **quiet**: neither its commands nor
their stdout reach the console. A call's value is used when it is:

- the right-hand side of an assignment: `🐆.ip = 🐭.host-ip()`
- a stage in a pipe: `🐭.load-config() | ⚙️.parse`
- an operand or argument: `🐭.cheap() or 🐭.expensive()`
- substituted into a line: `echo "ip: 🐭.host-ip()"`

A quiet call behaves like `$(...)` in a shell. Quietness extends to every function the
quiet call invokes. Stderr is not suppressed, so warnings and errors remain visible.
Quietness affects only the console: `⚙️.stdout` and the return value are captured as
usual.

A call used as a statement — a dependency, a call on its own line, or a target invoked
from the CLI — is not quiet.

An interactive function (section 9.7) is the exception: its output reaches the
console even in a quiet call. Its shell lines are not echoed, as in any quiet call.

Quiet calls matter especially for module-level assignments, which run every time the
module loads, including for `jaz --list`.

### 9.7 Interactive functions

Jazzoo captures the stdout and stderr of every block, for `⚙️.stdout`, the return
value and the error message, and prints them when the block ends. That does not suit
two kinds of blocks: a long-running command whose progress messages should appear as
they come (`docker compose build`), and a command that talks to the user (a prompt, a
menu, `fish`, `vim`, `docker exec -it ...`). Such blocks never need to tell Jazzoo what
they printed, and are put in a function marked `[interactive]`:

```
[interactive]
shell():
    docker exec -it blogs_be fish

[interactive]
build():
    #!/usr/bin/env python3
    from jazzoo import run

    print("Building the images")
    run("docker compose build")
```

- The attribute applies to every block of the function: its shell lines and its
  shebang blocks. To make only part of a function interactive, split it, e.g. with a
  local function (section 8.10).
- An interactive block inherits stdin, stdout and stderr from `jaz`; nothing is
  captured. Its output appears as it is written and in the order it is written, whether
  it comes from a shell line, from a script's own `print`, or from a command that the
  script starts with `run` (section 14). When `jaz` runs in a terminal, the block sees
  a terminal, so prompts, colours, progress bars, full-screen programs and ctrl-c work
  as in a shell.
- The output goes wherever `jaz`'s own output goes, so redirection
  (`jaz build > build.log`) and CI logs work as usual.
- After an interactive block, `⚙️.stdout` and `⚙️.output` are `""`, so the function's
  default return value is `""`. An explicit `🐆.retval` still works.
- Shell lines are still echoed, and `@` still suppresses the echo: the echo is printed
  by `jaz` before the block starts, and is not part of the block's output.
- A non-zero exit code raises an `ExecutionError`, whose message says
  `command failed: <command>`; the details were already shown on the console.
- An interactive function that is called quietly still shows its output (section
  9.6). Its value is `""`.
- The attribute is not inherited: the functions that an interactive function calls run
  with their own attributes.
- To pass data back to Jazzoo, an interactive block can use the filesystem (e.g. write
  a file that a later line reads with `⚙️.parse`), or its exit code.

---

## 10. Modules

### 10.1 Overview

Every `.jaz` file is a module. A module brings in functions from another file in one
of two ways:

- **import** — private to the importing file, always under a namespace alias, callable
  as `🐭.<alias>.<function>()`.
- **export** — public: the functions become targets of the importing module, visible
  to its own importers, the CLI and `jaz --list`.

Import paths are always explicit, relative or absolute. There is no search path.

### 10.2 Imports

```
from ./foo.jaz import bar as baz                    # 🐭.baz.bar()
from ./foo.jaz import (bar, okay) as baz            # 🐭.baz.bar(), 🐭.baz.okay()
from ./foo.jaz import (bar as hello, okay) as baz   # 🐭.baz.hello(), 🐭.baz.okay()
from ./foo.jaz import * as foo                      # 🐭.foo.<each exported function>()
```

The trailing `as <alias>` is mandatory. A single symbol is placed _under_ the alias:
`import bar as baz` makes `🐭.baz.bar()`, not `🐭.baz()`.

Importing a file that does not exist, or a symbol the module does not export, is a
`ModuleImportError`.

### 10.3 Resolution across modules

Code resolves names in the module where it is written:

- an imported function's `🐭` variables refer to its own module's scope;
- its dependencies and mid-body calls are resolved in its own module, so it may call
  that module's private functions and import namespaces;
- `🐐` is shared by all modules.

An importer therefore only needs to import or export the function itself:

```
# lib.jaz
from ./helper.jaz import other as _h

[private]
_prepare():
    echo "preparing"

build(): _prepare()        # resolved in lib.jaz
    🐭._h.other()          # resolved in lib.jaz
```

```
# jazzoo
from ./lib.jaz export build   # `jaz build` works; _prepare and _h stay private
```

### 10.4 Exports

An export without a layer places the functions flat in the importing module's `🐭`
namespace and makes them targets:

```
from ./foo.jaz export bar                     # 🐭.bar()
from ./foo.jaz export (bar, okay)             # 🐭.bar(), 🐭.okay()
from ./foo.jaz export bar as hello            # 🐭.hello()
from ./foo.jaz export (bar as hello,)         # 🐭.hello()
from ./foo.jaz export (bar as hello, okay)    # 🐭.hello(), 🐭.okay()
from ./foo.jaz export *                       # everything foo.jaz exports
```

`export *` includes only what `foo.jaz` itself exports, not functions it imported
privately.

#### Export layers

An export may instead group functions under a **layer**, which appears on the CLI as a
dotted prefix:

```
from ./hello.jaz export (build_fe as build,) as fe    # jaz fe.build mode=dev
from ./hello.jaz export (build, test) as fe           # jaz fe.build, jaz fe.test
from ./hello.jaz export * as fe                       # jaz fe.<function>
```

- **Naming symbols into a layer requires the tuple form.** `export bar as fe` renames
  `bar` to `fe`; `export (bar,) as fe` places `bar` in layer `fe`. The trailing comma
  makes a one-element tuple. `export * as fe` needs no tuple.
- **Layers nest.** A layer is itself an exported symbol, so it can be re-exported,
  selected by name or renamed like a function. Each file declares only its own layer:

  ```
  from ./react.jaz export (build_react,) as react   # in fe.jaz
  from ./fe.jaz export (react,) as fe               # in the root module
  ```

  gives `jaz fe.react.build_react mode=dev`. Renaming a layer renames its path
  segment: `from ./fe.jaz export (react as r,) as fe` gives `jaz fe.r.build_react`.
  Selecting a layer brings all of its contents at every depth, and `export *` includes
  layers.

- **Layers aggregate.** Exporting into the same layer more than once merges the
  contents:

  ```
  from ./frontend.jaz export (build,) as fe
  from ./styles.jaz export (lint,) as fe      # fe now has build and lint
  ```

- A module may not export a function and a layer under the same name (`ParseError`).
- Exporting two different functions under the same name in one layer is a
  `ParseError`, attributed to the second statement.

**Layered targets are reachable from the CLI only.** To call them from a `.jaz` file,
import them as well (section 10.6).

### 10.5 The same function along several paths

A function may reach a module along more than one path, as in this diamond:

```
# env-files.jaz
compile-env-files():
    python compile_env_files.py

# build.jaz
from ./env-files.jaz export compile-env-files

build(): compile-env-files()
    docker compose build

# index.jaz
from ./build.jaz export *         # build, compile-env-files
from ./env-files.jaz export *     # compile-env-files again
```

Bindings that trace back to the **same definition** — the same function in the same
file — are one symbol, regardless of path or alias, and the repeated binding has no
effect. This applies to flat exports, export layers and import namespaces alike.

Two **different** functions bound under the same name are a `ParseError`, attributed
to the statement that binds the second:

```
from ./env-files.jaz export compile-env-files
from ./legacy.jaz export compile-env-files     # ParseError: a different function
```

### 10.6 Import namespaces and export layers are independent

An import namespace and an export layer may share a name:

```
from ./hello.jaz import (build,) as fe      # 🐭.fe.build() in this file
from ./hello.jaz export (build,) as fe      # jaz fe.build on the CLI
```

They populate separate surfaces: `.jaz` code can only name imported symbols, and the
CLI can only reach exported symbols. This is the only exception to the uniqueness rule
of section 3.3.

### 10.7 Summary

| Form                                 | Callable in `.jaz` as    | CLI / `jaz --list`      |
| ------------------------------------ | ------------------------ | ----------------------- |
| `from ./foo.jaz import bar as ns`    | `🐭.ns.bar()`            | no                      |
| `from ./foo.jaz import (a, b) as ns` | `🐭.ns.a()`, `🐭.ns.b()` | no                      |
| `from ./foo.jaz import * as ns`      | `🐭.ns.<function>()`     | no                      |
| `from ./foo.jaz export bar`          | `🐭.bar()`               | yes                     |
| `from ./foo.jaz export bar as hello` | `🐭.hello()`             | yes                     |
| `from ./foo.jaz export *`            | `🐭.<function>()`        | yes                     |
| `from ./foo.jaz export (a,) as ns`   | not callable             | yes, as `ns.a`          |
| `from ./foo.jaz export * as ns`      | not callable             | yes, as `ns.<function>` |

### 10.8 Loading and circular imports

Modules are cached by resolved file path; a file imported several times is loaded
once. Circular imports are allowed: a module that imports a module still being loaded
receives the partially initialised cached module.

- References used only at call time, such as mid-body calls, are always safe, because
  names are resolved when accessed.
- A module-level assignment that calls into a module that has not finished loading is
  a `ModuleImportError` at run time.

> Rationale: this is TypeScript's model (live bindings resolved at access time). It is
> more predictable than Python's, where values are copied at import time and failures
> depend on statement order.

---

## 11. Command Line

### 11.1 Synopsis

```
jaz                            # list targets
jaz <target> [arg=value ...]   # run a target
jaz --list [<path>]            # list targets, or describe what is at <path>
jaz --list-all                 # list every target at every depth
jaz --file <path> ...          # use <path> as the root module
jaz --trace <target>           # on error, also print the stack trace
```

A target in an export layer is named by its dotted path: `jaz fe.build`,
`jaz fe.react.build`. CLI paths resolve against exports only; a name that exists only
as an import is `no such target`.

### 11.2 Listing targets

`jaz --list` lists the root module's targets one level deep. A layer appears as a
single entry ending in `...`:

```
$ jaz --list
build
test
fe...
```

`jaz --list <path>` describes what is at the path. For a layer, it lists the layer's
members one level deep; for a target, it prints the signature:

```
$ jaz --list fe
fe.build
fe.test
fe.react...

$ jaz --list fe.build
fe.build(mode="release")
```

`jaz --list-all` lists every target at every depth:

```
$ jaz --list-all
build
test
fe.build
fe.test
fe.react.build
```

The walk records modules it has entered by resolved path and skips layers whose module
has already been entered, so it terminates under circular imports and never lists a
target twice.

### 11.3 Arguments

Arguments are passed as `name=value`. Values are bare strings (section 2.4):

```
jaz debug name=jane
```

As a convenience, the argument for a target's **first** parameter may be given
positionally:

```
jaz build myapp        # same as: jaz build target=myapp
```

A positional argument must precede named ones, and supplying the same parameter both
positionally and by name is an error. Positional arguments are not permitted in
`.jaz` files.

Command-line arguments are untrusted input (section 5.5).

### 11.4 No dry-run mode

Jazzoo has no `--dry-run`. The commands a target issues often depend on the results
of earlier commands — through `⚙️.output`, return values, or computed dependency
arguments — and cannot be predicted without running them. A dry run that guessed
would diverge from reality exactly when a script is complex enough to need checking.
Use `jaz --list` to discover what a file offers and `--trace` to debug failures.

---

## 12. Errors

### 12.1 Error classes

Every error is a `JazzooError` and is attributed to a `.jaz` file and line:

| Class               | Meaning                                            |
| ------------------- | -------------------------------------------------- |
| `ParseError`        | the file is malformed                              |
| `ResolutionError`   | an unknown variable, function, module or namespace |
| `ArgumentError`     | wrong or missing arguments at a call site          |
| `ModuleImportError` | an import that cannot be satisfied                 |
| `ExecutionError`    | a block exited non-zero, or a built-in failed      |

### 12.2 Load-time errors

Everything decidable from the parse tree is checked when a file is loaded — before
any subprocess runs, whichever target was requested, and also for `jaz --list`. A
broken call site in one target therefore prevents every target from running.

| Condition                                                             | Class               |
| --------------------------------------------------------------------- | ------------------- |
| Syntax that does not parse                                            | `ParseError`        |
| An unquoted string in an expression (`🐆.x = hello`)                  | `ParseError`        |
| A malformed expression inside `{{ }}`                                 | `ParseError`        |
| A variable, function or namespace sharing a name in one scope         | `ParseError`        |
| Two different functions bound under one name by imports or exports    | `ParseError`        |
| Two exports landing different functions under one name in one layer   | `ParseError`        |
| A module exporting both a function and a layer under one name         | `ParseError`        |
| A call through a boolean whose branches are not all functions         | `ParseError`        |
| An unknown attribute (`[interactve]`)                                 | `ParseError`        |
| `[private]` on a local function                                       | `ParseError`        |
| A positional argument in a `.jaz` file (`🐭.build("dev")`)            | `ArgumentError`     |
| A pipe stage leaving zero, or more than one, parameter unbound        | `ArgumentError`     |
| Binding an unknown parameter in a curry expression                    | `ArgumentError`     |
| A call missing an argument for a required parameter                   | `ArgumentError`     |
| A call supplying an argument for a parameter already bound by a curry | `ArgumentError`     |
| A call through a boolean that some reachable function would reject    | `ArgumentError`     |
| An import naming a file that does not exist                           | `ModuleImportError` |
| An import naming a symbol the module does not export                  | `ModuleImportError` |
| A call to a function or module that does not exist                    | `ResolutionError`   |

Variable references are **not** checked at load time: `🐐` and `🐭` variables can be
assigned from any function in any module, so whether a reference resolves depends on
what has run.

### 12.3 Run-time errors

| Condition                                                      | Class               |
| -------------------------------------------------------------- | ------------------- |
| A block exits non-zero                                         | `ExecutionError`    |
| An unresolvable reference without a `?` marker                 | `ResolutionError`   |
| A path into a value that has no such field or index            | `ResolutionError`   |
| `⚙️.parse` given text that is not valid JSON                   | `ExecutionError`    |
| `⚙️.load_env` given a missing file, unless `required=false`    | `ExecutionError`    |
| `⚙️.load_config` given a missing file, unless `required=false` | `ExecutionError`    |
| A load-time circular import (section 10.8)                     | `ModuleImportError` |

A run-time error **aborts the whole run**: no further lines, dependencies or calling
targets run. Nothing is rolled back.

### 12.4 Reporting

`jaz` prints the message prefixed with its source location, and exits non-zero:

```
$ jaz build
jazzoo.jaz:12: error: build() has no parameter named 'profile'
```

`--trace` additionally prints the Python stack trace. It is never shown otherwise,
since it describes Jazzoo's internals rather than the user's file.

Errors raised while reading the config (section 13.7) are not `JazzooError`s. They
are raised by `get_config` in the script's own process, and are reported by that
script; to `jaz` they are an ordinary non-zero exit.

---

## 13. Config Files

### 13.1 Overview

A Jazzoo file names one or more YAML config files with `⚙️.load_config` (section
7.4). A script that the file runs — a Python shebang block, or any `python foo.py`
shell line — reads values from the merged config with a single call:

```
⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")
⚙️.load_config(path=⚙️.module.dirname / "config/local.yaml", required=false)

build:
    #!/usr/bin/env python3
    from jazzoo import get_config as get

    src = get("/root/src")
    print(f"building {src}")
```

```yaml
# config/base.yaml
root:
  project_dir: ${PROJECT_DIR}
  src: ${/root/project_dir}/src
  build_dir: ${/root/project_dir}/build
```

Jazzoo only manages the list of config files; it never reads them itself.

### 13.2 `get_config`

```python
from jazzoo import get_config as get

get("/root/src")                # a value: str, int, float, bool, None, list or dict
get("/root/tags/0")             # a list element, by index
get("/")                        # the whole config
get("/root/port", default=80)   # 80 if the path does not exist
```

- The argument is a path into the config: `/`-separated keys, starting with `/`. A
  segment that addresses a list is an integer index. Empty segments are ignored, so
  `/root/` is the same as `/root`.
- A path that does not start with `/` is a `ValueError`; `default` does not apply.
- `get` returns the value at the path, fully expanded (section 13.5). A dict or list
  is expanded recursively.
- A path that does not exist raises `ConfigKeyError`, which names the path and the
  first segment that was not found.
- With `default=<value>`, `get` returns `<value>` instead of raising `ConfigKeyError`
  when the path does not exist. The default is returned as is; it is not expanded.
  It only covers a missing path: an error while expanding a value that exists (e.g.
  an unset environment variable) is still raised.
- `get` reads the config list from `JAZZOO_CONFIG_FILES`. When the variable is unset
  or empty, the config is `{}`.

### 13.3 Caching and the environment

- `get` builds the config just in time and caches it. The cache key is the value of
  `JAZZOO_CONFIG_FILES`; when the list changes, the cache is rebuilt.
- The cache holds the merged raw tree, a copy of the environment, and every value
  expanded so far. `${NAME}` reads from the copy, not from the live environment, so
  every `get` sees the environment as it was at the first `get`. The result
  therefore does not depend on the order in which values are expanded: lazy
  expansion gives the same values as expanding the whole config up front would. A
  later change to the environment is only seen after the cache is rebuilt.
- Expansion is lazy: `get("/root/src")` expands only `/root/src` and whatever it
  references. A broken value elsewhere in the config (e.g. an unset environment
  variable in a section the script never reads) does not make `get` fail.

`prepare_config()` builds the cache for the current `JAZZOO_CONFIG_FILES` now,
instead of at the first `get`:

```python
from jazzoo import prepare_config

prepare_config()
os.environ["SHOP_USER"] = "deploy"   # does not affect later get calls
```

- It reads and merges the files and copies the environment. It expands nothing and
  returns `None`.
- A script that changes its environment calls it first, so that `get` keeps seeing
  the environment as it was when the script started.
- File errors (`ConfigFileError`) are raised by `prepare_config`, so they show up at
  the start of the script. A broken value does not make it fail, because nothing is
  expanded.
- When the cache for the current list already exists, it does nothing; in
  particular, it does not take a new copy of the environment.

### 13.4 Reading and merging files

Config files are read as plain YAML (no Python object tags). A file must contain a
single YAML document whose top level is a mapping, or be empty, which counts as
`{}`. Anything else is a `ConfigFileError` that names the file, as is a YAML syntax
error (with the file and line), a Python object tag such as `!!python/object`, and a
file in the list that no longer exists.

The files are merged in list order; a later file overrides an earlier one:

- two dicts are merged key by key, recursively;
- in all other cases the later value replaces the earlier one. This includes lists:
  a later list replaces an earlier list, it is not appended to;
- `null` is an ordinary value: it replaces the earlier value, it does not delete the
  key.

Merging happens before expansion, so a reference always sees the merged value. A
`local.yaml` that sets `/root/project_dir` also changes `/root/src` in `base.yaml`.

### 13.5 Expansion

Expansion applies to string values only. Keys are never expanded.

**References to other config values.** `${/a/b}` is replaced by the value at path
`/a/b` in the merged config.

- If the whole string is one reference, the result is the referenced value with its
  own type, which may be a number, list or dict: `threads: ${/build/nr_of_threads}`
  yields the number `2`.
- If the reference is part of a longer string, the referenced value is rendered into
  it as in Jazzoo substitution (section 4.3): a string as is, a number as JSON, a
  boolean as `true` or `false`, and `null` as the empty string. A list or dict is a
  `ConfigExpansionError`.
- The referenced value is expanded first, so references may chain.
- A reference to a path that does not exist is a `ConfigExpansionError`.
- A reference cycle (`/a` references `/b`, which references `/a`) is a
  `ConfigExpansionError` that lists the paths in the cycle.

**Nested references.** A reference may contain other references; the inner ones are
expanded first, and the result is used as the path:

```yaml
env: prod
urls:
  dev: http://localhost:8000
  prod: https://example.com
api_url: ${/urls/${/env}} # https://example.com
```

- An inner reference must yield a string or number, which becomes part of the path.
  A list, dict, boolean or `null` is a `ConfigExpansionError`.
- An inner reference may be an environment variable: `${/urls/${ENV_NAME}}`.
- Nesting may be any number of levels deep.

**Environment variables.** `${NAME}` (no leading `/`) is replaced by the environment
variable `NAME`.

- An unset variable is a `ConfigExpansionError`.
- `${NAME:-default}` yields `default` when `NAME` is unset or empty.
- `$NAME` without braces is not expanded; it stays literal text, so shell snippets
  stored in a config (`echo $HOME`) are left alone.
- The environment is that of the script that calls `get`, as copied when the cache
  was built (section 13.3). Variables that the Jazzoo file loaded with `⚙️.load_env`
  are therefore visible.

**Escapes.** `$${` yields a literal `${`.

### 13.6 The `jazzoo.config` sub-package

`get_config`, `prepare_config` and the config errors live in the sub-package
`jazzoo.config`, and are re-exported by `jazzoo`, so `from jazzoo import get_config`
works.

The sub-package is self-contained: it imports only the standard library and its own
modules, and its internal imports are relative. A project that does not want to
depend on `jazzoo`, or whose interpreter does not have `jazzoo` installed (e.g.
because `jaz` was installed with `pipx`), can copy the sub-package into its own
source tree under any name and call its `get_config`. It reads the same
`JAZZOO_CONFIG_FILES` that `jaz` sets.

Jazzoo has no runtime dependencies, so YAML is read with a vendored, pure-Python
copy of PyYAML inside the sub-package. It is never imported as `yaml`, so a PyYAML
installed in the same venv is neither used nor affected.

### 13.7 Config errors

| Class                  | Meaning                                                          |
| ---------------------- | ---------------------------------------------------------------- |
| `ConfigFileError`      | a config file is missing, is not valid YAML, or is not a mapping |
| `ConfigKeyError`       | `get` was given a path that does not exist, without a default    |
| `ConfigExpansionError` | a `${...}` cannot be expanded                                    |

All three subclass `ConfigError(Exception)`, defined in `jazzoo.config`. They are not
`JazzooError`s, so that the sub-package stays self-contained. A `ConfigFileError`
names the file and, for a syntax error, starts with `<file>:<line>:` like Jazzoo's
own errors. The other two name the config path involved and, where it is known, the
config file that supplied the value.

---

## 14. Running Commands

### 14.1 Overview

A script that a Jazzoo file runs — a Python shebang block, or any `python foo.py`
shell line — runs commands with `run`:

```python
from jazzoo import run

run("my-app --config=simple doit")                      # runs in the foreground
run("docker compose logs | grep error")                 # a string runs in bash
run(["tmux", "send-keys", "-t", pane, command, "C-m"])  # a list runs directly
head = run("git rev-parse HEAD", capture=True).stdout
if run("tmux has-session -t blogs", check=False).returncode != 0:
    run("tmux new-session -d -s blogs")
```

Jazzoo files themselves do not need `run`: a shell line already runs a command.

### 14.2 `run`

```python
run(command, cwd=None, env=None, capture=False, check=True, echo=False) -> CommandResult
```

**The command** is a string or a list:

- A string runs in bash (`bash -c "<command>"`), so pipes, `&&`, `;`, redirection,
  `$HOME`, `~`, globs and quoting work as in a shell line of a Jazzoo file.
- A list runs directly, without a shell: the first term is the executable, and the
  others are passed as they are. Its executable is looked up on the `PATH` of the
  command's environment before anything runs; a term that contains a `/` is used as a
  path. An executable that is not found is a `CommandNotFoundError`. For a string,
  bash reports an unknown command itself (exit code 127).
- An empty command is a `ValueError`.

A value that is pasted into a string becomes shell syntax, as in section 5.5. Use the
list form for values from variables, or quote them with `shlex.quote`.

**Where and how it runs:**

- `cwd` is the working directory of the command; a directory that does not exist is a
  `ValueError`, raised before anything runs.
- `env` is a dict of variables that is laid over `os.environ`; the script's own
  environment is not changed.
- By default the command runs in the foreground: it inherits the script's stdin,
  stdout and stderr, and `run` waits until it ends. Whether it reaches the terminal
  depends on where the script's stdout goes; under `jaz`, that is the terminal in an
  interactive function (section 9.7).
- With `capture=True`, stdout and stderr are captured as text instead of being shown.
  Stdin is still inherited.
- With `echo=True`, the command is printed before it runs. A string is shown as given,
  a list with `shlex.join`; with `cwd`, the directory comes first:
  `(/app/src) python manage.py migrate`.

**Ctrl-c.** While a command runs, `run` ignores SIGINT in the script (in the main
thread), so a ctrl-c reaches the command only. Afterwards the old handler is restored.
If the command was ended by SIGINT, `run` raises `KeyboardInterrupt`.

**The result** is a `CommandResult` with `command` (as given), `returncode`, and
`stdout` and `stderr` (`None` unless captured). With `check=True` (the default), a
non-zero exit code raises `CommandFailedError`, which holds the result and names the
command and the exit code (and includes the captured stderr). With `check=False`,
`run` returns the result whatever the exit code, for commands that answer a question
through their exit code (`grep -q`, `tmux has-session`).

### 14.3 The `jazzoo.commands` sub-package

`run`, `CommandResult` and the command errors live in the sub-package
`jazzoo.commands`, and are re-exported by `jazzoo`, so `from jazzoo import run` works.
Like `jazzoo.config` (section 13.6), the sub-package is self-contained: it imports only
the standard library and its own modules, and its internal imports are relative, so a
project can copy it into its own source tree under any name.

### 14.4 Command errors

| Class                  | Meaning                                                      |
| ---------------------- | ------------------------------------------------------------ |
| `CommandNotFoundError` | the executable of a list command is not on the `PATH`        |
| `CommandFailedError`   | a command exited non-zero while `check=True`                 |

Both subclass `CommandError(Exception)`, defined in `jazzoo.commands`. Like the config
errors, they are not `JazzooError`s. Invalid arguments (an empty command, a missing
`cwd`) are `ValueError`s.

---

## 15. Unspecified

- **Default shell.** Whether the shell used for jazzoo-mode lines can be configured
  (e.g. a `set shell` directive) is not yet specified.
- **Preset config values.** Values that `get_config` could provide without a config
  file defining them — the directory of the module that loaded a config file, the
  root module's directory, or the directory of the config file itself (to anchor
  relative paths inside it) — are not yet specified.

---

## Appendix A. Implementation Model

This appendix describes the reference implementation's data model. It is not part of
the language.

### A.1 Error classes

```python
class JazzooError(Exception):
    message: str
    filename: T.Optional[str]   # the .jaz file the error is attributed to
    line: T.Optional[int]       # 1-based line number within that file

class ParseError(JazzooError): ...         # malformed file, detected at load time
class ResolutionError(JazzooError): ...    # unknown variable, function, module or namespace
class ArgumentError(JazzooError): ...      # wrong or missing arguments at a call site
class ModuleImportError(JazzooError): ...  # an import that cannot be satisfied
class ExecutionError(JazzooError): ...     # a block exited non-zero
```

None of these shadow a Python builtin, so they can be imported without aliasing.

The config errors (section 13.7) form a separate hierarchy in `jazzoo.config`:

```python
class ConfigError(Exception): ...
class ConfigFileError(ConfigError): ...       # a config file that cannot be read
class ConfigKeyError(ConfigError): ...        # a get_config path that does not exist
class ConfigExpansionError(ConfigError): ...  # a ${...} that cannot be expanded
```

The command errors (section 14.4) form another separate hierarchy in
`jazzoo.commands`:

```python
class CommandError(Exception): ...
class CommandNotFoundError(CommandError): ...  # the executable of a list command is not found
class CommandFailedError(CommandError): ...    # a command exited non-zero; holds the CommandResult
```

### A.2 Scopes

The parse tree is a tree of nested scopes: the root
module, with imported modules as sub-modules of the module that imports them.

```python
class Variable:
    name: str
    # Any JSON value: str, int, float, bool, None, list or dict.
    value: T.Any

class Scope:
    variables: T.List[Variable]
    functions: T.List[Function]

class Module(Scope):
    filename: str
    modules: T.List[Module]

class Parameter:
    name: str
    default: T.Optional[Expression]  # None = required; evaluated at call time

class Function(Scope):
    parameters: T.List[Parameter]
    is_target: bool              # False for [private] functions
    is_interactive: bool         # True for [interactive] functions
```

- A `Module` contains sub-modules and functions; a `Function` contains local functions
  but no sub-modules.
- `parameters` is the static signature. At call time the arguments are validated
  against it and then stored in `variables`; the body reads only from `variables`.
- A function is a target when `is_target` is true, i.e. when it is not `[private]`.
