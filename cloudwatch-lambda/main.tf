
resource "aws_cloudwatch_event_rule" "config_noncompliant" {
  name        = "config-compliance-change-notification"
  description = "Alerts for Config status change"

  event_pattern = <<EOF
    {
    "source": [
        "aws.config"
    ],
    "detail-type": [
        "Config Rules Compliance Change"
    ],
    "detail": {
        "messageType": [
        "ComplianceChangeNotification"
        ]
    }
    }
EOF
}

resource "aws_cloudwatch_event_target" "config_event" {
  target_id = "config_noncompliant_event"
  rule      = aws_cloudwatch_event_rule.config_noncompliant.name
  arn       = aws_lambda_function.config_noncompliant.arn
}

