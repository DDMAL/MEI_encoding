import numpy as np
from xlrd import open_workbook
from unidecode import unidecode
import xml.etree.ElementTree as ET

classifier_fname = 'test_classifier.xlsx'
name_col = u'Encoding classifier'
mei_col = u'Encoding MEI'

def fetch_table(classifier_fname=classifier_fname):
    wb = open_workbook(classifier_fname)
    sheet = wb.sheets()[0]

    for n in range(sheet.nrows):
        row = [x.value for x in sheet.row(n)]
        if name_col in row and mei_col in row:
            name_pos = row.index(name_col)
            mei_pos = row.index(mei_col)
            starting_from = n
            break

    name_to_mei = {}
    for n in range(starting_from + 1, sheet.nrows):
        item_name = sheet.cell(n, name_pos).value
        item_mei = sheet.cell(n, mei_pos).value
        item_mei = unidecode(item_mei)
        if not item_name:
            continue
        try:
            parsed = ET.fromstring(item_mei)
        except ET.ParseError:
            print('{} failed: row {}, col {}'.format(item_name, n, mei_pos))
            continue
        name_to_mei[item_name] = parsed
    return name_to_mei