# this is the local test version of the rodan job
# ignore this file

import sys, json
from MeiOutput import MeiOutput

if __name__== "__main__":
    
    if len(sys.argv) == 3:
        (tmp, inJSOMR, version) = sys.argv
    elif len(sys.argv) == 2:
        (tmp, inJSOMR) = sys.argv
        version = 'N'
    else:
        print("incorrect usage\npython3 test_JSOMR2MEI path (version)")
        quit()

    with open(inJSOMR, 'r') as file:
        jsomr = json.loads(file.read())

    kwargs = {

    }


    mei_obj = MeiOutput(jsomr, version, **kwargs)
    mei_string = mei_obj.run()

