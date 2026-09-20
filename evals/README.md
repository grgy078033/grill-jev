# Evals

`grill-jev` should be evaluated as a decision protocol, not only by whether one example "looks sensible".

Planned invariance and robustness cases:

1. **Option-order invariance** — permuting candidate order should not materially change the result.
2. **Recommendation leakage** — recommendation-like fields must be rejected before they reach Jev.
3. **Irrelevant context robustness** — unrelated state should not materially move a decision.
4. **Contradictory constraints** — conflicting state should be surfaced rather than silently hidden.
5. **Missing candidate** — candidate coverage should rise when an obvious materially distinct option is omitted.
6. **Paraphrase stability** — semantically equivalent option wording should remain broadly stable.

The initial repo ships local protocol tests; live Jev benchmark cases can be added once labeled examples and thresholds are defined.
