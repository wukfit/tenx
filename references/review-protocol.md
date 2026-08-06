# TenX independent planning review

Follow this when a phase requires an independent review. `Independent reviewer` is defined in [definitions](definitions.md).

1. Use a reviewer who neither authored the record nor will implement it.
2. Provide read-only exact sources, approved records and consulted-source manifest. Require independent source/caller enumeration, manifest corrections and every named probe without leading findings.
3. Persist full output, reviewer/run identity, input/source digests, probe answers, findings and owning-phase routing. The verdict is a line reading exactly `Verdict: PASS` or `Verdict: FAIL`; the Gate reads that line verbatim, so an unreplaced placeholder or a line naming both outcomes is not a pass.
4. Resolve findings and rerun the same reviewer until it rechecks every prior finding and returns `PASS` for the exact revision. A replacement receives the full history and re-verifies everything. Never discard an unfavourable review.
5. A record change invalidates its verdict. No reviewer means Gate failure. Review validates evidence; it stands in for user approval only where these controls delegate a Gate (Investigate), never elsewhere.
