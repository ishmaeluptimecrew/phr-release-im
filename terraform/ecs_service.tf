# PHR API on ECS Fargate — the deploy stage of the Release Gate.
#
# This is how the team ships today: a rolling update. It works, right up until
# the version you rolled out is bad, at which point half your users are already
# on it and the old task set is gone.
#
# Challenge 05 converts this to native ECS blue/green.
#
# Nothing here is ever applied. There are no AWS credentials in this lab and no
# backend — `terraform validate` and the grader in tests/test_bluegreen.py read
# the configuration, they do not talk to AWS.

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
    strategy = "ROLLING"
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.blue.arn
    container_name   = "phr-api"
    container_port   = 8080
  }

  tags = {
    Name        = "phr-api"
    Environment = "staging"
    Owner       = var.owner_initials
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
    path                = "/healthz"
    matcher             = "200"
    interval            = 15
    healthy_threshold   = 2
    unhealthy_threshold = 2
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
