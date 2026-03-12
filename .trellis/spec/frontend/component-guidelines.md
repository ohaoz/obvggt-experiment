# Component Guidelines

> Not applicable in the current workspace.

---

## Current Rule

There is no maintained component system in this repository today.

If the user asks for experiment automation, evaluation, artifact validation, or server workflow changes:

- stay in Python / shell / Markdown / JSON
- do not introduce UI components as an unsolicited abstraction

---

## Common Mistakes To Avoid

- Adding a quick HTML page inside the controller tree for convenience
- Mixing presentation code with run-record generation
- Inventing React-style props/state conventions in a repo that does not have React at all
