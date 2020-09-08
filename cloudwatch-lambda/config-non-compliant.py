import boto3
import os

client = boto3.client('ec2')
sesClient = boto3.client('ses')

SOURCE_EMAIL = os.environ['SOURCE_EMAIL']
DEST_EMAIL = os.environ['DEST_EMAIL']

def lambda_handler(event,context):

   complianceType =  event['detail']['newEvaluationResult']['complianceType']
   
   if complianceType == "NON_COMPLIANT":
       resourceId = event['detail']['resourceId']
       awsRegion = event['detail']['awsRegion']
       awsAccountId = event['detail']['awsAccountId']
       resourceType =  event['detail']['newEvaluationResult']['evaluationResultIdentifier']['evaluationResultQualifier']['resourceType']
       emailBody = f"""
        Resource ID : {0}
        Resource Type : {1}
        Account Id : {2}
        Region : {3}
       """.format(resourceId,resourceType,awsAccountId,awsRegion)
       sesClient.send_email(
           Source = SOURCE_EMAIL,
           Destination={
            'ToAddresses': [
                DEST_EMAIL
            ]
          },
          Message={
            'Subject': {
                'Data': 'Resource Non Compliant',
                'Charset': 'utf-8'
            },
            'Body': {
                'Text': {
                    'Data': emailBody,
                    'Charset': 'utf-8'
                }
            }
          }
        )
