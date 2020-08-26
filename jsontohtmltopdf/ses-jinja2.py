from jinja2 import Template
import json
template_filename = "htmltemplate.j2"
json_file = "sortbysev.json"
output_file = 'output.html'
def process_template():
    with open(template_filename, 'r') as tf:
        with open(json_file,'r') as jf:
            data = json.load(jf)
            print(type(data))
            template = Template(tf.read())
            print(template.render())
            finalData = template.render(
                aggregatorRules = data['AggregatorRules']
            )
            print('Rendered ', finalData)
            with open(output_file,'w') as of:
                of.write(finalData)

process_template()  
