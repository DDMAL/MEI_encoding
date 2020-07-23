import json
import unittest
import xml.etree.ElementTree as ET
import build_mei_file as bmf
from pymei import MeiElement

class TestMEIGlyphCreation(unittest.TestCase):

    punctum_xml = '<neume>  <nc/>  </neume>'
    podastus2_xml = '<neume>  <nc/>  <nc intm="1S"/> </neume>'
    clefc_xml = '<clef line="4" oct="None" pname="None" shape="C" />'
    dummy_surface = MeiElement('surface')

    punctum_glyph = {'bounding_box': {'lrx': 1010, 'lry': 1010, 'ulx': 1000, 'uly': 1000},
     # 'clef': 'clef.c',
     # 'clef_pos': '7',
     'name': 'neume.punctum',
     'note': 'g',
     'octave': '2',
     'staff': '3',
     'strt_pos': '10',
     'system_begin': False}

    def test_punctum_element(self):
        xml = ET.fromstring(self.punctum_xml)
        el = bmf.create_primitive_element(xml, self.punctum_glyph, self.dummy_surface)

        # should return a simple MeiElement with a note, an octave, and a facsimile
        self.assertEqual(type(el), MeiElement)
        self.assertEqual(el.getAttribute('pname').value, self.punctum_glyph['note'])
        self.assertEqual(el.getAttribute('oct').value, self.punctum_glyph['octave'])

        exp_atts = set(['pname', 'oct', 'facs'])
        res_atts = set([x.name for x in el.attributes])
        self.assertEqual(exp_atts, res_atts)

    #
    # def test_isupper(self):
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())
    #
    # def test_split(self):
    #     s = 'hello world'
    #     self.assertEqual(s.split(), ['hello', 'world'])
    #     # check that s.split fails when the separator is not a string
    #     with self.assertRaises(TypeError):
    #         s.split(2)


if __name__ == '__main__':
    unittest.main()
