import re
import xml.dom.minidom
import argparse


class ZwoElement():
    def __init__(self, name, value=None):
        self._name = name
        self._attribs = []
        self._elements = []
        self._value = value

    def to_xml(self):
        att_str = "".join([f" {k}=\"{v}\"" for k, v in self._attribs])
        subs = "".join([s.to_xml() for s in self._elements])
        value = ""
        if self._value:
            value = self._value
        return f"<{self._name}{att_str}>{value}{subs}</{self._name}>"

    def add_attrib(self, name, value):
        self._attribs.append((name, value))

    def add_element(self, element):
        if element:
            self._elements.append(element)

    def get_duration(self):
        return next((x[1] for x in self._attribs if x[0].lower() == "duration"),
                    None)

    def set_duration(self, value):
        for x in self._attribs:
            if x[0].lower() == "duration":
                x[1] = value

    duration = property(get_duration, set_duration)

    def get_repeat(self):
        return next((x[1] for x in self._attribs if x[0].lower() == "repeat"), 1)


class TextEvent(ZwoElement):
    def __init__(self, distoffset, message):
        super().__init__("textevent")
        self.add_attrib("distoffset", distoffset)
        self.add_attrib("message", message)


class ZwoParser():
    def __init__(self, pattern):
        self._pattern = pattern

    def can_parse(self, line):
        regex = re.compile(self._pattern)
        return regex.match(line)

    def parse(self, line):
        pass


class Intervals(ZwoParser):
    def __init__(self):
        super().__init__(
            "^I [0-9]{1,2} [0-9]*:[0-9]* [0-9]*:[0-9]*( [0-9]{2,3})?")

    def parse(self, line):
        tokens = line.split()
        repeat = int(tokens[1])
        onDuration = int(tokens[2].split(':')[0])
        offDuration = int(tokens[2].split(':')[1])

        el = ZwoElement("IntervalsT")
        el.add_attrib("Repeat", repeat)
        el.add_attrib("OnDuration", onDuration)
        el.add_attrib("OffDuration", offDuration)
        el.add_attrib("OnPower", int(tokens[3].split(':')[0])/100)
        el.add_attrib("OffPower", int(tokens[3].split(':')[1])/100)
        el.add_attrib("Cadence", int(int(tokens[4])/2))

        for x in range(repeat):
            offset = onDuration + x * (onDuration + offDuration) - 100
            if offset > 100:
                el.add_element(
                    TextEvent(offset, "Last 100 meters. Keep it up!"))
        return el


class SteadyState(ZwoParser):
    def __init__(self):
        super().__init__(
            "^S [0-9]* [0-9]*"
        )

    def parse(self, line):
        tokens = line.split()
        el = ZwoElement("SteadyState")
        el.add_attrib("Duration", tokens[1])
        el.add_attrib("Power", int(tokens[2].split(':')[0])/100)
        el.add_attrib("Cadence", int(int(tokens[3])/2))
        return el


class Ramp(ZwoParser):
    def __init__(self):
        super().__init__(
            "^R [0-9]* [0-9]*:[0-9]*( [0-9](2,3))?"
        )

    def parse(self, line):
        tokens = line.split()
        el = ZwoElement("Ramp")
        el.add_attrib("Duration", tokens[1])
        el.add_attrib("PowerLow", int(tokens[2].split(':')[0])/100)
        el.add_attrib("PowerHigh", int(tokens[2].split(':')[1])/100)
        el.add_attrib("Cadence", 90)
        return el


class Warmup(ZwoParser):
    def __init__(self):
        super().__init__("^W [0-9]* [0-9]*:[0-9]*")

    def parse(self, line):
        tokens = line.split()
        el = ZwoElement("Warmup")
        el.add_attrib("Duration", tokens[1])
        el.add_attrib("PowerLow", int(tokens[2].split(':')[0])/100)
        el.add_attrib("PowerHigh", int(tokens[2].split(':')[1])/100)
        return el


class Cooldown(ZwoParser):
    def __init__(self):
        super().__init__("^C [0-9]*")

    def parse(self, line):
        tokens = line.split()
        el = ZwoElement("Cooldown")
        el.add_attrib("Duration", tokens[1])
        el.add_attrib("PowerLow", int(tokens[2].split(':')[0])/100)
        el.add_attrib("PowerHigh", int(tokens[2].split(':')[1])/100)
        return el


class Name(ZwoParser):
    def __init__(self):
        super().__init__("^N .*")

    def parse(self, line):
        tokens = line.split()
        return ZwoElement("name", tokens[1])


class Comment(ZwoParser):
    def __init__(self):
        super().__init__("^#.*$")
    

def lex(zwo_spec):
    wof = ZwoElement("workout_file")
    wo = ZwoElement("workout")
    parser_actions = [
        (Intervals(), wo.add_element),
        (Ramp(), wo.add_element),
        (Name(), wof.add_element),
        (Warmup(), wo.add_element),
        (Cooldown(), wo.add_element),
        (SteadyState(), wo.add_element),
        (Comment(), lambda x : print("Ignore comment"))
    ]

    for line in zwo_spec.splitlines():
        if not len(line):
            continue

        print(f"processing line {line}...")
        match = False
        for parser, action in parser_actions:
            if parser.can_parse(line):
                print(f"Match with {parser.__class__.__name__}")
                action(parser.parse(line))
                match = True
                continue
        if not match:
            print("*** NO MATCH ***")

    wof.add_element(ZwoElement("sportType", "run"))
    wof.add_element(get_tags())
    wof.add_element(wo)
    return wof


def get_tags():
    tags = ZwoElement("tags")
    tags.add_element(ZwoElement("tag", "ZwoMaker"))
    tags.add_element(ZwoElement("tag", "Running"))
    return tags
    

def pretty_print(xml_string):
    dom = xml.dom.minidom.parseString(xml_string)
    return dom.toprettyxml()


SAMPLE = """
N Sample Workout
W 1000 65:75
S 1000 82 180
# main set 2x 1000m
I 2 1000:200 90:65 180
R 1000 65:82 180
C 1000 75:65
"""


def main():
    parser = argparse.ArgumentParser(description="Zwift workout maker.")
    parser.add_argument("-s", "--specfile", type=str)
    parser.add_argument("-o", "--output", type=str, default="out.zwo")
    parser.add_argument("-p", "--print", action="store_true")

    args = parser.parse_args()
    spec = SAMPLE  #for dev
    if args.specfile:
        with open(args.specfile, "r") as file:
            spec = file.read()
    
    wof = lex(spec)
    pp_xml = pretty_print(wof.to_xml())
    with open(args.output, "w") as outfile:
        outfile.write(pp_xml)
    
    if args.print:
        print(pp_xml)


if __name__ == "__main__":
    main()