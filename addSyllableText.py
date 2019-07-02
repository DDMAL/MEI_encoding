import json
import MeiOutput
from pymei import MeiDocument, MeiElement, documentToText, documentToFile


def intersect(bb1, bb2):
    '''
    takes two bounding boxes as an argument. if they overlap, return the area of the overlap;
    else, return False
    '''
    dx = min(bb1['lrx'], bb2['lrx']) - max(bb1['ulx'], bb2['ulx'])
    dy = min(bb1['lry'], bb2['lry']) - max(bb1['uly'], bb2['uly'])
    if (dx > 0) and (dy > 0):
        return dx*dy
    else:
        return False


def union_bboxes(bboxes):
    '''
    given an iterable of bounding boxes, finds the smallest bounding box containing all of them
    '''
    lrx = max(int(bb['lrx']) for bb in bboxes)
    lry = max(int(bb['lry']) for bb in bboxes)
    ulx = min(int(bb['ulx']) for bb in bboxes)
    uly = min(int(bb['uly']) for bb in bboxes)

    return {'ulx': ulx, 'uly': uly, 'lrx': lrx, 'lry': lry}


def add_syllables_to_doc(mei_doc, syls_json, return_text=False):

    median_line_spacing = syls_json['median_line_spacing']
    syls_dict = syls_json['syl_boxes']

    syl_boxes = [
        {
            'ulx': int(s['ul'][0]),
            'uly': int(s['ul'][1]),
            'lrx': int(s['lr'][0]),
            'lry': int(s['lr'][1]),
            'syl': s['syl']
        }
        for s
        in syls_dict]

    syllables = mei_doc.getElementsByName('syllable')
    zones = mei_doc.getElementsByName('zone')
    surface = mei_doc.getElementsByName('surface')[0]

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

    for i, se in enumerate(syllables):

        # get the neume associated with this syllable and the syllable's id
        neume = se.getChildrenByName('neume')[0]
        syl_id = se

        if not cur_syllable:
            cur_syllable = se

        # get bounding box that contains all the neume components of this neume
        ncs = neume.getChildrenByName('nc')
        bboxes = [id_to_bb[nc.getAttribute('facs').value] for nc in ncs]
        neume_bbox = union_bboxes(bboxes)
        all_bboxes.append(neume_bbox)

        # translate this bounding box downwards by half the height of a line
        # this should put well-positioned neumes right in the middle of the text they're associated with
        trans_bbox = dict(neume_bbox)
        trans_bbox['lry'] += median_line_spacing // 1.5
        trans_bbox['uly'] += 1 # median_line_spacing

        colliding_syls = [s for s in syl_boxes if intersect(s, trans_bbox)]

        # of all the colliding syllable boxes, take the one with largest collision amount
        if colliding_syls:
            # best_colliding_text = min(colliding_syls, key=lambda x: x[1][0])
            best_colliding_text = max(colliding_syls, key=lambda s: intersect(s, trans_bbox))
            prev_assigned_text = best_colliding_text
        else:
            best_colliding_text = None

        # if there is no text OR if the found text is the same as last time then the neume being
        # considered here is linked to the previous syllable.
        if (not best_colliding_text) or (best_colliding_text == prev_text):
            cur_syllable.addChild(neume)
            elements_to_remove.append(se)
        # if the text found in the collision is new, then we're starting a new text syllable. register
        # it in the manifest section with a new zone and set the cur_syllable variable
        else:
            cur_syllable = se

            text_el = MeiElement('syl')
            text_el.setValue(str(best_colliding_text['syl']))

            zone_el = MeiElement('zone')
            zone_el.addAttribute('ulx', str(best_colliding_text['ulx']))
            zone_el.addAttribute('uly', str(best_colliding_text['uly']))
            zone_el.addAttribute('lrx', str(best_colliding_text['lrx']))
            zone_el.addAttribute('lry', str(best_colliding_text['lry']))
            text_el.addAttribute('facs', zone_el.id)

            cur_syllable.addChild(text_el)
            surface.addChild(zone_el)

        prev_text = best_colliding_text
        assign_lines.append([prev_assigned_text, neume_bbox])

    # remove syllable elements that just held neumes and are now duplicates
    for el in elements_to_remove:
        el.parent.removeChild(el)

    if return_text:
        return documentToText(mei_doc)
    else:
        return mei_doc, assign_lines


def draw_neume_alignment(fname, boxes, out_fname):
    import PIL
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    im = Image.open(fname).convert('RGB')
    draw = ImageDraw.Draw(im)

    last_text = None
    for tb, nb in boxes:

        if not (tb is None):
            last_text = tb
        if last_text is None:
            continue

        t = last_text
        for i in range(4):
            draw.rectangle([t['ulx'] - i, t['uly'] - i, t['lrx'] + i, t['lry'] + i], outline='black')
        draw.rectangle([nb['ulx'], nb['uly'], nb['lrx'], nb['lry']], outline='black')

        pt1 = ((t['ulx'] + t['lrx']) // 2, (t['lry'] + t['uly']) // 2)
        pt2 = ((nb['ulx'] + nb['lrx']) // 2, (nb['lry'] + nb['uly']) // 2)

        if pt1[1] > pt2[1]:
            draw.line([pt1, pt2], fill='black', width=10)

    im.save('neume_alignment_{}.jpg'.format(out_fname), quality=20, optimize=True)


if __name__ == '__main__':
    import os
    reload(MeiOutput)

    f_inds = range(80, 120)
    for f_ind in f_inds:
        fname = 'salzinnes_{:0>3}'.format(f_ind)
        inJSOMR = './jsomr-split/pitches_{}.json'.format(fname)
        in_syls = './syl_json/{}.json'.format(fname)
        in_png = '/Users/tim/Desktop/PNG_compressed/CF-{:0>3}.png'.format(f_ind)

        if not os.path.isfile(inJSOMR) or not os.path.isfile(in_syls):
            continue

        print('processing {}...'.format(fname))
        kwargs = {
            'max_neume_spacing': 0.3,
            'max_group_size': 8,
            'mei_version': '4.0.0',
        }

        with open(inJSOMR, 'r') as file:
            jsomr = json.loads(file.read())
            mei_obj = MeiOutput.MeiOutput(jsomr, **kwargs)
            mei_doc = mei_obj.run(return_text=False)

        with open(in_syls) as file:
            syls_json = json.loads(file.read())

        mei_doc, boxes = add_syllables_to_doc(mei_doc, syls_json)
        documentToFile(mei_doc, './out_mei/output_split_{}.mei'.format(fname))

        if os.path.isfile(in_png):
            draw_neume_alignment(in_png, boxes, fname)
