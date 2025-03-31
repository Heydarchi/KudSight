class AnalyzerHelper:
    def __init__(self) -> None:
        pass

    def findClassBoundary(self, inputStr):
        bracketCount = 0
        index = 0
        for index in range(len(inputStr)):
            if inputStr[index] == "}":
                bracketCount = bracketCount - 1
                if bracketCount == 0:
                    return index
            elif inputStr[index] == "{":
                bracketCount = bracketCount + 1
        return index

    def findMethodBoundary(self, inputStr):
        bracketCount = 0
        index = 0
        for index in range(len(inputStr)):
            if inputStr[index] == "}":
                bracketCount = bracketCount - 1
                if bracketCount == 0:
                    return index
            elif inputStr[index] == "{":
                bracketCount = bracketCount + 1
        return index
