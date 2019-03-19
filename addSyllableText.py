import json
from MeiOutput import MeiOutput
from pymei import MeiDocument, MeiElement, documentToText, documentToFile


def intersect(ul1, lr1, ul2, lr2):
    dx = min(lr1[1], lr2[1]) - max(ul1[1], ul2[1])
    dy = min(lr1[0], lr2[0]) - max(ul1[0], ul2[0])
    if (dx > 0) and (dy > 0):
        return dx*dy
    else:
        return False

if __name__ == '__main__':

    fname = 'salzinnes_20'
    inJSOMR = './jsomr_files/pitches_{}.json'.format(fname)
    in_syls = './json_syls/syls_{}.json'.format(fname)

    kwargs = {
        'max_neume_spacing': 0.3,
        'max_group_size': 8,
        'mei_version': '4.0.0',
    }

    with open(inJSOMR, 'r') as file:
        jsomr = json.loads(file.read())
        mei_obj = MeiOutput(jsomr, **kwargs)
        mei_doc = mei_obj._createDoc(return_text=False)

    with open(in_syls) as file:
        syls_json = json.loads(file.read())
        median_line_spacing = syls_json['median_line_spacing']
        syls_boxes = syls_json['syl_boxes']

    syllables = mei_doc.getElementsByName('syllable')
    zones = mei_doc.getElementsByName('zone')

    # dictionary mapping id of every zone element to its bounding box information
    id_to_bb = {}
    for z in zones:
        zattrib = z.attributes
        bb = {}
        for att in zattrib:
            bb[att.name] = att.value
        id_to_bb[z.id] = bb

    all_bboxes = []
    cur_syllable = None         # current syllable element in tree being added to
    prev_text = None            # last text found
    prev_assigned_text = None   # last text assigned
    elements_to_remove = []     # holds syllable elements containing duplicates
    assign_lines = []           # lines b/w text and neumes, for visualization only

    for i, se in enumerate(syllable_elements):

        # get the neume associated with this syllable and the syllable's id
        neume = se.getChildrenByName('neume')[0]
        syl_id = se

        if not cur_syllable:
            cur_syllable = se
