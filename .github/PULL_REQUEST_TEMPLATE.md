# Week 8.4 — The Secure Release Gate

**Name:**

**Challenges completed:**

---

## Why

Answer only the questions for the challenges you actually did. Two or three
sentences each — this is the part that shows you understood the gate rather than
the edit, and it is the only thing that separates the two.

### Challenge 01 — The Belt

After re-running with `break_scan=true`, `deploy-staging`, `dast` and
`smoke-test` came back **grey (skipped)** rather than **red (failed)**. Why does
that distinction matter to whoever is reading the pipeline at 2am?

>

### Challenge 02 — The CVE Gate

Trivy was already scanning and already printing CRITICALs before you touched it.
Why did adding `--exit-code 1` change anything that mattered?

>

### Challenge 03 — The Bill of Materials

You replaced `if: always()` with `needs: build-and-scan` on the `sbom` job. What
would be wrong with an SBOM that got generated regardless of whether the scan
passed?

>

### Challenge 04 — Proving It Is Ours

`cosign verify` passed before you pinned `--certificate-identity-regexp`. What
question was it actually answering at that point, and why is that question not
worth much?

>

### Challenge 05 — A Release You Can Undo

`terraform validate` was green on the rolling-update version too. What does the
blue/green configuration give you that a valid rolling update does not?

>

### Challenge 06 — The Running App

ADR-0026 rows 03 and 04 were suppressions with an expiry date on them. What is
the risk of an *expired* suppression that a finding nobody ever suppressed does
not have?

>

### Challenge 07 — The Last Check

The `break_deploy=true` run deployed an app that returned 500 while still
reporting itself healthy. Which single change made your smoke test catch it, and
why did the original version not?

>

---

## Anything you got stuck on

Genuinely useful — it tells us which part of the material to rework. No marks
either way.

>

## Did you use `solutions/` on any challenge?

If so, which. This is fine and it is what the overlay is there for; we just need
to know so the feedback is about the right thing.

>
