# Outputs for Blue-Green Deployment Module

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "blue_target_group_arn" {
  description = "ARN of the blue target group"
  value       = aws_lb_target_group.blue.arn
}

output "green_target_group_arn" {
  description = "ARN of the green target group"
  value       = aws_lb_target_group.green.arn
}

output "active_target_group_arn" {
  description = "ARN of the currently active target group"
  value       = var.current_environment == "blue" ? aws_lb_target_group.blue.arn : aws_lb_target_group.green.arn
}

output "inactive_target_group_arn" {
  description = "ARN of the currently inactive target group"
  value       = var.current_environment == "blue" ? aws_lb_target_group.green.arn : aws_lb_target_group.blue.arn
}

output "primary_listener_arn" {
  description = "ARN of the primary ALB listener"
  value       = aws_lb_listener.primary.arn
}

output "test_listener_arn" {
  description = "ARN of the test ALB listener"
  value       = aws_lb_listener.test.arn
}

output "traffic_switch_lambda_arn" {
  description = "ARN of the traffic switching Lambda function"
  value       = aws_lambda_function.traffic_switch.arn
}

output "health_check_lambda_arn" {
  description = "ARN of the health check Lambda function"
  value       = aws_lambda_function.health_check.arn
}

output "rollback_lambda_arn" {
  description = "ARN of the rollback Lambda function"
  value       = aws_lambda_function.rollback.arn
}

output "step_function_arn" {
  description = "ARN of the blue-green deployment Step Function"
  value       = aws_sfn_state_machine.blue_green_deployment.arn
}

output "deployment_log_group_name" {
  description = "Name of the CloudWatch log group for deployment events"
  value       = aws_cloudwatch_log_group.deployment_logs.name
}

output "deployment_log_group_arn" {
  description = "ARN of the CloudWatch log group for deployment events"
  value       = aws_cloudwatch_log_group.deployment_logs.arn
}

output "blue_environment_name" {
  description = "Name of the blue environment"
  value       = local.blue_environment
}

output "green_environment_name" {
  description = "Name of the green environment"
  value       = local.green_environment
}

output "active_environment" {
  description = "Name of the currently active environment"
  value       = var.current_environment
}

output "target_environment" {
  description = "Name of the target environment for deployment"
  value       = var.target_environment
}

output "blue_health_alarm_arn" {
  description = "ARN of the blue target group health alarm"
  value       = aws_cloudwatch_metric_alarm.blue_target_group_health.arn
}

output "green_health_alarm_arn" {
  description = "ARN of the green target group health alarm"
  value       = aws_cloudwatch_metric_alarm.green_target_group_health.arn
}

output "deployment_endpoints" {
  description = "Deployment endpoints for testing"
  value = {
    production = "https://${aws_lb.main.dns_name}"
    test       = "https://${aws_lb.main.dns_name}:${var.test_listener_port}"
  }
}

output "deployment_commands" {
  description = "Commands for manual deployment operations"
  value = {
    switch_to_blue = "aws stepfunctions start-execution --state-machine-arn ${aws_sfn_state_machine.blue_green_deployment.arn} --input '{\"action\":\"switch\",\"target\":\"blue\"}'"
    switch_to_green = "aws stepfunctions start-execution --state-machine-arn ${aws_sfn_state_machine.blue_green_deployment.arn} --input '{\"action\":\"switch\",\"target\":\"green\"}'"
    rollback = "aws stepfunctions start-execution --state-machine-arn ${aws_sfn_state_machine.blue_green_deployment.arn} --input '{\"action\":\"rollback\"}'"
  }
}