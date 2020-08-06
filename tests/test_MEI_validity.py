from lxml import etree
import unittest
import build_mei_file as bmf
import json
import parse_classifier_table as pct
from StringIO import StringIO


class TestMEIValidity(unittest.TestCase):

    # to be replaced with the neume schema when the clef/custos issue is resolved (hopefully)
    rng_path = './tests/resources/mei-all.rng'
    classifier_path = './tests/resources/square_notation_basic_classifier.csv'
    syls_path = './tests/resources/syls_salzinnes_400.json'
    pitches_path = './tests/resources/pitches_salzinnes_400.json'

    def setUp(self):
        with open(self.pitches_path) as file:
            self.jsomr = json.loads(file.read())
        with open(self.syls_path) as file:
            self.syls = json.loads(file.read())
        self.classifier = pct.fetch_table_from_csv(self.classifier_path)

    def test_build_mei(self):

        mei_text = bmf.process(self.jsomr, self.syls, self.classifier, width_mult=1, verbose=False)
        mei_xml = etree.parse(StringIO(mei_text))

        with open(self.rng_path) as file:
            relaxng_doc = etree.parse(file)
        rng = etree.RelaxNG(relaxng_doc)

        self.assertTrue(rng.validate(mei_xml))


if __name__ == '__main__':
    unittest.main()
