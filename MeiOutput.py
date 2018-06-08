from pymei import MeiDocument, MeiElement, documentToText  # , version_info
import sys
import json


class MeiOutput(object):

    SCALE = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

    CONTOURS = {
        'pes': ['u'],
        'clivis': ['d'],
        'pressus': ['s', 'd'],
        'scandicus': ['u', 'u'],
        'climacus': ['d', 'd'],
        'torculus': ['u', 'd'],
        'porrectus': ['d', 'u'],
    }

    def __init__(self, incoming_data, version, **kwargs):
        self.incoming_data = incoming_data
        self.version = version
        self.surface = 0
        self.original_image = ''

    def run(self):
        # print("version info", version_info)
        if self.version == 'N':
            return self._conversion()
        else:
            print('not valid MEI version')

    def add_Image(self, image):
        self.original_image = image

    def _conversion(self):
        print('begin conversion')

        doc = self._createDoc()

        return documentToText(doc)

    def _createDoc(self):
        # initialize basic universal attributes of any MEI document
        doc = MeiDocument()

        self._generate_mei(doc)
        # self._generate_meiCorpus(doc)     # unnecesary

        return doc

    def _generate_mei(self, parent):
        el = MeiElement("mei")
        parent.root = el

        el.addAttribute("meiversion", self.version)

        self._generate_meiHead(el)
        self._generate_music(el)

    def _generate_meiHead(self, parent):
        el = MeiElement("meiHead")
        parent.addChild(el)

    def _generate_music(self, parent):
        el = MeiElement("music")
        parent.addChild(el)

        # self._generate_front(el)          # unnecesary
        self._generate_facsimile(el)
        self._generate_body(el)
        # self._generate_back(el)           # unnecesary

    def _generate_facsimile(self, parent):
        el = MeiElement("facsimile")
        parent.addChild(el)

        self._generate_surface(el)

    def _generate_surface(self, parent):
        el = MeiElement("surface")
        parent.addChild(el)

        self._generate_graphic(el)
        self.surface = el

    def _generate_graphic(self, parent):
        el = MeiElement("graphic")
        parent.addChild(el)

        el.addAttribute('xlink:href', str(self.original_image))

    def _generate_body(self, parent):
        el = MeiElement("body")
        parent.addChild(el)

        self._generate_mdiv(el)

    def _generate_mdiv(self, parent):
        # LATER CHECK FOR SUBDIVS, multi movement pieces, etc.
        el = MeiElement("mdiv")
        parent.addChild(el)

        self._generate_score(el)

    def _generate_score(self, parent):
        el = MeiElement("score")
        parent.addChild(el)

        self._generate_scoreDef(el)
        self._generate_section(el)

    def _generate_scoreDef(self, parent):
        el = MeiElement("scoreDef")
        parent.addChild(el)

        self._generate_staffGrp(el)

    def _generate_section(self, parent):
        el = MeiElement("section")
        parent.addChild(el)

        # find number of staves
        for s in self.incoming_data['staves']:
            self._generate_staff(el, s)     # generate multiple staves

    def _generate_staffGrp(self, parent):
        el = MeiElement("staffGrp")
        parent.addChild(el)

        self._generate_staffDef(el)

    def _generate_staffDef(self, parent):
        el = MeiElement("staffDef")
        parent.addChild(el)

        # FIX HARDCODING
        el.addAttribute('n', '1')
        el.addAttribute('lines', '4')
        el.addAttribute('notationtype', 'neume')

    def _generate_staff(self, parent, staff):
        el = MeiElement("staff")
        parent.addChild(el)

        zoneId = self._generate_zone(self.surface, staff['bounding_box'])
        el.addAttribute('facs', zoneId)
        el.addAttribute('n', str(staff['staff_no']))
        el.addAttribute('lines', str(staff['num_lines']))

        self._generate_layer(el)
        # neume only get 1 layer per staff, worth verifying later

    def _generate_layer(self, parent):
        el = MeiElement("layer")
        parent.addChild(el)

        # for each glyph in this staff, make a syllable
        localGlyphs = list(filter(lambda g: g['pitch']['staff'] ==
                                  el.getParent().getAttribute('n').value, self.incoming_data['glyphs']))

        for g in localGlyphs:
            glyphName = g['glyph']['name'].split('.')
            if glyphName[0] == 'clef':
                self._generate_clef(el, g)
            elif glyphName[0] == 'custos':
                self._generate_custos(el, g)
            elif glyphName[0] == 'division':
                self._generate_division(el, g)
            elif glyphName[0] == 'accidental':
                self._generate_accidental(el, g)
            else:
                self._generate_syllable(el, g)

    def _generate_clef(self, parent, glyph):
        el = MeiElement("clef")
        parent.addChild(el)

        zoneId = self._generate_zone(self.surface, glyph['glyph']['bounding_box'])
        el.addAttribute('facs', zoneId)
        el.addAttribute('shape', glyph['glyph']['name'].split('.')[1].upper())
        el.addAttribute('line', glyph['pitch']['strt_pos'])

    def _generate_custos(self, parent, glyph):
        el = MeiElement("custos")
        parent.addChild(el)

        zoneId = self._generate_zone(self.surface, glyph['glyph']['bounding_box'])
        el.addAttribute('facs', zoneId)
        el.addAttribute("oct", glyph['pitch']['octave'])
        el.addAttribute("pname", glyph['pitch']['note'])

    def _generate_division(self, parent, glyph):
        el = MeiElement("division")
        parent.addChild(el)

        zoneId = self._generate_zone(self.surface, glyph['glyph']['bounding_box'])
        el.addAttribute('facs', zoneId)
        el.addAttribute("form", glyph['glyph']['name'].split('.')[1])

    def _generate_accidental(self, parent, glyph):
        el = MeiElement("accid")
        parent.addChild(el)

        zoneId = self._generate_zone(self.surface, glyph['glyph']['bounding_box'])
        el.addAttribute('facs', zoneId)
        el.addAttribute("type", glyph['glyph']['name'].split('.')[1])

    def _generate_syllable(self, parent, glyph):
        el = MeiElement("syllable")
        parent.addChild(el)

        # self._generate_syl(el, glyph)
        self._generate_comment(el, glyph['glyph']['name'])
        self._generate_neume(el, glyph)     # this may need to change

    def _generate_syl(self, parent, glyph):
        el = MeiElement("syl")
        parent.addChild(el)

        # self._generate_(el)

    def _generate_comment(self, parent, text):
        el = MeiElement("_comment")
        el.setValue(text)
        parent.addChild(el)

    def _generate_neume(self, parent, glyph):
        el = MeiElement("neume")
        parent.addChild(el)

        zoneId = self._generate_zone(self.surface, glyph['glyph']['bounding_box'])
        el.addAttribute('facs', zoneId)

        name = glyph['glyph']['name'].split('.')
        ncParams = {
            'pname': glyph['pitch']['note'],   # [a, b, c, d, e, f, g, unknown]
            'oct': glyph['pitch']['octave'],   # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            'intm': False,              # [u, d, s, n, su, sd]  up, down, same, unknown, same or up, same or down
            'liques': False,            # [Bool] elongated or curved stroke
            'con': False,               # [g, l, e] gapped, looped, extended  (connected to previous nc)
            'curve': False,             # [a, c] anticlockwise, clockwise
            'angled': False,            # [Bool]
            'hooked': False,            # [Bool]
            'ligature': False,          # [Bool]
            'tilt': False,              # [n, ne, e, se, s, sw, w, nw] direction of pen stroke

            'clef': glyph['pitch']['clef'].split('.')[1]    # don't atatch, just for octave calculating
        }
        nameParams = self._categorize_name(name)

        # generate neume components
        self._generate_nc(el, ncParams)  # initial note
        if nameParams['contours'][0]:   # related notes
            for i in range(len(nameParams['contours'])):
                self._generate_nc(el, self._new_ncParams(i, nameParams, ncParams))

    def _generate_nc(self, parent, kwargs):
        el = MeiElement("nc")
        parent.addChild(el)

        for name, value in kwargs.items():
            if name == 'clef':
                pass
            elif name == 'oct':  # this is a super lazy fix...
                el.addAttribute(name, str(int(value) - 1))
            elif kwargs[name]:
                el.addAttribute(name, value)

    def _generate_zone(self, parent, bounding_box):

        (nrows, ulx, uly, ncols) = bounding_box.values()

        el = MeiElement("zone")
        parent.addChild(el)

        el.addAttribute("ulx", str(ulx))
        el.addAttribute("uly", str(uly))
        el.addAttribute("lrx", str(ulx + ncols))
        el.addAttribute("lry", str(uly + nrows))

        return el.getId()   # returns the facsimile reference for neumes, etc.

    def _findRelativeNote(self, startNote, startOctave, contour, interval, clef):
        # print(startOctave, startNote, contour, interval)

        startOctave = int(startOctave)
        interval = int(interval) - 1  # because intervals are 1 note off

        # rotate scale based on clef
        rot = self.SCALE.index(clef)
        SCALE = self.SCALE[rot:] + self.SCALE[:rot]

        if contour == 'u':      # upwards
            newOctave = startOctave + \
                int((SCALE.index(startNote) + interval) / len(SCALE))
            newNote = SCALE[(SCALE.index(startNote) + interval) % len(SCALE)]

        elif contour == 'd':    # downwards
            newOctave = startOctave - \
                int((len(SCALE) - SCALE.index(startNote) - 1 + interval) / len(SCALE))
            newNote = SCALE[(SCALE.index(startNote) - interval) % len(SCALE)]

        elif contour == 's':   # repetition
            newOctave = startOctave
            newNote = startNote

        return [newNote, str(newOctave)]

    def _new_ncParams(self, i, nameParams, ncParams):
        newPitch = self._findRelativeNote(
            ncParams['pname'],
            ncParams['oct'],
            nameParams['contours'][i],
            nameParams['intervals'][i],
            ncParams['clef'])

        ncParams['intm'] = nameParams['contours'][i]
        ncParams['pname'] = newPitch[0]
        ncParams['oct'] = newPitch[1]

        return ncParams

    def _categorize_name(self, name):
        neumeName = name[1]
        if len(name) < 3:
            neumeStyle = None
            neumeMod = None
            neumeStyle2 = None
            neumeVars = [None]

        elif name[2] in ['a', 'b']:
            neumeStyle = name[2]
            if name[3] in ['flexus', 'resupinus', 'subpunctis', 'repeated']:
                neumeMod = name[3]
                if name[4] in ['a', 'b']:
                    neumeStyle2 = name[4]
                    neumeVars = name[5:]
                else:
                    neumeStyle2 = None
                    neumeVars = name[4:]
            else:
                neumeMod = None
                neumeStyle2 = None
                neumeVars = name[3:]

        elif name[2] in ['flexus', 'resupinus', 'subpunctis', 'repeated']:
            neumeMod = name[2]
            neumeStyle2 = None
            if name[3] in ['a', 'b']:
                neumeStyle = name[3]
                neumeVars = name[4:]
            else:
                neumeStyle = None
                neumeVars = name[3:]

        else:
            neumeStyle = None
            neumeMod = None
            neumeStyle2 = None
            neumeVars = name[2:]

        # get contours and intervals
        if neumeMod or neumeName == 'compound':   # explicit contours,      u2.d2
            if neumeMod == 'repeated':
                neumeContours = neumeVars[0] * ['s']
                neumeIntervals = neumeVars[0] * [1]
            else:
                neumeContours = list(c[0] for c in neumeVars)
                neumeIntervals = list(int(''.join(c[1:])) for c in neumeVars)

        elif neumeName in self.CONTOURS:          # predefined contours,    2.2.3
            neumeContours = self.CONTOURS[neumeName]
            neumeIntervals = list(int(i) for i in neumeVars)
            for i, c in enumerate(neumeContours):   # if missing unison intervals
                if c == 's':
                    neumeIntervals.insert(0, 1)

        else:
            neumeContours = [None]
            neumeIntervals = [None]

        nameParams = {
            'name': neumeName,
            'style': neumeStyle,
            'mod': neumeMod,
            'style2': neumeStyle2,
            'contours': neumeContours,
            'intervals': neumeIntervals,
        }

        return nameParams


if __name__ == "__main__":

    if len(sys.argv) == 4:
        (tmp, inJSOMR, version, image) = sys.argv
    elif len(sys.argv) == 3:
        (tmp, inJSOMR, image) = sys.argv
        version = 'N'
    elif len(sys.argv) == 2:
        (tmp, inJSOMR) = sys.argv
        version = 'N'
        image = None
    else:
        print("incorrect usage\npython3 main.py path (version)")
        quit()

    with open(inJSOMR, 'r') as file:
        jsomr = json.loads(file.read())

    kwargs = {

    }

    mei_obj = MeiOutput(jsomr, version, **kwargs)
    if image:
        mei_obj.add_Image(image)
    mei_string = mei_obj.run()

    print("\nFILE COMPLETE:\n")
    with open("output.mei", "w") as f:
        f.write(mei_string)

    # print(mei_string, '\n')
