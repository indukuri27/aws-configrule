resource "aws_iam_policy" "unused_eips" {
  name        = "unused_eips_for_lambda"
  path        = "/"
  description = "Policy for unused eips"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1598854465023",
      "Action": "logs:*",
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Sid": "Stmt1598854510488",
      "Action": [
        "ec2:DescribeAddresses"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Sid": "Stmt1598854605238",
      "Action": [
        "ses:SendEmail"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}

# IAM Role for lambda

resource "aws_iam_role" "unused_eips_role" {
  name = "unused_eips_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}
# Attach role and policy
resource "aws_iam_role_policy_attachment" "unused_eips_attach" {
  role       = aws_iam_role.unused_eips_role.name
  policy_arn = aws_iam_policy.unused_eips.arn
}