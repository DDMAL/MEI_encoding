# this is the local test version of the rodan job
# ignore this file

import sys, json
import MeiOutput
reload(MeiOutput)

if __name__== "__main__":

    if len(sys.argv) == 3:
        (tmp, inJSOMR, version) = sys.argv
    elif len(sys.argv) == 2:
        (tmp, inJSOMR) = sys.argv
        version = 'N'
    else:
        print("incorrect usage\npython3 test_JSOMR2MEI path (version)")
        sys.exit()

    with open(inJSOMR, 'r') as file:
        jsomr = json.loads(file.read())

    kwargs = {
        'max_neume_spacing': 0.3,
        'max_group_size': 8,
        'version': '4.0.0',
    }

    mei_obj = MeiOutput.MeiOutput(jsomr, **kwargs)
    mei_string = mei_obj.run()
