from gamera.core import Image

from rodan.jobs.base import RodanTask
import json

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
                'type': 'integer',
                'default': 3,
                'minimum': 0,
                'maximum': 4,
                'description': 'MEI file version to generate'
            }
        } 
    }
    enabled = True
    category = "Test"
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
        print jsomr

        mei_version = settings['MEI Version']
        print mei_version
       
        kwargs = {

        }

        output_mei = jsomr

        outfile_path = outputs['MEI'][0]['resource_path']
        outfile = open(outfile_path, "w")
        outfile.write(json.dumps(output_mei))
        outfile.close()
        return True
