# State Firewall

The State Firewall exists to prevent "more context" from becoming "more bias, more leakage, and more private data".

## Include

- current decision question;
- candidate options;
- user-authored goals;
- constraints;
- already-settled decisions that materially affect this decision;
- verified facts;
- known unknowns.

## Exclude

- the full transcript;
- the parent agent's preference or recommendation;
- previous Jev answers;
- stale or rejected alternatives unless their rejection itself is a settled constraint;
- secrets, tokens, credentials, private keys;
- full source files when a short verified fact is enough;
- irrelevant project details.

## Minimum sufficient state

Prefer:

```json
{"fact":"NPC employees already have daily schedules"}
```

over pasting the entire employee-system implementation.

## Provenance

Every goal, constraint, fact, and settled decision should include a source. The source is for auditability, not authority. Typical values:

- `user`
- `CONTEXT.md`
- `ADR-004`
- `codebase:path/to/file`
- `research:<artifact>`

Do not label an inference as a verified fact.
