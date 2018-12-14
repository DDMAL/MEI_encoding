from rodan.jobs.base import RodanTask

from gamera.core import Image
from MeiOutput import MeiOutput
import json


class JSOMR2MEI(RodanTask):
    name = 'JSOMR to MEI'
    author = 'Noah Baxter'
    description = 'Generates an MEI file from a JSOMR file containing CC and pitch information'
    settings = {
        'title': 'JSOMR to MEI settings',
        'type': 'object',
        'required': ['Clasification Spec'],
        'properties': {
            'Clasification Spec': {
                'enum': ['Neume Components', 'Neume Mappings'],
                'type': 'string',
                'default': 'Neume Components',
                'description': 'Specifies the naming, grouping, and spliting conventions used for glyph classification'

            }
        }
    }
    enabled = True
    category = "Encoding"
    interactive = False
    input_port_types = [{
        'name': 'JSOMR',
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

        with open(inputs['JSOMR'][0]['resource_path'], 'r') as file:
            jsomr = json.loads(file.read())
        print jsomr

        kwargs = {
            'version': '4.0.0',

            'max_neume_spacing': 0.3,
            'max_group_size': 8,
        }

        # do job
        mei_obj = MeiOutput(jsomr, **kwargs)
        mei_string = mei_obj.run()

        outfile_path = outputs['MEI'][0]['resource_path']
        outfile = open(outfile_path, "w")
        outfile.write(json.dumps(mei_string))
        outfile.close()
        return True
