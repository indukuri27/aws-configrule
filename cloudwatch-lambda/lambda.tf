data "archive_file" "init" {
  type        = "zip"
  source_file = "config-non-compliant.py"
  output_path = "config-non-compliant.zip"
}


resource "aws_lambda_function" "config_noncompliant" {
  filename      = data.archive_file.init.output_path
  function_name = "config-compliant-status"
  role          = aws_iam_role.unused_eips_role.arn
  handler       = "config-non-compliant.lambda_handler"

  source_code_hash = filebase64sha256(data.archive_file.init.output_path)
  
  runtime = "python3.8"
  environment {
    variables = {
      SOURCE_EMAIL = "indukuriv@gmail.com",
      DEST_EMAIL   = "indukuriva@gmail.com"
    }
  }
}