import json


def read_json_file():
  with open('sortbysev.json', 'r') as fp:
    return json.load(fp)

def main_method():
  json_data = read_json_file()
  json_data = json_data.get('AggregatorRules')
  paragraph = ""
  for item in json_data:
    paragraph += (
      '<h2>Rule: {}</h2>'
      '<p>Severity: {}</p>'
      '<p>Description: {}</p>'
    ).format(item.get('rule'), item.get('severity'), item.get('description'))
    resources = item.get('resources')
    table_row = ""
    for resource in resources:
      table_row += ('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>').format(\
        resource.get("ResourceId"), resource.get("ResourceType"),\
        resource.get("AccountId"), resource.get("AwsRegion"))
    paragraph += ('<table><thead><tr><th>Resource Id</th><th>Resource Type</th>'
      '<th>Account Id</th><th>Region</th></tr></thead><tbody>{}</tbody></table></body></html>').format(table_row)
  html_code = """
    <!DOCTYPE html>
    <html>

    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <style>
            table {
                border: 1px solid #1C6EA4;
                background-color: #EFEFEF;
                width: 100%;
                text-align: left;
                border-collapse: collapse;
                font-family: Tahoma, Geneva, sans-serif;
                font-size: 14px;
                letter-spacing: 2px;
                word-spacing: 2px;
                color: #000000;
                font-weight: normal;
                text-decoration: none;
                font-style: normal;
                font-variant: normal;
                text-transform: none;
            }
            
            table td,
            table th {
                border: 1px solid #AAAAAA;
                padding: 3px 2px;
            }
            
            table tbody td {
                font-size: 14px;
            }
            
            table tr:nth-child(even) {
                background: #D0E4F5;
            }
            
            table thead {
                background: #2591D8;
                background: -moz-linear-gradient(top, #5bace2 0%, #3a9cdc 66%, #2591D8 100%);
                background: -webkit-linear-gradient(top, #5bace2 0%, #3a9cdc 66%, #2591D8 100%);
                background: linear-gradient(to bottom, #5bace2 0%, #3a9cdc 66%, #2591D8 100%);
                border-bottom: 2px solid #444444;
            }
            
            table thead th {
                font-size: 14px;
                font-weight: bold;
                color: #FFFFFF;
                border-left: 2px solid #D0E4F5;
            }
            
            table thead th:first-child {
                border-left: none;
            }
            
            .High {
                color: crimson
            }
        </style>
    </head>

    <body>
        <p></p>
        <div>
          <p>Please review the following compliance report for your AWS accounts and take action as necessary.
          </p>
          <p>You can also log into the AWS Auditing account through the AWS Console via Okta to review the up-to-date compliance status of your AWS accounts.
          </p>
          <p>If you have any questions please contact Team Igneous on MS Team or by replying to this email.
          </p>
          <p>Thank you.</p>
        </div>
        """
  html_code += paragraph
  print(html_code)


main_method()