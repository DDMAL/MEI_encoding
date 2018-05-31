from gamera.core import Image

from rodan.jobs.base import RodanTask
import json
from MeiOutput import MeiOutput


class JSOMR2MEI(RodanTask):
    name = 'JSOMR to MEI'
    author = 'Noah Baxter'
    description = 'Generates an MEI file from a JSOMR file containing CC and pitch information'
    settings = {
        'title': 'JSOMR to MEI settings',
        'type': 'object',
        'required': ['MEI Version'],
        'properties': {
            'MEI Version': {
                'type': 'string',
                'default': 'N',
                'description': 'MEI file version to generate'
            }
        }
    }
    enabled = True
    category = "MEI Generation"
    interactive = False
    input_port_types = [{
        'name': 'JSOMR (JSON of CC and pitch)',
        'resource_types': ['application/json'],
        'minimum': 1,
        'maximum': 1,
        'is_list': False
    }]
    output_port_types = [{
        'name': 'MEI',
        'resource_types': ['application/mei+xml'],
        'minimum': 1,
        'maximum': 1,
        'is_list': False
    }]

    def run_my_task(self, inputs, settings, outputs):

        with open(inputs['JSOMR (JSON of CC and pitch)'][0]['resource_path'], 'r') as file:
            jsomr = json.loads(file.read())

        version = 'N'
        kwargs = {

        }
        print(version)

        # do job
        mei_obj = MeiOutput(jsomr, version, **kwargs)
        mei_string = mei_obj.run()

        # output results
        outfile_path = outputs['MEI'][0]['resource_path']
        with open(outfile_path, "w") as outfile:
            outfile.write(mei_string)

        return True
