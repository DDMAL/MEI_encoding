import xml.etree.ElementTree as ET
import numpy as np
import json
import parse_classifier_table as pct
import matplotlib.pyplot as plt
from pymei import MeiDocument, MeiElement, MeiAttribute, documentToText, documentToFile

f_ind = 56
classifier_fname = 'test_classifier.xlsx'
fname = 'salzinnes_{:0>3}'.format(f_ind)
inJSOMR = './jsomr-split/pitches_{}.json'.format(fname)
in_syls = './syl_json/{}.json'.format(fname)
in_png = '/Users/tim/Desktop/PNG_compressed/CF-{:0>3}.png'.format(f_ind)


with open(inJSOMR, 'r') as file:
    jsomr = json.loads(file.read())
with open(in_syls) as file:
    syls = json.loads(file.read())

glyphs = jsomr['glyphs']
syl_boxes = syls['syl_boxes']
median_line_spacing = syls['median_line_spacing']

# sort glyphs in lexicographical order by staff #, left to right
glyphs.sort(key=lambda x: (int(x['pitch']['staff']), int(x['pitch']['offset'])))

glyphs_pos = 0
num_glyphs = len(glyphs)

# MAKE SURE THAT SYL_BOXES IS SORTED IN READING ORDER! (include more info in json)
pairs = []
starts = []
last_used = 0
for box in syl_boxes:

    # assign each syllable to an ANCHOR GLYPH
    above_glyphs = [
        g for g in glyphs[last_used:] if
        (box['ul'][1] - median_line_spacing < g['glyph']['bounding_box']['uly'] < box['ul'][1]) and
        (box['ul'][0] < g['glyph']['bounding_box']['ulx'] + g['glyph']['bounding_box']['ncols'] // 2)
        ]

    print(last_used, box)

    if not above_glyphs:
        starts.append(last_used)
        continue

    nearest_glyph = min(above_glyphs, key=lambda g: g['glyph']['bounding_box']['ulx'])
    print(nearest_glyph['glyph']['bounding_box'])
    starts.append(glyphs.index(nearest_glyph))
    last_used = max(starts)

starts.append(len(glyphs))
for i in range(len(starts) - 1):
    pairs.append((syl_boxes[i], glyphs[starts[i]:starts[i+1]]))


def draw_neume_alignment(in_png, pairs, text_size=60):
    import PIL
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    fnt = ImageFont.truetype('FreeMono.ttf', text_size)
    im = Image.open(in_png).convert('RGB')
    draw = ImageDraw.Draw(im)

    last_text = None
    for tb, gbs in pairs:

        bbs = [
            g['glyph']['bounding_box'] for g in gbs
            if 'neume' in g['glyph']['name']
            ]

        draw.rectangle(tb['ul'] + tb['lr'], outline='black')
        draw.text(tb['ul'], tb['syl'], font=fnt, fill='gray')
        for bb in bbs:
            pt1 = (bb['ulx'] + bb['ncols'] // 2, bb['uly'] + bb['nrows'] // 2)
            pt2 = ((tb['ul'][0] + tb['lr'][0]) // 2, (tb['ul'][1] + tb['lr'][1]) // 2)
            draw.line((pt1, pt2), fill='black', width=5)
    im.show()


def add_attributes_to_element(el, add):
    for key in add.keys():
        if not add[key] or add[key] == 'None':
            continue
        el.addAttribute(key, add[key])
    return el


def create_primitive_element(xml, glyph, surface):
    name = str(glyph['glyph']['name'])
    if name.index('.'):
        name = name[:name.index('.')]

    res = MeiElement(name)
    attribs = xml.attrib

    attribs['line'] = str(glyph['pitch']['strt_pos'])
    attribs['octave'] = str(glyph['pitch']['octave'])
    attribs['pname'] = str(glyph['pitch']['note'])
    res = add_attributes_to_element(res, attribs)

    zoneId = generate_zone(surface, glyph['glyph']['bounding_box'])
    res.addAttribute('facs', zoneId)
    return res


def glyph_to_element(classifier, glyph, surface):
    '''
    translates a glyph as output by the pitchfinder into an MEI element, registering bounding boxes
    in the given surface.

    currently the assumption is that no MEI information in the given classifier is more than one
    level deep - that is, everything is either a single element (clef, custos) or the child of a
    single element (neumes).
    '''
    name = str(glyph['glyph']['name'])
    xml = classifier[name]
    if name.index('.'):
        name = name[:name.index('.')]

    # if this is an element with no children, then just apply a pitch and position to it
    if not list(xml):
        return create_primitive_element(xml, glyph, surface)

    # else, this element has at least one child (is a neume)
    ncs = list(xml)
    els = [create_primitive_element(nc, glyph, surface) for nc in ncs]
    parent = MeiElement(xml.tag)
    parent.setChildren(els)

    if len(els) < 2:
        return parent

    # if there's more than one element, must resolve intervals between ncs
    for i in range(1, len(els)):
        prev_nc = parent.children[i - 1]
        cur_nc = parent.children[i]
        new_pname, new_octave = resolve_interval(prev_nc, cur_nc)
        cur_nc.addAttribute('pname', new_pname)
        cur_nc.addAttribute('octave', new_octave)

    return parent


def resolve_interval(prev_nc, cur_nc):
    interval = cur_nc.getAttribute('intm').value
    print(interval)
    try:
        interval = interval.lower().replace('s', '')
        interval = int(interval)
    except ValueError:
        interval = 0
    except AttributeError:
        interval = 0

    starting_pitch = prev_nc.getAttribute('pname').value
    starting_octave = prev_nc.getAttribute('octave').value
    new_octave = starting_octave

    new_pitch = ord(starting_pitch) - ord('a') + interval

    if new_pitch >= 7:
        new_octave += 1
    elif new_pitch < 0:
        new_octave -= 1

    new_pitch %= 7
    new_pname = chr(new_pitch + ord('a'))

    return new_pname, new_octave


def generate_zone(surface, bb):
    return str(np.random.randint(0, 10e10))


# draw_neume_alignment(in_png, pairs)
classifier = pct.fetch_table(classifier_fname)

meiDoc = MeiDocument("4.0.0")

mei = MeiElement("mei")
mei.addAttribute("meiversion", "4.0.0")
meiDoc.root = mei

# placeholder meiHead
meihead = MeiElement('meiHead')
mei.addChild(meihead)
fileDesc = MeiElement('fileDesc')
meihead.addChild(fileDesc)
titleSt = MeiElement('titleStmt')
fileDesc.addChild(titleSt)
title = MeiElement('title')
titleSt.addChild(title)
title.setValue('MEI Encoding Output')
pubStmt = MeiElement('pubStmt')
fileDesc.addChild(pubStmt)

music = MeiElement("music")
mei.addChild(music)

facs = MeiElement("facsimile")
music.addChild(facs)

surface = MeiElement("surface")
facs.addChild(surface)

body = MeiElement('body')
music.addChild(body)

mdiv = MeiElement('mdiv')
body.addChild(mdiv)

score = MeiElement('score')
mdiv.addChild(score)

scoreDef = MeiElement('scoreDef')
score.addChild(scoreDef)

staffGrp = MeiElement('staffGrp')
scoreDef.addChild(staffGrp)

staffDef = MeiElement('staffDef')
staffGrp.addChild(staffDef)

# these hardcoded attributes define a single staff with 4 lines, neume notation, with a default c clef
staffDef.addAttribute('n', '1')
staffDef.addAttribute('lines', '4')
staffDef.addAttribute('notationtype', 'neume')
staffDef.addAttribute('clef.line', '3')
staffDef.addAttribute('clef.shape', 'C')

section = MeiElement('section')
score.addChild(section)

staff = MeiElement('staff')
section.addChild(staff)

layer = MeiElement('layer')
staff.addChild(layer)

for tb, gs in pairs:
    cur_syllable = MeiElement('syllable')
    staff.addChild(cur_syllable)
    syl = MeiElement('syl')
    syl.setValue(str(tb['syl']))

    for glyph in gs:
        new_el = glyph_to_element(classifier, glyph)


documentToFile(meiDoc, 'testexport.mei')
