from pymei import MeiDocument, MeiElement, documentToText  # , version_info
# maybe need XMLImport, xmlExport instead of docToText
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

    def __init__(self, incoming_data, version, simple, **kwargs):
        self.incoming_data = incoming_data
        self.version = version
        self.simple = simple
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

    def _generate_layer(self, parent):
        el = MeiElement("layer")
        parent.addChild(el)

        # for each non-skip glyph in this staff
        staffGlyphs = list(filter(lambda g: g['pitch']['staff'] ==
                                  el.getParent().getAttribute('n').value
                                  and g['glyph']['name'].split('.')[0] != 'skip',
                                  self.incoming_data['glyphs']))

        staffNeumes = list(filter(lambda g: g['glyph']['name'].split('.')[0] == 'neume',
                                  staffGlyphs))
        staffNotNeumes = list(filter(lambda g: g['glyph']['name'].split('.')[0] == 'neume',
                                     staffGlyphs))

        for g in staffNotNeumes:
            glyphName = g['glyph']['name'].split('.')
            # print(glyphName)
            if glyphName[0] == 'clef':
                self._generate_clef(el, g)
            elif glyphName[0] == 'custos':
                self._generate_custos(el, g)
            elif glyphName[0] == 'division':
                self._generate_division(el, g)
            elif glyphName[0] == 'accid':
                self._generate_accidental(el, g)

        if not self.simple:
            for n in staffNeumes:
                self._generate_syllable(el, n)
        else:
            avP = averagePunctum(list(filter(lambda g: g['glyph']['name'] == 'neume.punctum',
                                             self.incoming_data['glyphs'])))
            staffNeumeGroups = groupSimpleNeumes(staffNeumes, int(avP * 0.3), 8)    # 60% the width of a punctum, max 8 neume componenets attached
            for n in staffNeumeGroups:
                self._generate_simple_syllable(el, n)
            # print(staffNeumeGroups, '\n')

    def _generate_simple_syllable(self, parent, glyphs):
        el = MeiElement("syllable")
        parent.addChild(el)

        # self._generate_syl(el, glyph)
        self._generate_comment(el, ', '.join('.'.join(n['glyph']['name'].split('.')[1:]) for n in glyphs))
        self._generate_simple_neume(el, glyphs)

    def _generate_simple_neume(self, parent, glyphs):
        el = MeiElement("neume")
        parent.addChild(el)

        # zoneId = self._generate_zone(self.surface, glyphs['glyph']['bounding_box'])
        # el.addAttribute('facs', zoneId)

        # ncParams = {
        #     'pname': glyph['pitch']['note'],   # [a, b, c, d, e, f, g, unknown]
        #     'oct': glyph['pitch']['octave'],   # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        #     'intm': False,              # [u, d, s, n, su, sd]  up, down, same, unknown, same or up, same or down
        #     'liques': False,            # [Bool] elongated or curved stroke
        #     'con': False,               # [g, l, e] gapped, looped, extended  (connected to previous nc)
        #     'curve': False,             # [a, c] anticlockwise, clockwise
        #     'angled': False,            # [Bool]
        #     'hooked': False,            # [Bool]
        #     'ligature': False,          # [Bool]
        #     'tilt': False,              # [n, ne, e, se, s, sw, w, nw] direction of pen stroke

        #     'clef': glyph['pitch']['clef'].split('.')[1]    # don't atatch, just for octave calculating
        # }
        # nameParams = self._categorize_name(name)

        # # generate neume components
        # self._generate_nc(el, ncParams)  # initial note
        # if nameParams['contours'][0]:   # related notes
        #     for i in range(len(nameParams['contours'])):
        #         self._generate_nc(el, self._new_ncParams(i, nameParams, ncParams))

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
        el.addAttribute("accid", glyph['glyph']['name'].split('.')[1])

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
        # print(name)
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
                neumeContours = int(neumeVars[0]) * ['s']
                neumeIntervals = int(neumeVars[0]) * [1]
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


def averagePunctum(punctums):
    # get average width of all punctums on a page
    # as a reference length for groupings
    edges = getEdges(punctums)
    widths = list(e[1] - e[0] for e in edges)
    avg = int(sum(widths) / len(widths))
    return avg


def groupSimpleNeumes(neumes, max_distance, max_size):
    # input a horizontal staff of neumes
    # output grouped neume components

    groupedNeumes = list([n] for n in neumes)
    edges = getEdges(neumes)
    numSimpleNeumes = len(groupedNeumes)

    # basic neume component grouping rules
    autoMerge('inclinatum', 'left', groupedNeumes, edges)
    autoMerge('oblique', 'right', groupedNeumes, edges)

    autoMergeIf(max_distance, max_size, groupedNeumes, edges, getEdgeDistance(edges))

    printNeumeGroups(groupedNeumes)

    # print(list(g['glyph']['name'] for g in (gg for gg in neumes)))
    # for i, g in enumerate(neumes):
    # print(groupedNeumes)
    return groupedNeumes


def printNeumeGroups(neumeGroups):
    print('\n\nStaff')
    for ng in neumeGroups:
        print('')
        for n in ng:
            print(n['glyph']['name'])


def autoMergeIf(pixelDistance, maxSize, neumeGroup, edges, edgeDistances):
    rangeArray = range(len(neumeGroup) - 2)
    nudge = -1

    for i in rangeArray:
        if edgeDistances[i][0] < pixelDistance\
                and not len(neumeGroup[i - nudge]) + 1 > maxSize:
            mergeLeft(neumeGroup, edges, i - nudge)
            nudge += 1


def autoMerge(condition, direction, neumeGroup, edges):
    # merge every simple neume of type condition
    if direction == 'left':
        rangeArray = range(len(neumeGroup))
    else:
        rangeArray = range(len(neumeGroup) - 1, -1, -1)

    nudge = 0
    for i in rangeArray:
        n = neumeGroup[i - nudge][0]
        name = n['glyph']['name'].split('.')

        if direction == 'left'\
                and condition in name[1]\
                and i > 0:
            mergeLeft(neumeGroup, edges, i - nudge)
            nudge += 1

        elif direction == 'right'\
                and condition in name[len(name) - 1]\
                and i < rangeArray[0]:
            mergeRight(neumeGroup, edges, i - nudge)


def mergeRight(neumes, edges, pos):
    neumes[pos + 1] = neumes[pos] + neumes[pos + 1]
    edges[pos + 1][0] = edges[pos][0]
    del neumes[pos]
    del edges[pos]


def mergeLeft(neumes, edges, pos):
    neumes[pos - 1] += neumes[pos]
    edges[pos - 1][1] = edges[pos][1]
    del neumes[pos]
    del edges[pos]


def getEdges(glyphs):
    return list([g['glyph']['bounding_box']['ulx'], g['glyph']['bounding_box']['ulx'] + g['glyph']['bounding_box']['ncols']] for g in glyphs)


def getEdgeDistance(edges):
    return list([e[0] - edges[i][1], edges[i + 2][0] - e[1]] for i, e in enumerate(edges[1: -1]))


if __name__ == "__main__":

    if len(sys.argv) == 4:
        (tmp, inJSOMR, simple, image) = sys.argv
        version = 'N'
    elif len(sys.argv) == 3:
        (tmp, inJSOMR, simple) = sys.argv
        version = 'N'
        image = None
    else:
        print("incorrect usage\npython3 main.py (simple neumes) (image/path)")
        quit()

    with open(inJSOMR, 'r') as file:
        jsomr = json.loads(file.read())

    kwargs = {

    }

    mei_obj = MeiOutput(jsomr, version, simple, **kwargs)

    if image:
        mei_obj.add_Image(image)
    mei_string = mei_obj.run()

    print("\nFILE COMPLETE:\n")
    with open("output.mei", "w") as f:
        f.write(mei_string)

    # print(mei_string, '\n')
