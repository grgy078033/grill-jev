# Integrations

## Matt Pocock `grill-with-docs`

Recommended sequence:

```text
grilling frontier question
  → candidate options exist
  → construct DecisionState
  → construct EvaluationPlan
  → run grill-jev
  → present evidence + agent recommendation
  → user settles decision
  → return to grill-with-docs
  → CONTEXT.md / ADR handling remains upstream
```

`grill-jev` must not fork or duplicate the `grilling` primitive.

## Custom planning workflows

Any workflow can integrate if it can provide:

- one current decision question;
- two or more candidate options;
- minimum sufficient state;
- an evaluation plan with traceable dimensions.

## Harness portability

The protocol intentionally avoids Pi-specific session APIs. Pi, Codex, Claude Code, or another compatible agent can build the JSON artifacts and call the same script.

The output-to-user contract is in [presentation.md](presentation.md). Implement the same visible content, not an identical widget:

| Host capability | Presentation adapter |
|---|---|
| Pi with `ask_user_question` exposed | Map concise candidate labels and descriptions to the actual tool schema; omit `preview` by default. |
| Codex or Claude Code with a native question tool exposed and permitted | Use that tool's documented title/label and description equivalents. Inspect the current schema and mode restrictions; do not copy Pi-specific arguments. |
| Any host without a usable question tool, or with insufficient option/field capacity | Show the compact comparison directly in chat and ask for a stable option ID or a custom response. |

Before opening a question, show Jev evidence and agent reasoning separately. Menu descriptions must carry the short score summaries; long hidden previews are not a substitute. Preserve built-in custom-response behavior and respect reserved labels, option limits, and single-select semantics. Do not launch a separate agent, switch modes, install tooling, or request an extra API evaluation solely to render this menu.

### Loading in other hosts

Skill discovery paths and recursive discovery differ across hosts and versions. Preserve this repository's layout so `SKILL.md` can resolve `../../docs/`; do not assume copying only the skill subtree is sufficient. If automatic discovery is unavailable, ask the agent to read `<repo>/skills/grill-jev/SKILL.md` explicitly and resolve its references relative to that file. This provides the instructions without requiring Pi-specific slash commands.

This contract does not claim that every Codex/Claude Code version has been visually tested or that all terminal sizes can display every line. If the user reports hidden lines, shorten the menu or use the plain-text fallback.
