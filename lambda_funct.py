import re
import boto3
import json
import pdfkit

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from json.decoder import JSONDecodeError
from jinja2 import Template
from botocore.exceptions import ClientError


DEV_OPS_DL = 'indukuriv@gmail.com'
AUDIT_EMAIL_ADDRESS = 'indukuriv@gmail.com'
RETURN_PATH_ADDRESS = 'indukuriv@gmail.com'
#SES_SOURCE_ARN = 'arn:aws:ses:us-east-1:900751145041:identity/mail..io'
#SES_RETURNPATH_ARN = 'arn:aws:ses:us-east-1:900751145041:identity/mail.io'
DEBUG_EMAIL_DESTINATION = 'indukuriv@gmail.com'
RULE_NAME_REGEX = '-(.*?)-'
ses_client = boto3.client('ses', region_name="us-east-1")
config_client = boto3.client('config')

# Read rule_info.json file
ruleinfo_data = json.load(open('rule_info.json', 'r'))  # Config rule data file
template_data = open('htmltopdf_template.j2', 'r', encoding='utf-8').read()  # Jinja2 template file
#with open('keys.json', encoding='utf-8') as fh:
#    data = json.load(fh)

#json_file = "sortSevLambda.json"
output_file = '/tmp/output.html'

# Lambda handler function


def lambda_handler(event, context):
    # pylint: disable=unused-argument
    generate_reports()


def is_prod_environment():
    """Returns True if running in dev environment otherwise False"""
    return False
    # return 'HOME' in os.environ and os.environ.get('ENVIRONMENT') == 'PROD'

# This is the main function that retrieves the data and emails the reports


def generate_reports():
    aggregators = get_aggregator_data('BusinessUnit')
    print('Got list of BU aggregators')
    for aggregator in aggregators:
        agg_rules_obj = {}
        agg_rules_obj['BusinessUnit'] = get_aggregator_business_unit(
            aggregator)
        agg_rules_obj['AggregatorName'] = aggregator['AggregatorName']
        agg_rules_obj['AggregatorRules'] = []
        resources_by_rule_name = {}

        for rule in aggregator['AggregatorRules']:
            try:
                base_rule_name = re.findall(
                    RULE_NAME_REGEX, rule['ConfigRuleName'])[0]
            except IndexError:
                continue  # Name doesn't match regex, skip this iteration of the for loop
            rule_resources = resources_by_rule_name.get(base_rule_name, [])
            paginator = config_client.get_paginator(
                'get_aggregate_compliance_details_by_config_rule')

            for page in paginator.paginate(
                    ConfigurationAggregatorName=aggregator['AggregatorName'],
                    ConfigRuleName=rule['ConfigRuleName'],
                    ComplianceType='NON_COMPLIANT',
                    AccountId=rule['AccountId'],
                    AwsRegion=rule['AwsRegion']):

                for eval_result in page['AggregateEvaluationResults']:
                    result = eval_result['EvaluationResultIdentifier']['EvaluationResultQualifier']
                    result['AccountId'] = rule['AccountId']
                    result['AwsRegion'] = rule['AwsRegion']
                    rule_resources.append(result)
            resources_by_rule_name[base_rule_name] = rule_resources
        for rule in resources_by_rule_name:
            rule_data = {'rule': rule,
                         'resources': resources_by_rule_name[rule]}
            if rule in ruleinfo_data:
                rule_data.update(ruleinfo_data[rule])
                agg_rules_obj['AggregatorRules'].append(rule_data)
        agg_rules_obj['AggregatorRules'].sort(
            key=lambda r: {'High': 0, 'Medium': 1, 'Low': 2}[r['severity']])
#        create_pdf(template_data, agg_rules_obj)
        print(f"Sending report for {get_aggregator_business_unit(aggregator)}")
#        send_email(aggregator, json.dumps(agg_rules_obj))

        pdf_report_file = create_pdf(template_data, agg_rules_obj)
        with open(pdf_report_file, 'r') as pdf_file:
            pdf_data = pdf_file.read()
        send_email(aggregator, pdf_data)

        print(f"Sent report for {get_aggregator_business_unit(aggregator)}")
        break


def create_pdf(template_data1, agg_rules_obj):
    options = {
        'page-size': 'Letter',
        'margin-top': '0.40in',
        'margin-right': '0.40in',
        'margin-bottom': '0.40in',
        'margin-left': '0.40in',
        'encoding': "UTF-8",
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
        'no-outline': None
    }
    template = Template(template_data1)
    finalData = template.render(
        aggregatorRules=agg_rules_obj['AggregatorRules'])
    with open(output_file, 'w') as pdf:
        pdf.write(finalData)
    config = pdfkit.configuration(wkhtmltopdf='./wkhtmltox/bin/wkhtmltopdf')
#    pdfkit.from_file(output_file, '/tmp/convertedpdf.pdf', options=options, configuration=config)
    outputpdf = '/tmp/convertedpdf.pdf'
    pdfkit.from_file(output_file, outputpdf, options=options, configuration=config)
    
    return outputpdf

def get_aggregator_data(aggregator_level):
    """
    Parameters:
    aggregatorLevel (string): filter by either Pillar or BusinessUnit.

    Returns a list of aggregators and their rules that were evaluated as non compliant
    """
    aggregator_rule_list = []
    aggregators = get_aggregators()

    for aggregator in aggregators:
        config_rules = []
        aggregator_name = aggregator['AggregatorName']
        tags = aggregator['Tags']
        if tags['AggregateLevel'] != aggregator_level:
            continue
        aggregator_info = {}
        aggregator_info['AggregatorName'] = aggregator_name
        aggregator_info['Tags'] = tags
        paginator = config_client.get_paginator(
            'describe_aggregate_compliance_by_config_rules')
        for page in paginator.paginate(ConfigurationAggregatorName=aggregator_name, Filters={'ComplianceType': 'NON_COMPLIANT'}):
            config_rules.extend(page['AggregateComplianceByConfigRules'])

        aggregator_info['AggregatorRules'] = config_rules
        aggregator_rule_list.append(aggregator_info)
    return aggregator_rule_list

# This function returns a list of aggregators and their tags.


def get_aggregators():
    """Returns a list of AWS Config rule aggregators"""
    aggregators = []
    for page in config_client.get_paginator('describe_configuration_aggregators').paginate():
        for aggregator in page['ConfigurationAggregators']:
            name = aggregator['ConfigurationAggregatorName']
            aggregator_arn = aggregator['ConfigurationAggregatorArn']
            tags = get_tags_for_resource(aggregator_arn)
            aggregators.append({'AggregatorName': name, 'Tags': tags})
    return aggregators

# Returns the tags for a resource


def get_tags_for_resource(arn):
    """Parameters:
    arn (string): The arn of the resource
    """
    resp = config_client.list_tags_for_resource(ResourceArn=arn)
    tags = {tags['Key']: tags['Value'] for tags in resp['Tags']}
    return tags

# Gets the contact address associated with an aggregator


def get_aggregator_email_contact(aggregator):
    if is_prod_environment():
        return aggregator['Tags']['DevOpsContact']
    return DEBUG_EMAIL_DESTINATION

# Gets aggregator BU


def get_aggregator_business_unit(aggregator):
    return aggregator['Tags']['BusinessUnit']

# This functions sends an email using SES templates


def send_email(aggregator, attachment_data):
    # Try to send the email to test.
    try:
        # Provide the contents of the email.
        to_email = get_aggregator_email_contact(aggregator)
        bu_name = get_aggregator_business_unit(aggregator)
        subject = bu_name + " AWS Accounts Compliance Report"
        body_text = "Please review the attached compliance report for " + bu_name

        msg = create_multipart_message(
            DEV_OPS_DL, [to_email], subject, body_text, None, attachment_data)
        response = ses_client.send_raw_email(
            Destinations=[to_email],
            RawMessage={'Data': msg.as_string()},
#            SourceArn=SES_SOURCE_ARN,
#            ReturnPathArn=SES_RETURNPATH_ARN,
            Source=AUDIT_EMAIL_ADDRESS
        )
    # Display an error if something goes wrong
    except ClientError as client_error:
        # TODO: Need to report this to the team so they are aware
        print(client_error.response['Error']['Message'])
    else:
        print("Email sent!")
        print("Message ID:" + response['ResponseMetadata']['RequestId'])

# Creates a an email message


def create_multipart_message(sender, recipients, title, text, html, attachment):
    multipart_content_subtype = 'alternative' if text and html else 'mixed'
    msg = MIMEMultipart(multipart_content_subtype)
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    # Record the MIME types of both parts - text/plain and text/html.
    # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
    if text:
        part = MIMEText(text, 'plain')
        msg.attach(part)
    if html:
        part = MIMEText(html, 'html')
        msg.attach(part)
    # Add attachments
    if attachment:
        att = MIMEApplication(attachment)
        att.add_header('Content-Disposition', 'attachment', filename="report.pdf")
        # Add the attachment to the parent container.
        msg.attach(att)
    return msg
