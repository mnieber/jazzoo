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
🐭.tracing = true
```

### Types

A variable holds a JSON value: a string, a number, a boolean, `null`, an array, or an
object.

**A string on the right-hand side of an assignment must be quoted.** An unquoted word
is read as JSON, so `true`, `false`, `null` and `8080` are the boolean, null and number
values, and anything else is a `ParseError`:

```
🐆.flag = true       # the boolean
🐆.flag = "true"     # the string
🐆.name = "jane"     # a string, quoted
🐆.name = jane       # ParseError: strings must be quoted
```

Without this rule `🐆.flag = true` would be ambiguous the moment booleans exist, and
which reading won would decide whether `"yes" if 🐆.flag else "no"` is asking about a
boolean or about a five-character string. Quoting settles it in the source, where the
author can see it.

Quoting is required only where an expression is parsed. Two positions have no
expression grammar and so keep bare words, because there a word can only be a string:

- reference defaults — `⚙️.env.LOG_LEVEL?:-info` (see section 4)
- command-line arguments — `jaz build myapp` (see section 10)

Jazzoo does no arithmetic. A number is a value it can hold and pass around, not one it
can compute with: there is no `+`, and `==` compares the rendered strings. Numbers
exist so that a JSON document can round-trip through jazzoo unchanged.

### Structured values

A variable can hold an object or an array, and a dotted name reaches inside it:

```
🐆.config.name = "jane"
🐆.config.port = 8080
🐆.retval = 🐆.config.name        # "jane"
```

Assigning to a path creates the intermediate objects, so the two lines above are
enough to build `{"name": "jane", "port": 8080}` — `🐆.config` need not be declared
first. Assigning to a path under a value that is not an object replaces it.

Array elements are reached by index, written as an ordinary path segment:

```
🐆.hosts = ["a.example.com", "b.example.com"]
🐆.first = 🐆.hosts.0
```

A path that does not exist is unresolvable, exactly like an unset variable: it raises
a `ResolutionError` unless marked with `?` (see section 4).

```
🐆.maybe = 🐆.config.nickname?          # "" when absent
🐆.level  = 🐆.config.log-level?:-info  # "info" when absent or empty
```

Only `🐐`, `🐭` and `🐆` hold structured values. `⚙️` is a fixed set of built-ins, and
`⚙️.env` values are always strings, because that is what the environment provides.

A dotted name is also how a function inside an imported namespace is reached
(`🐭.docker.build`, section 9), so `🐭.a.b` is lexically both a field path and a call
path. Rather than pick a winner, jazzoo forbids the collision: a namespace alias and a
`🐭` variable may not share a name, in either order. This is the same rule that already
keeps a variable and a function apart (section 13), extended to the third thing a `🐭`
name can denote.

```
from ./docker.jaz import build as docker

🐭.docker.build = "x"     # error: `docker` is already a namespace
```

Because the collision is impossible, the first segment of a dotted `🐭` name always has
exactly one reading, and it can be determined from the file rather than from what
happens to be defined when the line runs.

### Rendering a value as text

Substitution always produces text (section 4), so every value has a string rendering:

| Value       | Renders as                      |
| ----------- | ------------------------------- |
| string      | the string itself, unquoted     |
| number      | its JSON form: `8080`, `1.5`    |
| boolean     | `true` / `false`                |
| `null`      | the empty string                |
| array/object | compact JSON, no spaces        |

```
🐆.config.name = "jane"
🐆.config.port = 8080

echo 🐆.config.name    # jane
echo 🐆.config.port    # 8080
echo 🐆.config         # {"name":"jane","port":8080}
```

A scalar renders bare rather than as JSON, so `echo 🐆.config.name` prints `jane` and
not `"jane"`. This is what keeps the common case — a variable holding a string — behaving
exactly as it did before structured values existed.

Rendering a container yields JSON that a downstream tool such as `jq` can consume. The
braces and quotes are spliced into the line as text and are **not** escaped for the
interpreter, so section 4's warning about untrusted values applies with extra force
here: a container rendering is live shell syntax. Use `⚙️.sh-quote` when the value did
not come from the `.jaz` file itself.

### Parsing and emitting JSON

Two pipe operators cross between text and structure:

- `⚙️.parse` reads a JSON string and yields the value it describes
- `⚙️.json` renders any value as JSON — unlike plain substitution, a string comes back
  quoted, so the result is always valid JSON

```
🐆.config = 🐭.load-config() | ⚙️.parse   # stdout of load-config, parsed
🐆.name   = 🐆.config.name                # reach into it
🐆.text   = 🐆.config | ⚙️.json           # back to a JSON string
```

`⚙️.parse` raises an `ExecutionError` if the text is not valid JSON, and is the only
way structure enters jazzoo from outside — a command's stdout is text until it is
parsed.

### Truthiness

In ternary expressions a value is falsy when it is:

- the boolean `false`, or `null`
- an empty array or an empty object
- the number `0`
- a string whose lowercased form is in `["0", "false", "no", ""]`

Everything else is truthy. The string rule allows natural use of env-var-style boolean
flags, and the others make `"yes" if 🐆.config.items else "no"` mean what it looks like.

Note that truthiness is decided on the value, not on its rendering — an empty array is
falsy even though it renders as the non-empty text `[]`.

### Testing for emptiness with `⚙️.empty`

Truthiness answers "does this value mean yes?", which is deliberately generous about
env-var spellings. A different and equally common question is "did I get anything back
at all?" — and for that the string rule gives the wrong answer, because a command that
printed `no` printed something:

```
🐆.result = 🐭.check-status()
🐆.nothing-came-back = 🐆.result | ⚙️.empty
```

`⚙️.empty` yields `true` when the value is the empty string, an empty array, an empty
object, or `null`, and `false` for everything else — including `"no"`, `"false"` and
`"0"`, which are falsy but not empty.

| Value      | Truthy? | `⚙️.empty` |
| ---------- | ------- | ---------- |
| `""`       | no      | `true`     |
| `[]`, `{}` | no      | `true`     |
| `null`     | no      | `true`     |
| `"no"`     | no      | `false`    |
| `"false"`  | no      | `false`    |
| `"0"`      | no      | `false`    |
| `"hello"`  | yes     | `false`    |

The two disagree on exactly the three env-var spellings, which is the point: use
truthiness to read a flag, and `⚙️.empty` to ask whether a command produced output.

### Capturing a truthiness decision with `⚙️.bool`

A ternary consumes truthiness but does not hand it back. `⚙️.bool` yields the decision
itself as a boolean, so it can be stored, passed to a function, or rendered:

```
🐆.ci = ⚙️.env.CI?  | ⚙️.bool      # true / false, whatever spelling CI used
🐭.report(enabled=🐆.ci)
```

It applies the same rule as a ternary condition, so `"yes"`, `"1"` and `"anything"`
yield `true`, while `""`, `"no"`, `"false"`, `"0"`, `null`, `[]`, `{}` and `0` yield
`false`. Its value is a real boolean, so it renders as `true` or `false` and is itself
truthy or falsy accordingly.

`⚙️.bool` is total: every value maps to a boolean and nothing raises. That is
deliberate, because the values it is for arrive as *strings* from `⚙️.env` or a
command's stdout, and a version that rejected `"yes"` would fail exactly where it is
most useful. Where a genuine boolean is required, take it from `⚙️.parse`, which
preserves JSON's own `true` and `false`.

The three ways of asking about a value line up like this:

| Value     | Truthy? | `⚙️.bool` | `⚙️.empty` |
| --------- | ------- | --------- | ---------- |
| `""`      | no      | `false`   | `true`     |
| `null`    | no      | `false`   | `true`     |
| `[]`, `{}` | no     | `false`   | `true`     |
| `"no"`    | no      | `false`   | `false`    |
| `"yes"`   | yes     | `true`    | `false`    |
| `["a"]`   | yes     | `true`    | `false`    |

`⚙️.bool` is the truthiness column made into a value; `⚙️.empty` answers a different
question and is not its negation.

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

| Variable    | Value                                                    |
| ----------- | -------------------------------------------------------- |
| `⚙️.stdout` | Stdout of the last shebang block in the current function |
| `⚙️.output` | `⚙️.stdout` minus its trailing newline, if it has one    |

### Environment variables

`⚙️.env.SOME_ALL_CAPS_VALUE` refers to an environment variable. All-caps is a convention, not a requirement. There is no syntax for enumerating the environment — variables are only ever accessed by name.

An environment variable that is not set cannot be resolved, and referencing it is a `ResolutionError` like any other unresolvable reference. Use the `?` marker (see section 4) to say that absence is expected.

### Loading a dotenv file with `⚙️.loadenv`

`⚙️.loadenv` reads a dotenv file and exports its variables into the environment:

```
⚙️.loadenv(path=⚙️.module.dirname / ".local.env")
⚙️.loadenv(path=⚙️.module.dirname / "secrets.env", required=false)
```

It is a statement, not an expression: it yields no value, and its only effect is on
the environment. After it runs, the variables are visible through `⚙️.env`, and every
later subprocess inherits them, so a command can use them as ordinary `$VAR`s.

It may appear at the top level of a module, where it runs when the module is loaded,
or as a line in a function body, where it takes effect from that line on.

The file holds `KEY=VALUE` lines. Blank lines and lines starting with `#` are skipped,
and a value wrapped in single or double quotes loses its quotes.

A variable that is **already set** in the environment keeps its value; the file only
fills in what is missing. This lets the caller override the file for one run
(`BLOGS_SHELL_COMMAND=bash jaz shell`), which is the same rule `just` and Docker
Compose use.

By default the file is required, and a missing file is an `ExecutionError`, so a
misspelled path is caught. `required=false` makes the file optional: when it is
missing nothing is loaded and no error is raised. This suits a per-developer override
file that not everyone has.

`⚙️.loadenv` is the one `⚙️` built-in with a side effect. It does not make `⚙️`
assignable — it changes the process environment, which `⚙️.env` reads.

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

Braces hold any expression (section 5), not only a reference. The expression is
evaluated and its value substituted:

```
echo "shell: {{ 🐆.cmd if 🐆.cmd else "bash" }}"
echo "fallback: {{ 🐆.cmd or "sh" }}"
echo "file: {{ 🐆.path | ⚙️.basename }}"
```

The quotes of a string literal inside braces belong to jazzoo, so they are gone
before the interpreter sees the line.

A braced expression is parsed when the file is loaded. A malformed one, such as
`{{ 🐆.cmd if 🐆.cmd }}`, is therefore a `ParseError` up front, rather than something
that renders as an empty string when the line runs.

### Escaping

Prefix the emoji sigil with `\` to suppress substitution:

```
echo "Running test with \🐭.tracing set to: 🐭.tracing"
echo "Running test with \🐭.tracing set to: 🐭.tracing\.com"  # prints .com after the value of 🐭.tracing
```

This prints the literal emoji and `.tracing` text for the escaped reference, and substitutes the unescaped one.

A `\` is **required** to end a name before a literal dot, because a dot otherwise
continues the name into a structured lookup (section 3):

```
🐭.tracing\.com    # the value of 🐭.tracing, then the text ".com"
🐭.tracing.com     # the `com` field of 🐭.tracing - a ResolutionError if there is none
```

A reference still ends on its own at any character that cannot start a path segment,
so only a following dot needs the escape. `🐭.tracing/com`, `🐭.tracing-com` and
`🐭.tracing:com` are unambiguous as written.

A dot only continues the name when what follows it could actually begin a segment —
a letter, a digit or an underscore. A dot followed by anything else is ordinary text,
which is what lets a reference end a sentence without an escape:

```
echo "Hello 🐆.name."              # "Hello jane."
echo "Hello 🐆.name. Welcome"      # "Hello jane. Welcome"
echo "🐆.dir./config"              # the value, then "./config"
```

Only `🐭.tracing.com` — a dot followed immediately by a name character — needs the
escape, because that really is indistinguishable from a field lookup.

To produce a literal `{{ 🐐.log-level }}` string:

```
echo "Jazzoo supports the {{ \🐐.log-level }}-setting syntax"
```

### Optional references and defaults

By default every reference must resolve: an unset variable is a `ResolutionError` (see section 12). Two markers relax that, and they apply uniformly to `🐐`, `🐭`, `🐆` and `⚙️.env`.

`?` marks a reference as **possibly absent**. It resolves to the empty string instead of raising:

```
🐆.ci-flag = "--ci" if ⚙️.env.CI? else ""
```

`:-` supplies a **default** used when the value is empty:

```
🐐.log-level:-info
```

Combined as `?:-`, the reference may be absent _and_ has a default — the default applies when it is absent or empty:

```
⚙️.env.LOG_LEVEL?:-info
```

The four forms:

| Syntax         | If absent         | If empty     |
| -------------- | ----------------- | ------------ |
| `⚙️.env.X`     | `ResolutionError` | empty string |
| `⚙️.env.X?`    | empty string      | empty string |
| `⚙️.env.X:-y`  | `ResolutionError` | `y`          |
| `⚙️.env.X?:-y` | `y`               | `y`          |

A default may be a bare string or a quoted one; bare defaults end at the first whitespace, so quote anything containing spaces:

```
⚙️.env.GREETING?:-hello
⚙️.env.GREETING?:-"hello there"
```

Both markers are part of the reference syntax, so they work in bare and braced positions alike, and `\` still terminates the variable name before them:

```
echo {{ ⚙️.env.LOG_LEVEL?:-info }}-setting
echo ⚙️.env.HOST\?:-literal        # prints the value of HOST, then "?:-literal"
```

Note that `:-` was chosen over a bare `:` because colons follow references routinely in shell lines — `⚙️.env.HOST:8080`, `-v ⚙️.env.HOME:/data` — and a bare `:` would silently read those as defaults.

### Substitution is textual, and values are not escaped

Substitution splices the value into the line as text, before the interpreter sees it. Jazzoo does not quote or escape what it splices, so a value containing interpreter syntax becomes interpreter syntax:

```
🐆.name = "; rm -rf ~ #"
echo "Hello 🐆.name"          # the shell sees a second command
```

This is the same exposure that `just`, `make` and a bare `$VAR` in a shell script have, and it follows from substituting into blocks that jazzoo treats as opaque. Jazzoo cannot escape correctly on the user's behalf: the same mechanism substitutes into bash words, Python identifiers (see section 6), JSON literals and interpreters jazzoo knows nothing about, and the correct escaping differs in each. Automatic quoting would be wrong in most of them.

In practice this matters when a value does **not** come from the `.jaz` file itself. A `.jaz` file is code the author already trusts — someone who can edit it does not need an injection to run commands. The channels that carry data from elsewhere are:

- `⚙️.stdout` and `⚙️.output` — the output of the last block, which may include filenames, branch names, or anything else a command printed
- `⚙️.env.*` — environment variables, especially in CI
- arguments passed on the command line

Treat values from those three as untrusted, and escape them for the context they land in.

### Escaping values with `⚙️.sh-quote`

`⚙️.sh-quote` renders a value as a single, safely quoted POSIX shell word:

```
🐆.safe = 🐆.filename | ⚙️.sh-quote
echo 🐆.safe                  # always exactly one shell word
```

It wraps the value in single quotes and escapes any single quotes inside it, so the result cannot expand, split, or terminate the surrounding command — the same guarantee as Python's `shlex.quote`. Use it whenever an untrusted value lands in a shell block:

```
list-branch(name):
    🐆.safe-name = 🐆.name | ⚙️.sh-quote
    git log 🐆.safe-name
```

Note that `⚙️.sh-quote` is a jazzoo pipe, evaluated in an expression before the line runs — it is not a shell pipeline. Applying it inside a shell line would be read by the shell, not by jazzoo.

`⚙️.sh-quote` produces a _shell_ word. It is not correct for Python, JSON, or any other interpreter, and applying it there yields a literal `'…'` string.

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

Chaining is right-associative: `A if C1 else (B if C2 else C)`. A condition is a
boolean expression: string equality (`==`), bare truthiness, and the operators below.

### Boolean operators

`and`, `or` and `not` combine values by their truthiness (section 3), and parentheses
group:

```
🐆.doit = "yes" if 🐆.foo or (🐆.bar and not 🐭.test) else "no"
```

Precedence follows Python, loosest first: `or`, then `and`, then `not`, then `==`. So
`a or b and not c` reads as `a or (b and (not c))`, and parentheses override it.

`and` and `or` yield **one of their operands**, not a plain boolean — `and` yields its
left operand when that is falsy and otherwise its right, and `or` does the reverse.
This is what makes `or` usable as a fallback, and it matches how the `?:-` default
marker already behaves:

```
🐆.name = 🐆.given or "anonymous"    # the given name, or "anonymous" if it is empty
```

Because a ternary tests truthiness, using such a value as a condition gives the answer
you would expect either way; the operand rule only matters when the result is kept.

When the operands are functions, the result is a function, and it can be called or
piped into like any other:

```
🐆.out = (🐭.fast or 🐭.slow)(input="x")
🐆.out = "x" | (🐭.fast or 🐭.slow)
```

Which function a boolean yields is only known at run time, so a call through one is
checked against **every** function it could reach: the call must be valid for all of
them. That keeps a call site correct whichever operand wins, and it is checked at load
time like any other call (section 12).

For the same reason, every branch must yield a function for the value to be callable
at all. A boolean whose operands are not all functions may still be assigned, rendered
and passed around — only *calling* it is an error, because one branch would produce
something uncallable:

```
🐆.thing = 🐭.some-string or 🐭.runner   # fine on its own
🐆.thing(x="1")                          # error: 🐭.some-string is not a function
```

This is what keeps the value fallback in the previous section unaffected: `🐆.given or
"anonymous"` involves no functions and is never called.

`not` is different: it always yields a real boolean, since there is no operand to pass
through.

```
🐆.quiet = not 🐭.verbose            # true or false
```

Both operators **short-circuit**. `or` does not evaluate its right operand when the
left is truthy, and `and` does not when the left is falsy. This matters because an
operand may be a function call:

```
🐆.ok = 🐭.cheap-check() or 🐭.expensive-check()
```

Short-circuiting applies to resolution as well, so an unresolvable reference on the
skipped side raises nothing.

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
- ⚙️.sh-quote: renders the value as a single, safely quoted POSIX shell word (see section 4)
- ⚙️.parse: parses a JSON string into a structured value (see section 3)
- ⚙️.json: renders any value as a JSON string (see section 3)
- ⚙️.empty: yields whether the value is empty, which is not the same as falsy (see section 3)
- ⚙️.bool: yields the value's truthiness as a boolean (see section 3)

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

### Comments

A line whose first non-whitespace character is `#` is a jazzoo comment. It is discarded
when the file is parsed, so it never reaches an interpreter:

```
build():
    # fetch the sources first
    git clone 🐆.url
```

The exception is `#!`, which stays a shebang and keeps its meaning from the previous
section — including bare `#!` returning to jazzoo mode.

Being discarded at parse time is what makes a comment inert everywhere it could
otherwise have an effect. A comment is not substituted, so a reference inside one is
just text and an unresolvable one is not an error. It is not echoed to the console. And
it is not a block, so it leaves `⚙️.stdout` alone — adding a comment between a command and
the line that reads its output does not change what that line sees.

Comments are stripped only from jazzoo-mode lines. Inside a shebang block the body
belongs to that interpreter, so a `#` line is passed through untouched and Python's or
bash's own comments — including pragmas such as `# noqa` — survive the sweep.

Only whole lines are comments. A `#` after other text on a line is part of that line,
because it is ordinary syntax in the shells jazzoo drives:

```
grep '#define' 🐆.header      # this whole line is passed to the shell
```

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

### Console output

Jazzoo shows what it runs, the way `just` does. A jazzoo-mode line is echoed to the
console before it runs, followed by its output. Prefix the line with `@` to hide the
echo; the output is still shown:

```
build():
    echo "starting"      # prints the command, then "starting"
    @echo "starting"     # prints only "starting"
```

A shebang block is **not** echoed. Its swept body is a script, not a command, and
printing it would bury the output under the source. Only what the block writes is
shown.

#### Quiet calls

A call whose return value is used is **quiet**: neither the commands it runs nor
their stdout reach the console. A value is used when the call is:

- the right-hand side of an assignment: `🐆.ip = 🐭.host-ip()`
- a stage in a pipe: `🐭.load-config() | ⚙️.parse`
- an operand or an argument: `🐭.cheap() or 🐭.expensive()`
- substituted inline into a line: `echo "ip: 🐭.host-ip()"`

The output of such a call is data for the caller, not a message for the user, so it
behaves like `$(...)` in a shell or a backtick in `just`. This matters most for
module-level assignments, which run every time the module is loaded — including for
`jaz --list` — and would otherwise print their output on every invocation.

A call used as a statement is not quiet: a dependency, a mid-body call on its own
line, or a target invoked from the CLI prints its commands and their output as usual.

Quietness covers the whole call. Functions that a quiet call invokes as statements
are quiet too, as they would be inside `$(...)`.

Only stdout is held back. A quiet call's stderr still reaches the console, so its
warnings and errors stay visible. Being quiet changes nothing about the value: the
call's stdout is captured into `⚙️.stdout` and its return value exactly as before.

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

A function declares _parameters_; a caller supplies _arguments_ for them. A parameter may have a default value or be required (no default). Arguments are always named:

```
build(target, mode="release"):
    cargo build --target=🐆.target --profile=🐆.mode

test():
    🐭.build(target="dev")   # correct
    🐭.build("dev")          # raises an error, arguments are always named
```

A default is an expression, like the right-hand side of an assignment, so the usual
rules apply: a string must be quoted, and a default may reference a `🐐` or `🐭`
variable or `⚙️.env`:

```
🐭.default-mode = ⚙️.env.BUILD_MODE?:-release

build(target, mode=🐭.default-mode):
    cargo build --target=🐆.target --profile=🐆.mode
```

A default is evaluated each time the function is called without that argument, in
the scope of the module that defines the function. It resolves to the variable's
value, never to its name.

### Currying

Square brackets are used to create a curried function:

```
🐭.build_in_dev = 🐭.build[mode="dev"]
```

You can think of this as creating a new function in which the `mode` parameter is bound to "dev". The caller may no longer supply an argument for `mode`.

A bound value is an expression, like an argument, so a string must be quoted and a
value may reference a variable — including a `🐆` local of the body that writes the
curry:

```
build-for(user):
    🐆.build = 🐭.build[mode=🐭.default-mode, target=🐆.user]
```

The bound values are evaluated **once, where the brackets are written**, not each
time the curried function is called. Reassigning `🐭.default-mode` afterwards does not
change `🐆.build`, and `🐆.user` keeps its value after the body that bound it has
returned. This differs from a parameter default, which is evaluated on every call that
omits it: a default belongs to the function, whereas a curry captures a value at one
point in the caller.

A bare parameter name inside the brackets does the opposite — it marks that parameter as explicitly **unbound**:

```
🐭.clean_up_name = 🐭.clean_up[name, max_length=3]
```

Here `name` is left open, `max_length` is bound to `3`, and every other parameter of `clean_up` must already have a default. This is the form used to prepare a function for a pipe (see below), where exactly one parameter must be left unbound.

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

This requires that exactly one parameter is left unbound for each function in the pipe. The piped value becomes the argument for that parameter, and the call's return value is piped onwards to the next stage.

A parameter is unbound if the curry expression does not bind it to a value — either because it is named bare in the brackets, or because the brackets are absent or empty. Which parameter is free must be unambiguous from the expression alone; defaults play no part in deciding it. It is an error for a stage to leave zero parameters unbound, or more than one.

`🐭.drop-config-dir-part` above is piped without brackets, which is the same as `🐭.drop-config-dir-part[]` — so it must declare exactly one parameter in total. A function with more than one parameter has to say which is free, even when every other parameter has a default:

```
🐭.f[path]                # path is free; style takes its default
🐭.f[style="posix"]       # equivalent, by binding everything else
🐭.f                      # error for f(path, style="posix") - ambiguous
```

Naming the free parameter is usually clearer, since it also says that every other parameter falls back to its default.

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
This can be suppressed using `@echo "Hello 🐆.who! Tracing is: 🐭.tracing"`. Because
`🐆.dump` is called for its value, the call is quiet anyway; see "Console output" in
section 6.

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

The same holds for calls. A function resolves its dependencies and its mid-body calls
against the module that defines it, wherever it is called or exported from. It can
therefore call its own module's private functions and imported namespaces, and an
importer only has to import or export the function itself:

```
# lib.jaz
from ./helper.jaz import other as _h

[private]
_prepare():
    echo "preparing"

build(): _prepare()        # found in lib.jaz, not in the importer
    🐭._h.other()          # likewise
```

```
# jazzoo
from ./lib.jaz export build   # `jaz build` works; _prepare and _h stay private
```

### Exporting into the module namespace (public)

Exported functions land flat in `🐭` and become targets — visible to outside importers, the CLI, and `jaz --list`. An export may instead group them under a layer; see the next section.

```
from ./foo.jaz export bar                           # 🐭.bar()
from ./foo.jaz export (bar, okay)                   # 🐭.bar(), 🐭.okay()
from ./foo.jaz export (bar as hello,)               # 🐭.hello()
from ./foo.jaz export (bar as hello, okay)          # 🐭.hello(), 🐭.okay()
from ./foo.jaz export *                             # 🐭.<all exported functions from foo>()
```

`export *` includes only functions that `foo.jaz` itself exports — it does not transitively pull in functions that `foo.jaz` imported privately.

### Exporting into a namespace layer (public)

An export may also name a namespace, which groups the exported functions under a
layer instead of landing them flat:

```
from ./hello.jaz export (build_fe as build,) as fe      # jaz fe.build mode=dev
from ./hello.jaz export (build, test) as fe             # jaz fe.build, jaz fe.test
from ./hello.jaz export * as fe                         # jaz fe.<function>
```

Naming symbols into a layer **requires the tuple form**, because a bare symbol before
`as` is already the rename form: `export bar as fe` exports `bar` under the name `fe`,
and keeps that meaning. `export (bar,) as fe` is how the layer is asked for instead —
the trailing comma is what makes a one-symbol tuple.

`export * as fe` needs no tuple, since `*` cannot be renamed and so has only one
reading.

Layers nest, because a layer is itself an exported symbol. A module that exports a
layer offers it under that name, and an importer may re-export it exactly as it would
a function:

```
from ./react.jaz export (build_react,) as react   # in fe.jaz
from ./fe.jaz export (react,) as fe               # in the root file
```

which gives:

```
jaz fe.react.build_react mode=dev
```

Naming a layer selects it whole — every target inside it comes along, at every depth.
A layer may be renamed like any other symbol, which renames the path segment:

```
from ./fe.jaz export (react as r,) as fe          # jaz fe.r.build_react
```

`export *` carries every symbol the module exports, layers included, so
`from ./fe.jaz export * as fe` reaches the same target without naming `react`.

Each file only declares its own layer. The root file says that it exports `fe`, and
`fe.jaz` says that it exports `react`; neither needs to know how deep the result goes.

Because a layer and a function are both symbols, a module may not export both under
one name; doing so is a `ParseError` in the module that declares the second one.

Exporting into the same layer more than once **aggregates**, so a layer can be
assembled from several files:

```
from ./frontend.jaz export (build,) as fe
from ./styles.jaz export (lint,) as fe      # fe now has build and lint
```

Two exports landing the same name in one layer is a `ParseError`, attributed to the
second statement, per the rule in section 13.

### A layer alias and an import alias are separate

The same name may be used for an import namespace and an export layer:

```
from ./hello.jaz import (build,) as fe      # 🐭.fe.build() - callable in this file
from ./hello.jaz export (build,) as fe      # jaz fe.build - callable from the CLI
```

These do not collide, because they populate two different surfaces. A `.jaz` file can
only refer to *imported* symbols, so `🐭.fe.build()` always means the import; the CLI
can only reach *exported* symbols, so `jaz fe.build` always means the export. Neither
surface can see the other, which is why one name can serve both without ambiguity.

This is the one place where the section 13 uniqueness rule does not apply, and it is
because an export layer is not something a `.jaz` file can name at all.

### Import/export semantics summary

| Form                                 | Callable as              | CLI / `jaz --list` |
| ------------------------------------ | ------------------------ | ------------------ |
| `from ./foo.jaz import bar as ns`    | `🐭.ns.bar()`            | ✗                  |
| `from ./foo.jaz import (a, b) as ns` | `🐭.ns.a()`, `🐭.ns.b()` | ✗                  |
| `from ./foo.jaz import * as ns`      | `🐭.ns.<function>()`     | ✗                  |
| `from ./foo.jaz export bar`          | `🐭.bar()`               | ✓                  |
| `from ./foo.jaz export bar as hello` | `🐭.hello()`             | ✓                  |
| `from ./foo.jaz export *`            | `🐭.<function>()`        | ✓                  |
| `from ./foo.jaz export (a,) as ns`   | `jaz ns.a` (CLI only)    | ✓ (under `ns`)     |
| `from ./foo.jaz export * as ns`      | `jaz ns.<function>`      | ✓ (under `ns`)     |

A layered export is reachable from the CLI only. To call it from within a `.jaz`
file as well, import it under a namespace too — the two aliases are independent, and
may share a name.

---

## 10. CLI

```
jaz <target> [arg=value ...]   # run a target
jaz --list [<path>]            # list targets, or describe what is at <path>
jaz --list-all                 # list the entire target tree
jaz --file <path>              # use <path> instead of the default file
jaz --trace <target>           # on error, also print the stack trace
```

### Targets in an export layer

A target inside an export layer (section 9) is named by its dotted path:

```
jaz fe.build mode=dev
jaz fe.react.build mode=dev
```

The path is resolved against export layers only. Import namespaces are not reachable
from the CLI, so a name that exists solely as an import is `no such target`.

### Listing

`jaz --list` lists the root file's targets. An export layer appears as a single entry
marked as a layer rather than being expanded, so the listing stays the size of the file
that produced it:

```
$ jaz --list
build
test
fe...          # a layer; use `jaz --list fe`
```

`jaz --list <path>` describes what is at that path. For a layer, that is its members —
again one level deep:

```
$ jaz --list fe
fe.build
fe.test
fe.react...
```

For a target, it is the signature, which is how a caller finds out what arguments it
takes:

```
$ jaz --list fe.build
fe.build(mode="release")
```

`jaz --list-all` walks the whole tree and lists every target at every depth:

```
$ jaz --list-all
build
test
fe.build
fe.test
fe.react.build
```

Because circular imports are allowed (section 14), the walk tracks the modules it has
already entered, keyed by resolved file path. A layer whose module has already been
entered is skipped rather than descended into, so `--list-all` always terminates and
never prints the same target twice.

### No dry-run mode

Jazzoo has no `--dry-run`. A dry run would have to predict the commands a target
issues without running them, and in jazzoo that is not decidable in general: a body
can branch on `⚙️.output`, pass a called function's return value onwards, or compute
a dependency argument — all of which need a command to have actually run. Since every
jazzoo-mode line is its own subprocess and `⚙️.output` is re-read after each one, this
is the main path rather than an edge case.

A dry run could only cover straight-line bodies, and would have to either invent
values or stop at the first undecidable point. Inventing them prints a plausible
fiction that diverges from reality exactly when the script is complex enough to want
checking, so the feature is omitted rather than made unreliable. `--list` covers
discovering what a file offers, and `--trace` covers debugging a failure.

### Argument passing

Arguments are always named:

```
jaz debug name=jane
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

Because phase 2 is textual and phase 1 never inspects the block's contents, jazzoo has no notion of the syntactic context a value lands in, and does not escape substituted values. See section 4 for what that means for untrusted input.

---

## 12. Errors

All errors jazzoo raises derive from a single base class, `JazzooError`. Subclasses exist to distinguish the kind of failure:

```python
class JazzooError(Exception):
    message: str
    filename: T.Optional[str]   # the .jaz file the error is attributed to
    line: T.Optional[int]       # 1-based line number within that file

class ParseError(JazzooError):       # malformed file, detected in phase 1
class ResolutionError(JazzooError):  # unknown variable, function, module or namespace
class ArgumentError(JazzooError):    # wrong or missing arguments at a call site
class ModuleImportError(JazzooError):  # an import that cannot be satisfied
class ExecutionError(JazzooError):   # a shebang block exited non-zero
```

None of these shadow a Python builtin, so they can be imported directly without aliasing.

Every error carries the `.jaz` file and line it is attributed to, so the message can point at the offending source rather than at jazzoo's internals.

### When errors are detected

Errors are reported as early as they can be. Anything decidable from the parse tree alone is a **parse-time** error, raised when the file is loaded — before any subprocess runs, and regardless of which target was invoked. A `.jaz` file with a bad call site in one target therefore fails even when a different target is run, and `jaz --list` fails too. This is deliberate: mistakes surface immediately rather than when some rarely-used branch is first exercised.

| Condition                                                             | Class               |
| --------------------------------------------------------------------- | ------------------- |
| Syntax that does not parse                                            | `ParseError`        |
| An unquoted string in an expression (`🐆.x = hello`)                  | `ParseError`        |
| A malformed expression inside `{{ }}`                                 | `ParseError`        |
| Two of a variable, function or namespace sharing a name in one scope  | `ParseError`        |
| Two exports landing the same name in one export layer                 | `ParseError`        |
| A module exporting both a function and a layer under one name         | `ParseError`        |
| A positional argument in a `.jaz` file (`🐭.build("dev")`)            | `ArgumentError`     |
| A pipe stage leaving zero, or more than one, parameter unbound        | `ArgumentError`     |
| Binding an unknown parameter in a curry expression                    | `ArgumentError`     |
| A call missing an argument for a required parameter                   | `ArgumentError`     |
| A call through a boolean that some reachable function would reject    | `ArgumentError`     |
| A call through a boolean whose branches are not all functions         | `ParseError`        |
| A call supplying an argument for a parameter already bound by a curry | `ArgumentError`     |
| An import naming a file that does not exist                           | `ModuleImportError` |
| An import naming a symbol the imported module does not export         | `ModuleImportError` |
| A call to a function or module that does not exist                    | `ResolutionError`   |

Variable references are **not** checked at parse time. `🐐` and `🐭` variables may be assigned from any function body in any module, so whether a given reference resolves depends on which targets and dependencies have run — it is not decidable from the parse tree.

The rest are **run-time** errors, raised while a target executes:

| Condition                                                 | Class               |
| --------------------------------------------------------- | ------------------- |
| A shebang block exits non-zero                            | `ExecutionError`    |
| A reference that cannot be resolved, without a `?` marker | `ResolutionError`   |
| A path into a value that has no such field or index       | `ResolutionError`   |
| `⚙️.parse` given text that is not valid JSON              | `ExecutionError`    |
| `⚙️.loadenv` given a missing file, unless `required=false` | `ExecutionError`   |
| A load-time circular import (see section 14)              | `ModuleImportError` |

A run-time error **aborts the whole run** — jazzoo does not continue with the remaining lines of the body, with later dependencies, or with the target that triggered a dependency. Nothing is rolled back: steps that already ran have already had their effects.

### What the user sees

By default `jaz` prints only the error message, prefixed with its source location, and exits with a non-zero status:

```
$ jaz build
jazzoo.jaz:12: error: build() has no parameter named 'profile'
```

Passing `--trace` additionally prints the Python stack trace, for debugging jazzoo itself:

```
jaz --trace build
```

A stack trace is never shown without `--trace` — it describes jazzoo's internals, not the user's `.jaz` file, and the location in the message is what the user can act on.

---

## 13. Scope and Object Model

Jazzoo's parse tree is structured as nested scopes. The entry-point `.jaz` file is the root module. Imported modules are sub-modules of the module that imports them.

```python
class Variable:
    name: str
    # Any JSON value: str, int, float, bool, None, list or dict. A dotted
    # reference reaches into a list or dict; see section 3.
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
```

Key properties:

- **`Module`** is a `Scope` and can contain sub-modules (from imports) and functions.
- **`Function`** is a `Scope` and can contain local functions, but not sub-modules.
- **Parameters** are the static call signature. At call time, jazzoo validates the caller's arguments against `parameters`, then populates `variables` with the resolved values. The function body only ever reads from `variables`.
- **Targets** are functions with `is_target = True` — i.e. all functions not marked `[private]`. Only targets are callable from the CLI and visible in `jaz --list`.

### Names are unique within a scope

A `Scope` holds `variables`, `functions` and sub-modules separately, but a reference names only a sigil and a name — `🐭.foo` does not say which of the three to look in. A scope may therefore not define two of them under the same name, in any order. Doing so is a `ParseError`:

```
🐭.foo = "bar"

foo():              # error: `foo` is already defined in this scope
    echo "hello"
```

The error is attributed to whichever of the two came **second** in the file, since
that is the declaration to remove. Assigning a variable again is not a second
declaration — `🐭.cfg = "x"` followed by `🐭.cfg.name = "y"` is a re-assignment, and
only the first mention counts as the declaration.

This covers currying too, since a curry expression assigns a function to a variable:

```
build(target, mode="release"):
    cargo build --target=🐆.target --profile=🐆.mode

🐭.build = 🐭.build[mode="dev"]   # error: `build` is already defined in this scope
```

It covers an imported namespace alias too, which is the third thing a `🐭` name can
denote:

```
from ./docker.jaz import build as docker

🐭.docker = "x"           # error: `docker` is already defined in this scope
🐭.docker.port = "8080"   # error: same, the first segment is what collides
```

The rule applies per scope, so a local `🐆.foo` may shadow a module-level `🐭.foo` — they are different scopes, and their sigils tell them apart. What lives *inside* a namespace is a separate scope as well: `🐭.docker.build` and a module-level `🐭.build` do not collide, because only the first segment names something in this scope.

Export layers (section 9) are outside this rule, because they are not part of any scope
a `.jaz` file can name. A layer alias may therefore share a name with an import
namespace, a variable, or a function, and two exports into one layer collide only with
each other.

---

## 14. Open Questions

- **`set shell`**: Should jazzoo support configuring the default shell (e.g. bash vs sh vs fish)? Currently unspecified.
- **Circular imports**: Circular imports are allowed. Modules are cached by resolved file path after first load; a circular import receives the cached partially-initialized module. Circular references used only at call time (mid-body function calls) are safe. Circular references at load time — module-level variable assignments that call into a module not yet fully initialized — are a runtime error. This is the same model as TypeScript (live bindings resolved at access time), which is more predictable than Python's approach (copied values resolved at import time, where failures depend on statement order).
