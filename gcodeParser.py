import re

supported_commands = {
    "G0": "Coordinated Motion at Rapid Rate",
    "G1": "Coordinated Motion at Feed Rate",
    "G90": "Absolute Distance Mode",
    "G91": "Incremental Distance Mode",
}

supported_axis = {"X": "X axis", "Y": "Y axis"}

comment_symbols = {
    ";": "Comment everything after this symbol on that line",
    "(": "Comment everything until ')' is used to close it",
}


class GcodeObject:
    def __init__(self):
        self.command = None
        self.params = {}
        self.comment = ""


g_ex = (
    "G1 X83.123 Y135;asd",
    "G1 X84.094 Y135.057 E369.38473",
    "G1 X83.787 Y134.749 E369.40144",
    "G1 X84.138 Y134.447 E369.41922",
)


def parseLine(line: str) -> GcodeObject:
    result = GcodeObject()
    pattern = r"(G\d+)\s(X)(\d+(\.\d*)?)\s(Y)(\d+(\.\d*)?)\s*(;(.*))?"
    res = re.match(pattern, line)
    result.command = supported_commands[res.group(1)]
    result.params = {
        supported_axis[res.group(2)]: float(res.group(3)),
        supported_axis[res.group(5)]: float(res.group(6)),
    }
    result.comment = res.group(9)
    return result


parsed = parseLine(g_ex[0])

print(parsed.command,
      parsed.params,
      parsed.comment)
