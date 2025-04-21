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

    def parse_template_params(self, template_str):
        """
        Parse template parameters, handling nested templates correctly.
        Example: "int, std::vector<std::string>, MyClass" -> ["int", "std::vector<std::string>", "MyClass"]
        """
        params = []
        current_param = ""
        nesting_level = 0

        for char in template_str:
            if char == "<":
                nesting_level += 1
                current_param += char
            elif char == ">":
                nesting_level -= 1
                current_param += char
            elif char == "," and nesting_level == 0:
                # Only split on commas at the top level
                params.append(current_param.strip())
                current_param = ""
            else:
                current_param += char

        # Add the last parameter if it exists
        if current_param:
            params.append(current_param.strip())

        return params

    def extract_template_base_name(self, qualified_type):
        """
        Extract the base name without template parameters.
        Example: "std::vector<int>" -> "std::vector"
        """
        template_start = qualified_type.find("<")
        if template_start >= 0:
            return qualified_type[:template_start].strip()
        return qualified_type
