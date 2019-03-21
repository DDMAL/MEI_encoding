from rodan.jobs.base import RodanTask

from gamera.core import Image
from MeiOutput import MeiOutput
from addSyllableText import add_syllables_to_doc
import json


class JSOMR2MEI(RodanTask):
    name = 'JSOMR to MEI'
    author = 'Noah Baxter'
    description = 'Generates an MEI file from a JSOMR file containing CC and pitch information'
    enabled = True
    category = "Encoding"
    interactive = False

    settings = {
        'title': 'JSOMR to MEI Settings',
        'type': 'object',
        'required': ['MEI Version', 'Maximum Neume Spacing', 'Neume Grouping Size'],
        'properties': {
            'MEI Version': {
                'enum': ['4.0.0', '3.9.9'],
                'type': 'string',
                'default': '3.9.9',
                'description': 'Specifies the MEI version, 3.9.9 is the old unofficial MEI standard used by Neon',
            },
            'Maximum Neume Spacing': {
                'type': 'number',
                'default': 0.3,
                'minimum': 0.0,
                'maximum': 100.0,
                'description': 'The maximum spacing allowed between two neume shapes when grouping into syllables, 1.0 is the length of the average punctum',
            },
            'Neume Grouping Size': {
                'type': 'integer',
                'default': 8,
                'minimum': 1,
                'maximum': 99999,
                'description': 'The maximum number of neume shapes that can be grouped into a syllable',
            }
        }
    }

    input_port_types = [{
        'name': 'JSOMR',
        'resource_types': ['application/json'],
        'minimum': 1,
        'maximum': 1,
        'is_list': False
    }, {
        'name': 'Text Alignment JSON',
        'resource_types': ['application/json'],
        'minimum': 1,
        'maximum': 1,
        'is_list': False
    }
    ]

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

        with open(inputs['Text Alignment JSON'][0]['resource_path'], 'r') as file:
            syls_json = json.loads(file.read())

        kwargs = {
            'mei_version': str(settings['MEI Version']),
            'max_neume_spacing': settings['Maximum Neume Spacing'],
            'max_group_size': settings['Neume Grouping Size'],
        }

        # parse JSOMR into an mei document
        mei_obj = MeiOutput(jsomr, **kwargs)
        mei_doc = mei_obj.run()

        # add syllable information into mei document
        mei_string = add_syllables_to_doc(mei_doc, syls_json, return_text=True)

        # write document to file
        outfile_path = outputs['MEI'][0]['resource_path']
        with open(outfile_path, 'w') as file:
            file.write(mei_string)

        return True
