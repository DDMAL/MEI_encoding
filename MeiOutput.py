from pymei import MeiDocument, MeiElement, documentToText


class MeiOutput(object):

    def __init__(self, incoming_data, version, **kwargs):
        self.incoming_data = incoming_data
        self.version = version

    def run(self):

        if self.version == 'N':
            return self.meiNume()
        else:
            print('not MEI neume version')

    def meiNume(self):
        print('begin conversion')

        doc = self.setupDoc()

        return documentToText(doc)

    def setupDoc(self):
        # initialize basic universal attributes of any MEI document
        doc = MeiDocument()

        root = self._generate_root(doc)
        head = self._generate_meiHead(root)
        music = self._generate_music(root)

        return doc

    def _generate_root(self, parent):
        el = MeiElement("mei")
        parent.root = el

        el.addAttribute("meiversion", "Neume")

        return el

    def _generate_meiHead(self, parent):
        el = MeiElement("meiHead")
        parent.addChild(el)

        return el

    def _generate_music(self, parent):
        el = MeiElement("music")
        parent.addChild(el)

        self._generate_body(el)

        return el

    def _generate_body(self, parent):
        el = MeiElement("body")
        parent.addChild(el)

        self._generate_mdiv(el)

    def _generate_mdiv(self, parent):
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

        # self._generate_(el)

    def _generate_staffGrp(self, parent):
        el = MeiElement("staffGrp")
        parent.addChild(el)

        self._generate_staffDef(el)

    def _generate_staffDef(self, parent):
            el = MeiElement("staffDef")
            parent.addChild(el)

            # self._generate_(el)

    def _generate_(self, parent):
                el = MeiElement("")
                parent.addChild(el)

                # self._generate_(el)

