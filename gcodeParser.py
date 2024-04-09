supported_commands = {
    "G0": "Coordinated Motion at Rapid Rate",
    "G1": "Coordinated Motion at Feed Rate",
    "G90": "Absolute Distance Mode",
    "G91": "Incremental Distance Mode",
}

supported_axis = {
    "X": "X axis",
    "Y": "Y axis"
}

comment_symbols = {
    ";": "Comment everything after this symbol on that line",
    "(": "Comment everything until ')' is used to close it"
}


class GcodeObject:
    def __init__(self):
        self.command = None
        self.params = {}
        self.comment = ""


def parseLine(line: str) -> GcodeObject:
    result = GcodeObject()
    for letter in line:
        if 
        pass
    return result
