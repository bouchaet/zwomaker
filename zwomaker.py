import re
import xml.dom.minidom
import argparse


class Messages():
    def __init__(self):
        self.pattern = "^M [WIC] .*$"
        self.warmup = {"pos": -1, "messages": []}
        self.interval = {"pos": -1, "messages": []}
        self.cooldown = {"pos": -1, "messages": []}

    def parse(self, text):
        classifier = { 
            "W": lambda x: self.warmup["messages"].append(x),
            "I": lambda x: self.interval["messages"].append(x),
            "C": lambda x: self.cooldown["messages"].append(x)
        }
        regex = re.compile(self.pattern)
        for line in text.splitlines():
            if regex.match(line):
                classifier.get(line[2])(line[4:])

    def get_next_interval(self) -> str:
        return self._get_next(self.interval)
    
    def get_next_cooldown(self) -> str:
        return self._get_next(self.cooldown)

    def get_next_warmup(self) -> str:
        return self._get_next(self.warmup)
  
    def _get_next(self, msgDict) -> str:
        if not len(msgDict["messages"]):
            return ""
        
        nxt = (msgDict["pos"] + 1)%len(msgDict["messages"])
        msgDict["pos"] = nxt
        return msgDict["messages"][nxt]
        

class ZwoElement():
    def __init__(self, name, value=None, next_msg="get_next_interval"):
        self._name = name
        self._attribs = []
        self._elements = []
        self._value = value
        self._next_msg = next_msg

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
        return next((int(x[1]) for x in self._attribs 
                     if x[0].lower().endswith("duration")),
                    0)

    def set_duration(self, value: int):
        for x in self._attribs:
            if x[0].lower().endswith("duration"):
                x[1] = value
    
    def get_off_duration(self) -> int:
        return next((int(x[1]) for x in self._attribs 
                    if x[0].lower() == "offduration"),
                   0)

    duration = property(get_duration, set_duration)

    def get_repeat(self):
        return next((x[1] for x in self._attribs if x[0].lower() == "repeat"), 1)

    def insert_messages(self, messages: Messages) -> None:
        elements = [self]
        while len(elements):
            el = elements.pop()
            elements.extend(el._elements)
            if el.duration < 400:
                continue

            silentDist = 200
            offset = silentDist
            next_msg = getattr(messages, el._next_msg)
            maxRep = el.get_repeat()
            duration = el.duration
            offDuration = el.get_off_duration()
            rep = 1
            total = maxRep *(duration + offDuration)
            while offset < total - offDuration:
                if offset == rep * duration + (rep - 1) * offDuration - 100:
                    el.add_element(
                        TextEvent(offset, "Last 100 meters. Almost there!"))
                else:
                    msg = next_msg()
                    if msg:
                        el.add_element(TextEvent(offset, msg))
                offset += 100
                if offset >= rep * duration + (rep -1) * offDuration \
                    and offset < rep * (duration + offDuration):
                    offset += offDuration + silentDist
                    rep += 1


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
            "^R [0-9]* [0-9]*:[0-9]*( [0-9]{2,3})?"
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
        el = ZwoElement("Warmup", next_msg="get_next_warmup")
        el.add_attrib("Duration", tokens[1])
        el.add_attrib("PowerLow", int(tokens[2].split(':')[0])/100)
        el.add_attrib("PowerHigh", int(tokens[2].split(':')[1])/100)
        return el


class Cooldown(ZwoParser):
    def __init__(self):
        super().__init__("^C [0-9]*")

    def parse(self, line):
        tokens = line.split()
        el = ZwoElement("Cooldown", next_msg="get_next_cooldown")
        el.add_attrib("Duration", tokens[1])
        el.add_attrib("PowerLow", int(tokens[2].split(':')[0])/100)
        el.add_attrib("PowerHigh", int(tokens[2].split(':')[1])/100)
        return el


class Name(ZwoParser):
    def __init__(self):
        super().__init__("^N .*")

    def parse(self, line):
        return ZwoElement("name", line[2:])


class Comment(ZwoParser):
    def __init__(self):
        super().__init__("^#.*$")


def lex(zwo_spec: str) -> ZwoElement:
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

    wof.add_element(ZwoElement("author", "zwomaker"))
    wof.add_element(ZwoElement("description", "prepared by zwomaker"))
    wof.add_element(ZwoElement("sportType", "run"))
    wof.add_element(get_tags())
    wof.add_element(wo)
    return wof


def get_tags() -> ZwoElement:
    tags = ZwoElement("tags")

    tag = ZwoElement("tag")
    tag.add_attrib("name", "zwomaker")
    tags.add_element(tag)

    tag = ZwoElement("tag")
    tag.add_attrib("name", "running")
    tags.add_element(tag)
    return tags
    

def pretty_print(xml_string: str) -> str:
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
    parser.add_argument("-m", "--messages", type=str, default="messages.zwodef")
    parser.add_argument("-p", "--print", action="store_true")

    args = parser.parse_args()
    spec = SAMPLE  #for dev
    if args.specfile:
        with open(args.specfile, "r") as file:
            spec = file.read()
    
    with open(args.messages, "r") as msg_file:
        messages = Messages()
        messages.parse(msg_file.read())
    
    wof = lex(spec)
    wof.insert_messages(messages)
    pp_xml = pretty_print(wof.to_xml())
    with open(args.output, "w") as outfile:
        outfile.write(pp_xml)
    
    if args.print:
        print(pp_xml)


if __name__ == "__main__":
   main()