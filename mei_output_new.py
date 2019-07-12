import xml.etree.ElementTree as ET
import numpy as np
import json
import parse_classifier_table as pct
import matplotlib.pyplot as plt
from pymei import MeiDocument, MeiElement, MeiAttribute, documentToText, documentToFile
from itertools import groupby

def neume_to_lyric_alignment(glyphs, syl_boxes, median_line_spacing):

    glyphs_pos = 0
    num_glyphs = len(glyphs)

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

        if not above_glyphs:
            starts.append(last_used)
            continue

        nearest_glyph = min(above_glyphs, key=lambda g: g['glyph']['bounding_box']['ulx'])
        # print(nearest_glyph['glyph']['bounding_box'])
        starts.append(glyphs.index(nearest_glyph))
        last_used = max(starts)

    starts.append(len(glyphs))
    for i in range(len(starts) - 1):
        pairs.append((glyphs[starts[i]:starts[i+1]], syl_boxes[i]))

    return pairs


def draw_neume_alignment(in_png, pairs, text_size=60):
    import PIL
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    fnt = ImageFont.truetype('FreeMono.ttf', text_size)
    im = Image.open(in_png).convert('RGB')
    draw = ImageDraw.Draw(im)

    last_text = None
    for gb, tb in pairs:
        if not tb:
            continue
        bb = gb['glyph']['bounding_box']

        draw.rectangle(tb['ul'] + tb['lr'], outline='black')
        draw.text(tb['ul'], tb['syl'], font=fnt, fill='gray')
        pt1 = (bb['ulx'] + bb['ncols'] // 2, bb['uly'] + bb['nrows'] // 2)
        pt2 = ((tb['ul'][0] + tb['lr'][0]) // 2, (tb['ul'][1] + tb['lr'][1]) // 2)
        draw.line((pt1, pt2), fill='black', width=5)
    im.show()


def generate_base_document():

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

    return meiDoc, surface, layer


def add_attributes_to_element(el, add):
    for key in add.keys():
        if not add[key] or add[key] == 'None':
            continue
        el.addAttribute(key, str(add[key]))
    return el


def create_primitive_element(xml, glyph, surface):
    '''
    creates
    '''
    res = MeiElement(xml.tag)
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
    try:
        name = name[:name.index('.')]
    except ValueError:
        pass

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
        cur_nc.removeAttribute('intm')

    return parent


def resolve_interval(prev_nc, cur_nc):

    scale = ['c', 'd', 'e', 'f', 'g', 'a', 'b']

    interval = cur_nc.getAttribute('intm').value
    try:
        interval = interval.lower().replace('s', '')
        interval = int(interval)
    except ValueError:
        interval = 0
    except AttributeError:
        interval = 0

    starting_pitch = prev_nc.getAttribute('pname').value
    starting_octave = prev_nc.getAttribute('octave').value
    end_octave = starting_octave

    try:
        start_index = scale.index(starting_pitch)
    except ValueError:
        print('pname {} is not in scale {}!'.format(starting_pitch, scale))
        return

    end_idx = start_index + interval

    if end_idx >= len(scale):
        end_octave += 1
    elif end_idx < 0:
        end_octave -= 1

    end_idx %= len(scale)
    end_pname = scale[end_idx]

    return end_pname, end_octave


def generate_zone(surface, bb):
    el = MeiElement('zone')
    surface.addChild(el)

    attribs = {
        'ulx': bb['ulx'],
        'uly': bb['uly'],
        'lrx': bb['ulx'] + bb['ncols'],
        'lry': bb['uly'] + bb['nrows'],
    }

    el = add_attributes_to_element(el, attribs)
    return el.getId()


def build_mei(glyphs, syl_boxes, staves, classifier, median_line_spacing):

    # MAKE SURE THAT SYL_BOXES IS SORTED IN READING ORDER! (include more info in json)
    # sort glyphs in lexicographical order by staff #, left to right
    glyphs.sort(key=lambda x: (int(x['pitch']['staff']), int(x['pitch']['offset'])))

    avg_glyph_width = np.mean([x['glyph']['bounding_box']['ncols'] for x in glyphs])

    # add flag to every glyph denoting whether or not a line break should come immediately after
    for i in range(len(glyphs)):

        glyphs[i]['system_begin'] = False
        glyphs[i]['continue_neume'] = False
        if i < len(glyphs) - 1:

            left_staff = int(glyphs[i]['pitch']['staff'])
            right_staff = int(glyphs[i + 1]['pitch']['staff'])

            if left_staff < right_staff:
                glyphs[i]['system_begin'] = True

        if i > 0:
            left_bb = glyphs[i - 1]['glyph']['bounding_box'] if i > 0 else np.inf
            right_bb = glyphs[i]['glyph']['bounding_box']

            if int(right_bb['ulx']) - (int(left_bb['ulx']) + int(left_bb['ncols'])) < avg_glyph_width:
                glyphs[i]['continue_neume'] = True


    # get (syl, assigned glyphs) pairs
    pairs = neume_to_lyric_alignment(glyphs, syl_boxes, median_line_spacing)

    meiDoc, surface, layer = generate_base_document()

    for gs, syl_box in pairs:
        cur_syllable = MeiElement('syllable')
        bb = {
            'ulx': syl_box['ul'][0],
            'uly': syl_box['ul'][1],
            'ncols': syl_box['lr'][0] - syl_box['ul'][0],
            'nrows': syl_box['lr'][1] - syl_box['ul'][1],
        }
        zoneId = generate_zone(surface, bb)
        cur_syllable.addAttribute('facs', zoneId)
        layer.addChild(cur_syllable)

        syl = MeiElement('syl')
        syl.setValue(str(syl_box['syl']))
        cur_syllable.addChild(syl)

        for i, glyph in enumerate(gs):

            # are we done with neume components in this grouping?
            syllable_over = not any(('neume' in x['glyph']['name']) for x in gs[i:])
            new_el = glyph_to_element(classifier, glyph, surface)

            # four cases to consider:
            # 1. no line break and not done with this syllable (more neume components to add)
            # 2. no line break and done with this syllable (usually a clef)
            # 3. a line break and not done with this syllable (a custos INSIDE a <syllable> tag)
            # 4. a line break and done with this syllable (a custos OUTSIDE a <syllable> tag)

            if not glyph['system_begin']:
                # case 2
                if syllable_over:
                    layer.addChild(new_el)
                # case 1
                else:
                    cur_syllable.addChild(new_el)
                continue

            sb = MeiElement('sb')
            cur_staff = int(glyph['pitch']['staff']) - 1
            zoneId = generate_zone(surface, staves[cur_staff]['bounding_box'])
            sb.addAttribute('facs', zoneId)

            # case 3
            if syllable_over:
                sb.addAttribute('facs', zoneId)
                layer.addChild(new_el)
                layer.addChild(sb)
            elif 'custos' in glyph['glyph']['name']:
                sb.addChild(new_el)
                cur_syllable.addChild(sb)
            # case 4
            else:
                cur_syllable.addChild(new_el)
                cur_syllable.addChild(sb)

    return meiDoc


if __name__ == '__main__':

    f_ind = 56
    classifier_fname = 'test_classifier.xlsx'
    fname = 'salzinnes_{:0>3}'.format(f_ind)
    inJSOMR = './jsomr-split/pitches_{}.json'.format(fname)
    in_syls = './syl_json/{}.json'.format(fname)
    in_png = '/Users/tim/Desktop/PNG_compressed/CF-{:0>3}.png'.format(f_ind)

    classifier = pct.fetch_table(classifier_fname)

    with open(inJSOMR, 'r') as file:
        jsomr = json.loads(file.read())
    with open(in_syls) as file:
        syls = json.loads(file.read())

    glyphs = jsomr['glyphs']
    syl_boxes = syls['syl_boxes']
    staves = jsomr['staves']
    median_line_spacing = syls['median_line_spacing']

    meiDoc = build_mei(glyphs, syl_boxes, staves, classifier, median_line_spacing)

    all_syllables = meiDoc.getElementsByName('syllable')
    # surface = meiDoc.getElementsByName('surface')[0]
    # surf_dict = {}
    # for c in surface.getChildren():
    #     surf_dict[c.id] = c.getAttribute('ulx')

    spacing_dict = {}

    # mean_glyph_width = np.mean([x[1] - x[0] for x in surf_dict.values()])

    for syllable in all_syllables:
        children = syllable.getChildren()
        nc_groups = []
        for k, g in groupby(children, key=lambda x: x.name):
            g = list(g)
            if (not k == 'neume') or len(g) == 1:
                continue
            ncs_to_merge = []
            for neume in g[1:]:
                ncs_to_merge += neume.getChildren()
            for nc in ncs_to_merge:
                g[0].addChild(nc)
            for neume in g[1:]:
                syllable.removeChild(neume)


    documentToFile(meiDoc, 'testexport.mei')
