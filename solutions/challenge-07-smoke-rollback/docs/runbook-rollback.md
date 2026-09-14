# Roll back the last release — PHR API

**When to use:** the new version is erroring above 1% after promotion, or during
the 15-minute bake time.

**Who can run this:** any on-call engineer. That is the test — if it only works
when the person who wrote the deploy is awake, it is not a runbook.

**Before you start:** you do not need to know why it broke. Roll back first,
diagnose after. The investigation is easier when nobody is being paged.

## Step 1: Trigger the rollback in ECS

If ECS has not already auto-rolled back via the lifecycle hook:

```bash
aws ecs update-service \
  --cluster phr-staging \
  --service phr-api \
  --force-new-deployment
```

ECS shifts the ALB listener back to the BLUE target group. Takes about 10
seconds, because BLUE is still running — that is what `bake_time_in_minutes = 15`
bought you. Past the bake window BLUE is gone and this is a redeploy, not a
rollback, so check how long ago the promotion was before you start.

## Step 2: Verify BLUE is serving

```bash
curl -fsS https://phr-staging.acme.gov/healthz
```

Expect `200 OK` and the previous version in the body:

```json
{"status": "ok", "version": "1.2.3"}
```

Check the version number, not just the 200. A health check that passes on the
version you were trying to get rid of is the failure mode this step exists to
catch. Never assume the flip worked.

## Step 3: Reconcile IaC

```bash
git revert <bad-commit-sha>
terraform apply
```

Git now matches what is actually running. Skip this and the next deploy — or the
next person who runs `terraform apply` for an unrelated reason — quietly
re-applies the change you just rolled back.

## Afterwards

- Post the bad SHA and the rollback time in `#phr-releases`.
- Open a ticket before you close the incident. A rollback with no follow-up
  ticket becomes a permanent version freeze nobody remembers agreeing to.

---

**Dry-run rule:** every quarter, run this against a test deploy to prove it still
works. A runbook nobody has executed is a wish.

**Why this document exists:** an auditor asks "how would you roll back?". You
hand them this and the timestamped output of the last dry-run. "We would work it
out" is not an answer that passes.
