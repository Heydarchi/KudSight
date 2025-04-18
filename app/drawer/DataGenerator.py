import os, sys
import re
from model.AnalyzerEntities import *
from model.DataGeneratorEntities import *
from drawer.ClassUmlDrawer import ClassUmlDrawer
from utils.FileWriter import *
from datetime import datetime
from typing import Dict, List  # Import Dict and List for type hinting


class DataGenerator:
    def __init__(self) -> None:
        self.graphData = GraphData()
        try:
            # Assuming CPP context for filtering based on the example
            # TODO: Determine language context dynamically if needed
            self._uml_drawer_for_filtering = ClassUmlDrawer(FileTypeEnum.CPP)
        except Exception as e:
            print(f"Warning: Could not instantiate ClassUmlDrawer for filtering: {e}")
            self._uml_drawer_for_filtering = None

    # Ensure this signature accepts targetPath and base_filename
    def generateData(
        self, listOfClassNodes: list[ClassNode], targetPath: str, base_filename: str
    ):
        self.graphData.analysisSourcePath = targetPath

        qualified_name_map: Dict[str, ClassNode] = {}
        simple_name_map: Dict[str, List[str]] = {}

        for node in listOfClassNodes:
            qualified_name = self._get_qualified_name(node)
            if qualified_name:
                qualified_name_map[qualified_name] = node
                simple_name = node.name
                if simple_name:
                    if simple_name not in simple_name_map:
                        simple_name_map[simple_name] = []
                    simple_name_map[simple_name].append(qualified_name)

        for node in listOfClassNodes:
            self.dumpClass(node, qualified_name_map, simple_name_map)

        self.graphData.add_blank_classes()
        self.graphData.remove_duplicates()

        json_output = self.graphData.to_json()

        # Use base_filename for JSON
        filePath = f"static/out/{base_filename}.json"

        self.writeToFile(filePath, json_output)

    def _sanitize_path_for_filename(self, path: str) -> str:
        """Sanitizes a full path string to be suitable for use in a filename."""
        if not path:
            return "analysis"

        # Replace drive colon first (e.g., C:)
        sanitized = path.replace(":", "_")
        # Replace path separators with underscores
        sanitized = sanitized.replace("\\", "_").replace("/", "_")
        # Remove or replace other invalid filename characters
        sanitized = re.sub(
            r'[<>"]', "_", sanitized
        )  # Removed /\|?* as they were handled by separator replacement
        # Replace sequences of underscores with a single one
        sanitized = re.sub(r"_+", "_", sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")

        # Limit length if necessary (e.g., 100 chars for full path)
        max_len = 100
        if len(sanitized) > max_len:
            # Try to keep the end part of the path
            sanitized = sanitized[-max_len:]
            # Remove any partial segment at the beginning
            sanitized = re.sub(r"^[^_]*_", "", sanitized, count=1)

        return sanitized if sanitized else "analysis"

    def _get_qualified_name(self, classInfo: ClassNode) -> str:
        """Generates the fully qualified name."""
        name_part = classInfo.name
        if classInfo.params:
            # Add template params to simple name before adding package
            name_part = f'{classInfo.name}<{", ".join(classInfo.params)}>'
        if classInfo.package:
            return f"{classInfo.package}::{name_part}"
        else:
            return name_part

    def _get_qualified_name_from_string(
        self, name_str: str, current_package: str = None
    ) -> str:
        """
        Attempts to ensure a name string is fully qualified.
        If it doesn't contain '::', prepend the current_package if available,
        unless it's a known primitive/standard type or likely a template parameter.
        """
        if not isinstance(name_str, str):
            return ""
        name_str = name_str.strip()  # Ensure no leading/trailing spaces

        # If it already has a namespace separator, assume it's qualified (or std::)
        if "::" in name_str:
            # Special case: Strip std:: prefix for consistency if present
            if name_str.startswith("std::"):
                return name_str[5:]
            return name_str

        # Check if it's a known primitive/common type that shouldn't be qualified
        # (This list should ideally match the one used for ignoring relations)
        common_unqualified_types = {
            "string",
            "vector",
            "map",
            "set",
            "list",
            "deque",
            "pair",
            "void",
            "bool",
            "char",
            "wchar_t",
            "char8_t",
            "char16_t",
            "char32_t",
            "short",
            "int",
            "long",
            "float",
            "double",
            "signed",
            "unsigned",
            "size_t",
            "ptrdiff_t",
            "nullptr_t",
            "auto",
            # Add other common STL types as needed
        }
        # Also check for typical template parameter names (e.g., single uppercase letter)
        is_likely_template_param = len(name_str) == 1 and "A" <= name_str <= "Z"

        if name_str in common_unqualified_types or is_likely_template_param:
            return name_str  # Return as is, don't prepend package

        # If no namespace, not common/template, and we have a current package context, prepend it
        elif current_package:
            return f"{current_package}::{name_str}"
        # Otherwise, return the name as is (might be a global type from root namespace)
        else:
            return name_str

    # Ensure dumpClass signature accepts the maps
    def dumpClass(
        self,
        classInfo: ClassNode,
        qualified_name_map: Dict[str, ClassNode],
        simple_name_map: Dict[str, List[str]],
    ):
        qualified_name = self._get_qualified_name(classInfo)

        classData = ClassData()
        classData.package = classInfo.package
        classData.id = qualified_name  # Use fully qualified name as ID
        classData.type = "interface" if classInfo.isInterface else "class"

        classData.isAbstract = classInfo.isAbstract
        classData.isFinal = classInfo.isFinal
        classData.isStatic = classInfo.isStatic

        # Keep simple strings for attributes/methods for now
        classData.methods = [method.name for method in classInfo.methods]
        classData.attributes = [
            f"{var.accessLevel.name.lower()} {'static ' if var.isStatic else ''}{var.dataType} {var.name}".strip()
            for var in classInfo.variables
            if var.name != "return"
        ]

        self.graphData.nodes.append(classData)

        for relation in classInfo.relations:
            try:
                target_name_original = relation.name  # Keep original name from relation
                target_name_full = target_name_original  # Default target for link

                is_inheritance = relation.relationship in [
                    InheritanceEnum.EXTENDED,
                    InheritanceEnum.IMPLEMENTED,
                ]
                is_qualified_original = "::" in target_name_original

                if not is_inheritance or is_qualified_original:
                    # Try to qualify dependencies or already-qualified inheritance names
                    target_name_full = self._get_qualified_name_from_string(
                        target_name_original, classInfo.package
                    )

                # Resolve target against known classes
                resolved_target = target_name_full  # Start with the potentially qualified/unqualified name

                if target_name_full not in qualified_name_map:
                    # If the target isn't directly found (e.g., "Utils", "T", or maybe "MyCompany::Core::Utils" which is wrong)
                    # And if the target_name_full is currently unqualified...
                    if "::" not in target_name_full:
                        # Check if this simple name exists uniquely in the simple_name_map
                        possible_matches = simple_name_map.get(target_name_full, [])
                        if len(possible_matches) == 1:
                            # Found a unique qualified match, use it!
                            resolved_target = possible_matches[0]

                should_ignore = False
                if self._uml_drawer_for_filtering:
                    # Filter based on the resolved target name
                    should_ignore = self._uml_drawer_for_filtering._should_ignore_type(
                        resolved_target
                    )

                if not should_ignore:
                    dependency = Dependency()
                    dependency.source = classData.id  # Source is qualified name
                    dependency.target = resolved_target  # Use the resolved name
                    dependency.relation = relation.relationship.name.lower()
                    self.graphData.links.append(dependency)

            except AttributeError as e:
                print(
                    f"    - Error processing relation {relation}: {e}"
                )  # Keep error log

    def writeToFile(self, fileName, json_output):
        with open(fileName, "w") as f:
            f.write(json_output)


# Optional test run (standalone)
if __name__ == "__main__":
    print(sys.argv)
    classInfo = ClassNode()
    classInfo.name = "TestClass"
    classInfo.relations.append(Inheritance("Class1", InheritanceEnum.DEPENDED))
    classInfo.relations.append(Inheritance("Class2", InheritanceEnum.EXTENDED))
    classInfo.relations.append(Inheritance("Class3", InheritanceEnum.IMPLEMENTED))
    classUmlDrawer = ClassUmlDrawer()
    classUmlDrawer.drawUml(classInfo)
