"""Challenge 05 grader — does terraform/ecs_service.tf actually describe a
blue/green deployment you could roll back?

`terraform validate` only proves the configuration parses and the argument names
exist. A rolling update parses perfectly well. These checks are the difference
between "valid Terraform" and "a release you can undo", which is the whole point
of the deck's Blue/Green section.

Run locally:
    pip install pytest python-hcl2
    pytest week8/8.4-the-secure-release-gate/labs/tests -q
"""

import pathlib

import hcl2
import pytest

TERRAFORM_DIR = pathlib.Path(__file__).resolve().parent.parent / "terraform"

MINIMUM_BAKE_MINUTES = 15
REQUIRED_LIFECYCLE_STAGE = "POST_PRODUCTION_TRAFFIC_SHIFT"


def _unquote(value):
    """python-hcl2 8.x keeps the source quotes on block labels and string
    literals: `'"BLUE_GREEN"'` rather than `'BLUE_GREEN'`. Strip them so the
    assertions below read like the Terraform they are checking."""
    if isinstance(value, str) and len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def _first(value):
    """hcl2 wraps repeatable blocks in lists. Unwrap one level."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _get(block, key):
    """Read an argument out of a parsed block, without its quotes."""
    return _unquote(block.get(key)) if block else None


def _load_resources():
    resources = {}
    for path in sorted(TERRAFORM_DIR.glob("*.tf")):
        with path.open() as handle:
            parsed = hcl2.load(handle)
        for block in parsed.get("resource", []):
            for kind, named in block.items():
                for name, body in named.items():
                    resources[(_unquote(kind), _unquote(name))] = body
    return resources


@pytest.fixture(scope="module")
def service():
    resources = _load_resources()
    body = resources.get(("aws_ecs_service", "phr_api"))
    assert body is not None, (
        "No aws_ecs_service.phr_api found in terraform/. Did you rename it?"
    )
    return body


@pytest.fixture(scope="module")
def resources():
    return _load_resources()


@pytest.fixture(scope="module")
def deployment(service):
    block = _first(service.get("deployment_configuration"))
    assert block is not None, (
        "aws_ecs_service.phr_api has no deployment_configuration block."
    )
    return block


def test_strategy_is_blue_green(deployment):
    strategy = _get(deployment, "strategy")
    assert strategy == "BLUE_GREEN", (
        "strategy is {!r}. A ROLLING update mutates the service in place: the "
        "old task set is gone, so there is nothing to roll back to. Set "
        'strategy = "BLUE_GREEN".'.format(strategy)
    )


def test_bake_time_gives_you_a_rollback_window(deployment):
    bake = _get(deployment, "bake_time_in_minutes")
    assert bake is not None, (
        "No bake_time_in_minutes. Without a bake time ECS tears BLUE down as "
        "soon as traffic shifts, and a bug found two minutes later means a full "
        "redeploy instead of a 10-second flip back."
    )
    assert int(bake) >= MINIMUM_BAKE_MINUTES, (
        "bake_time_in_minutes is {}. The PHR standard is at least {} minutes — "
        "long enough for the error rate to show up in dashboards while BLUE is "
        "still warm.".format(bake, MINIMUM_BAKE_MINUTES)
    )


def test_lifecycle_hook_runs_after_traffic_shifts(deployment):
    hook = _first(deployment.get("lifecycle_hook"))
    assert hook is not None, (
        "No lifecycle_hook. This is where the ZAP/smoke check plugs in — if it "
        "returns FAILED, ECS rolls back before the deployment completes. "
        "Without it, nothing automated is watching the cutover."
    )

    raw_stages = hook.get("lifecycle_stages") or []
    if isinstance(raw_stages, str):
        raw_stages = [raw_stages]
    stages = [_unquote(stage) for stage in raw_stages]
    assert REQUIRED_LIFECYCLE_STAGE in stages, (
        "lifecycle_stages is {!r}. It must include {!r} — the check has to run "
        "after traffic flips to GREEN, or it is not testing what users are "
        "hitting.".format(stages, REQUIRED_LIFECYCLE_STAGE)
    )
    assert _get(hook, "hook_target_arn"), "lifecycle_hook has no hook_target_arn."
    assert _get(hook, "role_arn"), "lifecycle_hook has no role_arn."


def test_second_target_group_exists(resources):
    assert ("aws_lb_target_group", "green") in resources, (
        "There is only one target group. Blue/green needs two: ECS reweights "
        "the ALB listener from the BLUE target group to the GREEN one. One "
        "target group means there is nowhere to put the new version."
    )


def test_service_points_at_the_alternate_target_group(service):
    load_balancer = _first(service.get("load_balancer"))
    assert load_balancer is not None, "aws_ecs_service.phr_api has no load_balancer block."

    advanced = _first(load_balancer.get("advanced_configuration"))
    assert advanced is not None, (
        "load_balancer has no advanced_configuration block. Creating a green "
        "target group is not enough — the service has to be told about it, or "
        "ECS has no alternate to shift traffic to."
    )

    alternate = _get(advanced, "alternate_target_group_arn") or ""
    assert "green" in str(alternate), (
        "alternate_target_group_arn is {!r}; it should reference "
        "aws_lb_target_group.green.arn.".format(alternate)
    )
    assert _get(advanced, "production_listener_rule"), (
        "advanced_configuration has no production_listener_rule. That is the "
        "ALB rule ECS reweights during the cutover."
    )
    assert _get(advanced, "role_arn"), (
        "advanced_configuration has no role_arn. ECS needs a role to modify "
        "your listener on your behalf."
    )
