from MeiOutput import MeiOutput
import json


def test_generate_synthMEI():
    # test if able to generate MeiOutput object

    inJSOMR = './tests/synthetic_res/classification/jsomr_output.json'
    with open(inJSOMR, 'r') as f:
        jsomr = json.loads(f.read())

    kwargs = {
        'max_width': 0.4,
        'max_size': 8,
        'version': 'N',
    }

    mei_obj = MeiOutput(jsomr, kwargs)
    assert True
