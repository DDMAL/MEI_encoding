from rodan.jobs.base import RodanTask

from gamera.core import Image
import build_mei_file as bm
import parse_classifier_table as pct
from addSyllableText import add_syllables_to_doc
import json


class Mei-encoding(RodanTask):
    name = 'Mei-encoding'
    author = 'Tim de Reuse'
    description = 'Builds an MEI file from pitchfinding information and transcript alignment results.'
    enabled = True
    category = "Encoding"
    interactive = False

    settings = {
        'title': 'Mei Encoding Settings',
        'type': 'object',
        'required': ['Maximum Neume Spacing'],
        'properties': {
            'Maximum Neume Spacing': {
                'type': 'number',
                'default': 1.0,
                'minimum': 0.0,
                'maximum': 20.0,
                'description': 'The spacing allowed between two neume components when grouping into neumes, where 1.0 is the width of the average punctum. At 0, neume components will not be merged together.',
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
        'minimum': 0,
        'maximum': 1,
        'is_list': False
    }, {
        'name': 'MEI Mapping CSV',
        'resource_types': ['text/csv'],
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
        print('loading jsomr')
        with open(inputs['JSOMR'][0]['resource_path'], 'r') as file:
            jsomr = json.loads(file.read())

        print('loading json alignment')
        try:
            with open(inputs['Text Alignment JSON'][0]['resource_path'], 'r') as file:
                syls = json.loads(file.read())
        except IOError:
            syls = None

        print('fetching classifier table')
        classifier_table = pct.fetch_table_from_csv(inputs['Text Alignment JSON'][0]['resource_path'])

        print('processing doc')
        spacing = settings['Neume Component Spacing']
        meiDoc = bm.process(jsomr, syls, classifier_table, spacing)

        print('writing doc')
        # write document to file
        outfile_path = outputs['MEI'][0]['resource_path']
        with open(outfile_path, 'w') as file:
            file.write(mei_string)

        return True
