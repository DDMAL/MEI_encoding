import xml.etree.ElementTree as ET
import numpy as np
import json
import parse_classifier_table as pct
from pymei import MeiDocument, MeiElement, documentToText, documentToFile

f_ind = 40

fname = 'salzinnes_{:0>3}'.format(f_ind)
inJSOMR = './jsomr-split/pitches_{}.json'.format(fname)
in_syls = './syl_json/{}.json'.format(fname)

with open(inJSOMR, 'r') as file:
    jsomr = json.loads(file.read())
with open(in_syls) as file:
    syls = json.loads(file.read())

glyphs = jsomr['glyphs']
syl_boxes = syls['syl_boxes']

# sort glyphs in lexicographical order by staff #, left to right
glyphs.sort(key=lambda x: (x['pitch']['staff'], x['pitch']['offset']))

glyphs_pos = 0
num_glyphs = len(glyphs)

# MAKE SURE THAT SYL_BOXES IS SORTED IN READING ORDER! (include more info in json)
pairs = []
for box in syl_boxes:

    # get everything to the upper-left of current box
    retrieved = [g for g in range(glyphs_pos, num_glyphs) if
        glyphs[g]['glyph']['bounding_box']['ulx'] < box['ul'][0] and
        glyphs[g]['glyph']['bounding_box']['uly'] < box['ul'][1]]

    last_found = max(retrieved)
    print(box)
    print(glyphs[last_found])
    print('\n\n')
    pairs.append((box, glyphs[glyphs_pos:last_found]))
    glyphs_pos = last_found
