import re
import xml.dom.minidom

def dict_to_xml(d, text=None, is_open=False):
    tmp = [item for item in d.items()]
    elements = [i for i in tmp if i[0][0] != "@"]
    attribs = [i for i in tmp if i[0][0] == "@"]
    if not text:
        text = []

    for key, value in attribs:
        text.append(f" {key[1:]}=\"{value}\"")
    if is_open:
        text.append(">")
        is_open = False

    for key,value in elements:
        text.append(f"<{key}")
        if isinstance(value, dict):
            dict_to_xml(value, text, True)
        elif isinstance(value, list):
            text.append(">")
            for x in value:
                dict_to_xml(x, text, False) 
        else:
            text.append(f">{value}")
        text.append(f"</{key}>")

    return "".join(str(t) for t in text)


def lex(zwo_spec):
    token_exprs = [
            ("^I [0-9]*:[0-9]* [0-9]*:[0-9]*( [0-9](2,3))?", "IntervalsT", addInterval),
            ("^R .*", "Ramp", addRamp),
            ("^S [0-9]* [0-9]*", "SteadyState", addSteadyState),
            ("^W [0-9]* [0-9]*:[0-9]*", "Warmup", addWarmup),
            ("^C [0-9]*", "Cooldown", addCooldown),
            ("^T .*", "Name", addName),
            ("^# .*", "Comment", comment)
            ]
    match = None
    wo = {"zwift_workout": {"name":"", "sportType":"run", "workout":[]}}
    for line in zwo_spec.splitlines():
        print(f"processing {line}...")
        for token_expr in token_exprs:
            pattern, tag, action = token_expr
            regex = re.compile(pattern)
            match = regex.match(line)

            if match:
                print(f"{match.group(0)} match with tag {tag}")
                action(wo, line)
                continue
    return wo


def comment(wo, line):
    pass

def addSteadyState(wo, line):
    tokens = line.split()
    el = {
            "SteadyState": {
                "@Duration": tokens[1],
                "@Power": int(tokens[2].split(':')[0])/100,
                "@Cadence": int(int(tokens[3])/2)
                }}
    wo["zwift_workout"]["workout"].append(el)

def addWarmup(wo, line):
    tokens = line.split()
    el = {
            "Warmup": {
                "@Duration": tokens[1],
                "@PowerLow": int(tokens[2].split(':')[0])/100,
                "@PowerHigh": int(tokens[2].split(':')[1])/100,
            }}
    wo["zwift_workout"]["workout"].append(el)


def addCooldown(wo, line):
    tokens = line.split()
    el = {
            "Cooldown": {
                "@Duration": tokens[1],
                "@PowerLow": int(tokens[2].split(':')[0])/100,
                "@PowerHigh": int(tokens[2].split(':')[1])/100,
            }}
    wo["zwift_workout"]["workout"].append(el)

def addName(wo, line):
    tokens = line.split();
    wo["zwift_workout"]["name"] = tokens[1]

def addInterval(wo, line):
    tokens = line.split()
    onDuration = tokens[1].split(':')[0]
    offDuration = tokens[1].split(':')[1]
    el = {
        "IntervalsT": {
            "@onDuration": onDuration,
            "@offDuration": offDuration,
            "@onPower": int(tokens[2].split(':')[0])/100,
            "@offPower": int(tokens[2].split(':')[1])/100,
            "@Cadence": int(int(tokens[3])/2)
        }
    }
    wo["zwift_workout"]["workout"].append(el)

def addRamp(wo, line):
    tokens = line.split()
    el = {
            "Ramp": {
                "@Duration": tokens[1],
                "@PowerLow": int(tokens[2].split(':')[0])/100,
                "@PowerHigh": int(tokens[2].split(':')[1])/100,
                "@Cadence": 90
                }}
    wo["zwift_workout"]["workout"].append(el)

def pretty_print(xml_string):
    dom = xml.dom.minidom.parseString(xml_string)
    return dom.toprettyxml()

def create_zwo(zwo):
    xml_text = dict_to_xml(zwo)
    print(xml_text)
    print(pretty_print(xml_text))

SAMPLE="""
T Test
W 1000 65:75
S 1000 82 180
I 1000:200 90:65 180
R 1000 65:82 180
C 1000 75:65
"""

if __name__ == "__main__" :
    wo = lex(SAMPLE)
    create_zwo(wo)
