# PHR API on ECS Fargate — SOLVED.
#
# Native ECS blue/green: no CodeDeploy, no appspec.yml. ECS stands GREEN up
# beside BLUE, health-checks it, reweights the ALB listener, then keeps BLUE
# warm for the bake time so a rollback is a 10-second flip rather than a
# redeploy.
#
# The four things Challenge 05 adds:
#   strategy = "BLUE_GREEN"        ECS runs the cutover itself
#   bake_time_in_minutes = 15      BLUE stays alive 15 min after the shift
#   aws_lb_target_group.green      somewhere to put the new version
#   lifecycle_hook                 the post-shift check that can force a rollback

resource "aws_ecs_service" "phr_api" {
  name            = "phr-api"
  cluster         = aws_ecs_cluster.phr_staging.id
  task_definition = aws_ecs_task_definition.phr_api.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.phr_api.id]
    assign_public_ip = false
  }

  deployment_configuration {
    strategy             = "BLUE_GREEN"
    bake_time_in_minutes = 15

    lifecycle_hook {
      hook_target_arn  = aws_lambda_function.post_deploy_check.arn
      role_arn         = aws_iam_role.ecs_bluegreen.arn
      lifecycle_stages = ["POST_PRODUCTION_TRAFFIC_SHIFT"]
    }
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.blue.arn
    container_name   = "phr-api"
    container_port   = 8080

    advanced_configuration {
      alternate_target_group_arn = aws_lb_target_group.green.arn
      production_listener_rule   = aws_lb_listener_rule.prod.arn
      role_arn                   = aws_iam_role.ecs_bluegreen.arn
    }
  }
}

resource "aws_ecs_cluster" "phr_staging" {
  name = "phr-staging"
}

resource "aws_lb_target_group" "blue" {
  name        = "phr-api-blue"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path    = "/healthz"
    matcher = "200"
  }
}

resource "aws_lb_target_group" "green" {
  name        = "phr-api-green"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path    = "/healthz"
    matcher = "200"
  }
}

resource "aws_lb_listener_rule" "prod" {
  listener_arn = var.listener_arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.blue.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

resource "aws_lambda_function" "post_deploy_check" {
  function_name = "phr-post-deploy-check"
  role          = aws_iam_role.ecs_bluegreen.arn
  handler       = "index.handler"
  runtime       = "python3.13"
  filename      = "check.zip"
}
