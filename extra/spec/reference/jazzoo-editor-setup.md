# Jazzoo Editor Setup

This document describes how to type the four sigils of Jazzoo in an editor.

---

## 1. The sigils

| Sigil | Name    | Namespace | Code points       |
| ----- | ------- | --------- | ----------------- |
| 🐐    | Goat    | global    | `U+1F410`         |
| 🐭    | Mouse   | module    | `U+1F42D`         |
| 🐆    | Leopard | local     | `U+1F406`         |
| ⚙️    | System  | built-in  | `U+2699 U+FE0F`   |

The system sigil is a gear followed by a variation selector, which asks for the emoji
form. Jazzoo also accepts the gear without the selector (`⚙`), which is what some
input methods produce.

## 2. VS Code

Bind a key to each sigil. Open the command palette, run
**Preferences: Open Keyboard Shortcuts (JSON)**, and add these entries to the list:

```json
[
  {
    "key": "ctrl+alt+meta+g",
    "command": "type",
    "args": { "text": "🐐" },
    "when": "editorTextFocus && (resourceExtname == .jaz || resourceFilename == jazzoo)"
  },
  {
    "key": "ctrl+alt+meta+m",
    "command": "type",
    "args": { "text": "🐭" },
    "when": "editorTextFocus && (resourceExtname == .jaz || resourceFilename == jazzoo)"
  },
  {
    "key": "ctrl+alt+meta+l",
    "command": "type",
    "args": { "text": "🐆" },
    "when": "editorTextFocus && (resourceExtname == .jaz || resourceFilename == jazzoo)"
  },
  {
    "key": "ctrl+alt+meta+j",
    "command": "type",
    "args": { "text": "⚙️" },
    "when": "editorTextFocus && (resourceExtname == .jaz || resourceFilename == jazzoo)"
  }
]
```

- The letters are mnemonics: **g**oat, **m**ouse, **l**eopard, and **j** for jazzoo.
- The `when` clause limits the keys to Jazzoo files. Drop the part after
  `editorTextFocus` to type the sigils in any file, e.g. in the docs of a project.
- `meta` is Cmd on macOS, and the Super or Windows key elsewhere. Window managers on
  Linux and Windows often claim combinations with that key; pick other keys if one of
  them does not reach VS Code.

## 3. Other editors

- **The emoji picker of the OS** works in every editor: Win+. on Windows,
  Ctrl+Cmd+Space on macOS. Search for "goat", "mouse", "leopard" and "gear".
- **Snippets or abbreviations** of the editor, or a system-wide text expander, can turn
  a short word such as `;g` into a sigil.
- **Copy a sigil** from the table in section 1.
