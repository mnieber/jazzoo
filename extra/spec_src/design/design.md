# Attribute lists

Several attributes can be written in one pair of brackets, separated by commas:

```
[private, interactive]
_shell():
    fish
```

This is the same as writing the attributes on separate lines, one per line. Both forms
keep working and can be mixed:

```
[private, interactive]
[private]
_shell():
    fish
```

The same holds for local functions (e.g. `[interactive]` before `🐆.build():`).

## Attribute lines

A line that starts with `[` directly followed by a letter or `_`, and ends with `]`, is
an attribute line, also in a function body. It is never a shell line. Shell tests are
not affected, because the shell needs a space after `[` and `[[` (e.g. `[ -d / ]`,
`[[ -f .env ]]`, `[ "a,b" = "a,b" ]` are shell lines).

This replaces the earlier rule that a `[name]` line in a body is an attribute only when
a local function header follows it.

## Decisions

- Whitespace around the commas and before the closing `]` is ignored:
  `[private,interactive]` and `[private , interactive ]` mean the same as
  `[private, interactive]`. A space directly after `[` makes the line a shell line
  (`[ private ]` is a shell test).
- The order of the attributes does not matter.
- A repeated attribute (`[private, private]`) is allowed and has no extra effect, as
  with two `[private]` lines.
- An unknown name in an attribute line (`[private, interactve]`) is a `ParseError` that
  names the unknown attribute and its line. In a body, this now also holds when no
  local function header follows.
- A malformed attribute line is a `ParseError` with the line of the attribute: an empty
  item (`[private,]`, `[private,,interactive]`), names without a comma
  (`[private interactive]`), or a name with characters that are not allowed in a name.
- An attribute line in a body that is not followed (after any further attribute lines
  and empty lines) by a local function header is a `ParseError`: an attribute must
  precede a function. The same holds at the top level for an attribute line that is not
  followed by a function.
- `private` before a local function is a `ParseError`, as for `[private]`.
