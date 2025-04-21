import os, sys
import re
from model.AnalyzerEntities import *
from model.DataGeneratorEntities import *
from drawer.ClassUmlDrawer import ClassUmlDrawer
from utils.FileWriter import *
from datetime import datetime
from typing import Dict, List, Set, Tuple
from model.AnalyzerEntities import FileTypeEnum


class DataGenerator:
    def __init__(self) -> None:
        self.graphData = GraphData()
        self._uml_drawer_for_filtering = None
        self._language_context = FileTypeEnum.UNDEFINED

    # Ensure this signature accepts targetPath and base_filename
    # Language context is now set externally before calling this
    def generateData(
        self, listOfClassNodes: list[ClassNode], targetPath: str, base_filename: str
    ):
        self.graphData.analysisSourcePath = targetPath
        # Set the language context on the GraphData instance as well
        self.graphData._language_context = self._language_context

        # --- Language Context is now set by FileAnalyzer via self._language_context ---
        # Remove the heuristic block that tried to guess the language here.

        # Instantiate filter helper based on the already set context
        if self._language_context != FileTypeEnum.UNDEFINED:
            print(f"DataGenerator using context: {self._language_context.name}")
            try:
                self._uml_drawer_for_filtering = ClassUmlDrawer(self._language_context)
            except Exception as e:
                print(
                    f"Warning: Could not instantiate ClassUmlDrawer for filtering: {e}"
                )
                self._uml_drawer_for_filtering = None
        else:
            print("Warning: DataGenerator running with UNDEFINED language context.")
            self._uml_drawer_for_filtering = None

        # --- End Language Context Handling ---

        qualified_name_map: Dict[str, ClassNode] = {}
        simple_name_map: Dict[str, List[str]] = {}

        # Use the (now deduplicated) listOfClassNodes
        for node in listOfClassNodes:
            qualified_name = self._get_qualified_name(node)
            if qualified_name:
                qualified_name_map[qualified_name] = node
                # Use the simple name (last part) for the simple_name_map
                separator = "." if self._language_context == FileTypeEnum.JAVA else "::"
                simple_name = qualified_name.split(separator)[-1]
                # Remove template/generic part for simple name mapping
                simple_name = simple_name.split("<")[0]
                if simple_name:
                    if simple_name not in simple_name_map:
                        simple_name_map[simple_name] = []
                    simple_name_map[simple_name].append(qualified_name)

        for node in listOfClassNodes:
            self.dumpClass(node, qualified_name_map, simple_name_map)

        self.graphData.add_blank_classes()  # This needs the language context set
        self.graphData.remove_duplicates()  # Should be redundant now if input list is clean, but safe to keep.

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
        """Generates the fully qualified name based on language context, excluding trailing * &."""
        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"
        name_part = classInfo.name
        # Handle Java generics or C++ templates in name
        if classInfo.params:
            # Use <> for both Java and C++ for consistency in the graph ID
            name_part = f'{classInfo.name}<{", ".join(classInfo.params)}>'

        # Strip trailing * or & from the name part if present (for C++)
        if self._language_context == FileTypeEnum.CPP:
            while name_part.endswith("*") or name_part.endswith("&"):
                name_part = name_part[:-1].strip()

        if classInfo.package:
            return f"{classInfo.package}{separator}{name_part}"
        else:
            return name_part

    def _get_qualified_name_from_string(
        self, name_str: str, current_package: str = None
    ) -> str:
        """
        Attempts to ensure a name string is fully qualified based on language context,
        returning the base type name (no trailing * or &).
        """
        if not isinstance(name_str, str):
            return ""
        name_str = name_str.strip()
        # Clean * and & first
        base_name_str = name_str.replace("*", " ").replace("&", " ").strip()

        # Use the instance's language context
        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"
        alt_separator = "::" if self._language_context == FileTypeEnum.JAVA else "."

        # If it already contains the expected separator, assume qualified
        if separator in base_name_str:
            # Special case: Strip std:: prefix for C++ consistency if present
            if self._language_context == FileTypeEnum.CPP and base_name_str.startswith(
                "std::"
            ):
                return base_name_str[5:]
            return base_name_str
        # If it contains the *other* language's separator, it's likely a mistake or cross-language ref
        elif alt_separator in base_name_str:
            return base_name_str  # Treat as already qualified (maybe incorrectly)

        should_ignore = False
        if self._uml_drawer_for_filtering:
            # Check ignore list using the base name
            should_ignore = self._uml_drawer_for_filtering._should_ignore_type(
                base_name_str
            )
        else:
            # Basic check if filter helper not available (less accurate)
            common_unqualified_types = {  # Combine some common ones
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
                "short",
                "int",
                "long",
                "float",
                "double",
                "size_t",
                "auto",
                "String",
                "Object",
                "Integer",
                "Boolean",
                "Double",
                "Float",
                "Long",
                "Short",
                "Byte",
                "Character",
                "List",
                "ArrayList",
                "Map",
                "HashMap",
                "Set",
                "HashSet",
            }
            # Check template param convention on base name
            is_likely_template_param = (
                len(base_name_str) == 1 and "A" <= base_name_str <= "Z"
            )
            should_ignore = (
                base_name_str in common_unqualified_types or is_likely_template_param
            )

        if should_ignore:
            return base_name_str  # Return base name as is, don't prepend package
        elif current_package:
            # Prepend package to base name
            return f"{current_package}{separator}{base_name_str}"
        else:
            # Assume base name is global type or from root namespace/default package
            return base_name_str

    # Ensure dumpClass signature accepts the maps
    def dumpClass(
        self,
        classInfo: ClassNode,
        qualified_name_map: Dict[str, ClassNode],
        simple_name_map: Dict[str, List[str]],
    ):
        # Use the BASE qualified name for the ID
        qualified_name = self._get_qualified_name(classInfo)
        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"

        classData = ClassData()
        classData.package = classInfo.package
        classData.id = qualified_name  # Use BASE qualified name as ID
        classData.type = "interface" if classInfo.isInterface else "class"
        classData.isAbstract = classInfo.isAbstract
        classData.isFinal = classInfo.isFinal
        classData.isStatic = classInfo.isStatic

        # Format attributes and methods for display - USE ORIGINAL TYPES WITH * &
        classData.methods = []
        for method in classInfo.methods:
            # Skip methods with malformed names (like "result", "return", etc.)
            if (
                not method.name
                or " " in method.name
                or method.name in ["result", "return"]
            ):
                continue

            params_str = ", ".join(method.params)  # method.params includes * &
            return_type = (
                method.dataType  # method.dataType includes * &
                if method.dataType
                else ("void" if self._language_context == FileTypeEnum.JAVA else "")
            )
            method_sig = f"{method.name}({params_str})"
            if return_type:
                method_sig += f": {return_type}"
            classData.methods.append(method_sig)

        classData.attributes = []
        for var in classInfo.variables:
            # Skip variables with malformed names
            if not var.name or " " in var.name:
                continue

            attr_str = f"{var.accessLevel.name.lower()} "
            if var.isStatic:
                attr_str += "static "
            attr_str += f"{var.dataType} {var.name}"
            classData.attributes.append(attr_str.strip())

        self.graphData.nodes.append(classData)

        # Process relations for links - USE BASE TYPES
        # Track relationships we've already processed to avoid duplicates
        processed_relations = set()

        for relation in classInfo.relations:
            try:
                # Skip relationships that were already processed
                rel_key = (relation.name, relation.relationship)
                if rel_key in processed_relations:
                    continue
                processed_relations.add(rel_key)

                target_name_original_base = relation.name
                if not target_name_original_base:
                    continue

                # Skip malformed relationships
                if (
                    target_name_original_base in ["return", "result"]
                    or target_name_original_base.startswith(
                        ":"
                    )  # Possible malformed namespace
                    or " " in target_name_original_base
                ):  # Spaces should not be in class names
                    continue

                # Special handling for templated inheritance relations
                if (
                    relation.relationship == InheritanceEnum.EXTENDED
                    and "<" in target_name_original_base
                ):
                    # For inheritance with templates like ComplexContainer<std::string, int>
                    # Extract the base template name
                    base_template_name = target_name_original_base.split("<")[0].strip()

                    # Try to match by simple name for the ComplexContainer part
                    if base_template_name:
                        # Try to match just the base name against all known classes
                        potential_matches = []
                        for qname in qualified_name_map.keys():
                            # Extract the class name portion (after the last namespace separator)
                            class_part = (
                                qname.split("::")[-1].split("<")[0]
                                if "::" in qname
                                else qname.split("<")[0]
                            )
                            if class_part == base_template_name:
                                potential_matches.append(qname)

                        if len(potential_matches) == 1:
                            # We found exactly one matching class
                            target_name_full_base = potential_matches[0]
                        else:
                            # Try standard namespace qualification
                            target_name_full_base = (
                                self._get_qualified_name_from_string(
                                    base_template_name, classInfo.package
                                )
                            )
                    else:
                        continue
                else:
                    # Regular relationship processing
                    target_name_full_base = self._get_qualified_name_from_string(
                        target_name_original_base, classInfo.package
                    )

                # Resolve BASE target against known BASE classes
                resolved_target_base = target_name_full_base
                if target_name_full_base not in qualified_name_map:
                    separator = (
                        "." if self._language_context == FileTypeEnum.JAVA else "::"
                    )
                    simple_target_name_base = target_name_full_base.split(separator)[
                        -1
                    ].split("<")[0]
                    possible_matches = simple_name_map.get(simple_target_name_base, [])
                    if len(possible_matches) == 1:
                        resolved_target_base = possible_matches[
                            0
                        ]  # This is a base qualified name

                # Check if the resolved BASE target should be ignored
                should_ignore = False
                if self._uml_drawer_for_filtering:
                    # Check ignore using the BASE name
                    should_ignore = self._uml_drawer_for_filtering._should_ignore_type(
                        resolved_target_base
                    )

                # Don't create self-relationships
                if qualified_name == resolved_target_base:
                    should_ignore = True

                # Special handling for known problematic targets
                if relation.relationship == InheritanceEnum.EXTENDED:
                    # Keep extended relationships based on base name match, even for complex templates
                    should_ignore = False

                # Check for common malformed relationship targets
                if resolved_target_base in ["int>", "isModifie"]:
                    should_ignore = True

                if not should_ignore:
                    dependency = Dependency()
                    dependency.source = classData.id  # Source is BASE qualified name
                    dependency.target = (
                        resolved_target_base  # Target is BASE qualified name
                    )
                    dependency.relation = relation.relationship.name.lower()
                    self.graphData.links.append(dependency)
            except AttributeError as e:
                print(
                    f"    - Error processing relation {relation} for node {classData.id}: {e}"
                )

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
