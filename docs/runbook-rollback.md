# Roll back the last release — PHR API

**Status:** incomplete. Challenge 07 finishes it.

**When to use:** the new version is erroring above 1% after promotion, or during
the 15-minute bake time.

**Who can run this:** any on-call engineer. That is the test — if it only works
when the person who wrote the deploy is awake, it is not a runbook.

## Step 1: Trigger the rollback in ECS

_(not written yet)_

## Step 2: Verify BLUE is serving

_(not written yet)_

## Step 3: Reconcile IaC

_(not written yet)_

---

**Dry-run rule:** every quarter, run this against a test deploy to prove it still
works. A runbook nobody has executed is a wish.
