import os, sys
import re
from model.AnalyzerEntities import *
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


class ClassUmlDrawer:
    def __init__(self, file_type: FileTypeEnum) -> None:
        self.mapList = list()
        self.mapList.append(UmlRelationMap("", InheritanceEnum.DEPENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.EXTENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.IMPLEMENTED))

        self._language_context = file_type

        loaded_keywords = self.load_keywords(file_type)
        common_types_to_ignore = set()
        basic_primitives = set()
        if file_type == FileTypeEnum.JAVA:
            basic_primitives = {
                "void",
                "boolean",
                "byte",
                "char",
                "short",
                "int",
                "long",
                "float",
                "double",
            }
            common_types_to_ignore = {
                "Object",
                "String",
                "CharSequence",
                "Number",
                "Boolean",
                "Byte",
                "Character",
                "Short",
                "Integer",
                "Long",
                "Float",
                "Double",
                "Void",
                "Math",
                "System",
                "Thread",
                "Runnable",
                "Exception",
                "RuntimeException",
                "Error",
                "Throwable",
                "Class",
                "ClassLoader",
                "Package",
                "Process",
                "Runtime",
                "Enum",
                "List",
                "ArrayList",
                "LinkedList",
                "Map",
                "HashMap",
                "Set",
                "HashSet",
                "Collection",
                "Collections",
                "Iterator",
                "Optional",
                "Date",
                "Calendar",
                "UUID",
                "Arrays",
                "Objects",
                "Properties",
                "Random",
                "Scanner",
                "File",
                "InputStream",
                "OutputStream",
                "Reader",
                "Writer",
                "Serializable",
                "Override",
                "Deprecated",
                "SuppressWarnings",
            }
        elif file_type == FileTypeEnum.CPP:
            basic_primitives = {
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
                "size_t",
                "ptrdiff_t",
                "nullptr_t",
                "auto",
            }
            common_types_to_ignore = {
                "string",
                "wstring",
                "vector",
                "map",
                "set",
                "list",
                "deque",
                "pair",
                "tuple",
                "shared_ptr",
                "unique_ptr",
                "weak_ptr",
                "istream",
                "ostream",
                "iostream",
                "fstream",
                "sstream",
                "function",
                "optional",
                "variant",
                "any",
            }

        combined_ignored = (
            set(loaded_keywords) | common_types_to_ignore | basic_primitives
        )
        self.dataTypeToIgnore = combined_ignored
        self.type_cleaner = self._get_type_cleaner()

    @staticmethod
    def load_keywords(file_type: FileTypeEnum) -> list[str]:
        if file_type == FileTypeEnum.UNDEFINED:
            print("Warning: Undefined file type, cannot load keywords.")
            return []
        try:
            current_script_dir = Path(__file__).resolve().parent
            app_dir = current_script_dir.parent
            data_dir = app_dir.parent / "data"
            if not data_dir.exists():
                print(f"Warning: Calculated data directory does not exist: {data_dir}")
                data_dir = Path("data")
                if not data_dir.exists():
                    print(
                        f"Warning: Fallback data directory does not exist: {data_dir.resolve()}"
                    )
                    return []
            file_name = f"{file_type.name}.txt"
            file_path = data_dir / file_name
        except Exception as e:
            print(f"Error calculating keyword file path: {e}")
            return []

        print(f"Attempting to load keywords from: {file_path.resolve()}")
        keywords = []
        if not file_path.is_file():
            print(f"Warning: Keyword file not found at {file_path.resolve()}")
            return []
        try:
            with open(file_path, "r") as f:
                keywords = [line.strip() for line in f if line.strip()]
                print(f"Loaded {len(keywords)} keywords from {file_path.resolve()}")
        except Exception as e:
            print(f"Error loading keywords from {file_path.resolve()}: {e}")
        return keywords

    def _get_type_cleaner(self):
        """Returns a cleaner function for DISPLAY purposes (keeps * &)."""
        modifiers = set()
        namespaces_to_strip = set()

        if self._language_context == FileTypeEnum.JAVA:
            modifiers = {
                "public",
                "protected",
                "private",
                "static",
                "final",
                "abstract",
                "synchronized",
                "volatile",
                "transient",
                "native",
                "strictfp",
                "default",
                "sealed",
                "non-sealed",
            }
        elif self._language_context == FileTypeEnum.CPP:
            modifiers = {
                "const",
                "volatile",
                "static",
                "mutable",
                "register",
                "inline",
                "extern",
                "typename",
                "using",
                "struct",
                "class",
                "virtual",
                "explicit",
                "friend",
            }
            namespaces_to_strip = {"std::"}

        def clean_type(name: str) -> str:
            if not isinstance(name, str):
                return ""
            # Don't strip * & for display
            name = re.sub(r"\s*=[^,]+", "", name)
            name = re.sub(r"\[.*?\]", "", name)

            parts = name.split()
            core_parts = [p for p in parts if p and p not in modifiers]
            if not core_parts:
                return ""

            cleaned_name = " ".join(core_parts)

            for ns in namespaces_to_strip:
                if cleaned_name.startswith(ns):
                    cleaned_name = cleaned_name[len(ns) :]

            if self._language_context == FileTypeEnum.CPP and cleaned_name.startswith(
                "::"
            ):
                cleaned_name = cleaned_name[2:]

            if self._language_context == FileTypeEnum.JAVA:
                cleaned_name = cleaned_name.replace("...", "").strip()

            # Consolidate pointer/ref spacing for display
            if self._language_context == FileTypeEnum.CPP:
                cleaned_name = cleaned_name.replace(" *", "*").replace(" &", "&")

            return cleaned_name.strip()

        return clean_type

    def _should_ignore_type(self, type_name: str) -> bool:
        """Checks if a type should be ignored for relationships, using BASE type."""
        if not type_name:
            return True
        # Clean * & for the check against ignore list
        base_type_name = type_name.replace("*", " ").replace("&", " ").strip()
        # Use the display cleaner just to remove keywords/namespaces before checking ignore list
        cleaned_base_name = self.type_cleaner(base_type_name)
        if not cleaned_base_name:
            return True

        # Check the cleaned base name against the ignore list
        if cleaned_base_name in self.dataTypeToIgnore:
            return True

        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"
        simple_base_name = cleaned_base_name.split(separator)[-1]
        if simple_base_name in self.dataTypeToIgnore:
            return True

        # Special check for template/generic parameters (single uppercase letters) - Apply to all languages
        if len(cleaned_base_name) == 1 and "A" <= cleaned_base_name <= "Z":
            return True

        return False

    def drawUml(self, classInfo: ClassNode):
        plantUmlList = list()
        plantUmlList.append("@startuml")
        plantUmlList.append("hide empty members")
        plantUmlList.append("skinparam classAttributeIconSize 0")
        simple_name = (
            classInfo.name.split("::")[-1] if "::" in classInfo.name else classInfo.name
        )
        temp_node_for_dump = ClassNode(**vars(classInfo))
        temp_node_for_dump.name = simple_name

        plantUmlList.extend(self.dump_single_class_definition(temp_node_for_dump))
        plantUmlList.extend(self.dump_relations_for_class(classInfo, {}, {}))
        plantUmlList.append("@enduml")
        plantUmlList = list(dict.fromkeys(plantUmlList))
        filePath = (
            "static/out/data_" + self.sanitize_filename(classInfo.name) + "_uml.puml"
        )
        if self.write_list_to_file(filePath, plantUmlList):
            print(f"Generated single UML: {filePath}")
            self.generatePng(filePath)
        else:
            print(f"Failed to write single UML file: {filePath}")

    def draw_multiple_uml(self, listOfClassNodes: list[ClassNode], base_filename: str):
        if not listOfClassNodes:
            print("No class nodes provided for consolidated UML.")
            return
        plantUmlList = ["@startuml"]
        plantUmlList.append("' Consolidated UML Diagram")
        plantUmlList.append("hide empty members")
        plantUmlList.append("skinparam classAttributeIconSize 0")
        plantUmlList.append("skinparam packageStyle rectangle")
        packages = defaultdict(list)
        qualified_name_map: Dict[str, ClassNode] = {}
        simple_name_map: Dict[str, List[str]] = {}
        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"

        for node in listOfClassNodes:
            qualified_name = self._get_qualified_name(node)
            if qualified_name:
                qualified_name_map[qualified_name] = node
                simple_name = qualified_name.split(separator)[-1].split("<")[0]
                if simple_name:
                    if simple_name not in simple_name_map:
                        simple_name_map[simple_name] = []
                    simple_name_map[simple_name].append(qualified_name)
        for node in listOfClassNodes:
            package_name = (
                node.package.replace("::", ".") if node.package else "default"
            )
            packages[package_name].append(node)
        for package_name, classes_in_package in sorted(packages.items()):
            if package_name != "default":
                plantUmlList.append(f'package "{package_name}" {{')
            classes_in_package.sort(key=lambda x: self._get_qualified_name(x))
            for classInfo in classes_in_package:
                plantUmlList.extend(self.dump_single_class_definition(classInfo))
            if package_name != "default":
                plantUmlList.append("}")
            plantUmlList.append("")

        plantUmlList.append("' Relationships")
        all_relations = set()
        for classInfo in listOfClassNodes:
            relation_lines = self.dump_relations_for_class(
                classInfo, qualified_name_map, simple_name_map
            )
            all_relations.update(relation_lines)

        plantUmlList.extend(sorted(list(all_relations)))
        plantUmlList.append("@enduml")

        output_puml_path = Path("static/out") / f"{base_filename}.puml"
        if self.write_list_to_file(str(output_puml_path), plantUmlList):
            print(f"Generated consolidated UML: {str(output_puml_path)}")
            self.generatePng(str(output_puml_path))
        else:
            print(f"Failed to write consolidated UML file: {str(output_puml_path)}")

    def _get_qualified_name(self, classInfo: ClassNode) -> str:
        """Gets the BASE qualified name (no trailing * &) for identification."""
        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"
        name_part = classInfo.name
        if classInfo.params:
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
        if not isinstance(name_str, str):
            return ""
        name_str = name_str.strip()

        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"
        alt_separator = "::" if self._language_context == FileTypeEnum.JAVA else "."

        if separator in name_str:
            if self._language_context == FileTypeEnum.CPP and name_str.startswith(
                "std::"
            ):
                return name_str[5:]
            return name_str
        elif alt_separator in name_str:
            return name_str

        if self._should_ignore_type(name_str):
            return name_str

        elif current_package:
            return f"{current_package}{separator}{name_str}"
        else:
            return name_str

    def dump_single_class_definition(self, classInfo: ClassNode) -> list[str]:
        """Dumps definition using BASE name for class ID, but FULL types for members."""
        definition = []
        class_type = "interface" if classInfo.isInterface else "class"
        # Use BASE qualified name for the definition ID
        qualified_name = self._get_qualified_name(classInfo)
        name_for_plantuml = self._quote_if_needed(qualified_name)  # Quote the BASE name

        stereotype_parts = []
        if classInfo.isAbstract and not classInfo.isInterface:
            stereotype_parts.append("abstract")
        if classInfo.isFinal:
            stereotype_parts.append("final")
        stereotype = f"<< { ' '.join(stereotype_parts) } >>" if stereotype_parts else ""
        definition.append(f"{class_type} {name_for_plantuml} {stereotype} {{")

        # Use the DISPLAY cleaner (keeps * &) for member types
        display_cleaner = self._get_type_cleaner()

        for var in sorted(classInfo.variables, key=lambda x: x.name):
            access = self._get_access_symbol(var.accessLevel)
            static_marker = "{static}" if var.isStatic else ""
            var_type_display = self._quote_if_needed(display_cleaner(var.dataType))
            definition.append(
                f"  {access} {static_marker} {var_type_display} {var.name}".strip()
            )

        for method in sorted(classInfo.methods, key=lambda x: x.name):
            access = self._get_access_symbol(method.accessLevel)
            stereotype_m_parts = []
            if method.isStatic:
                stereotype_m_parts.append("static")
            if method.isAbstract:
                stereotype_m_parts.append("abstract")
            method_stereotype = (
                f"{{ { ' '.join(stereotype_m_parts) } }}" if stereotype_m_parts else ""
            )

            # Use original params (includes * &) cleaned for display
            params_list = [
                self._quote_if_needed(display_cleaner(p)) for p in method.params
            ]
            params_str = ", ".join(params_list)

            return_type_display = ""
            if method.dataType:
                # Use original return type (includes * &) cleaned for display
                cleaned_return_type_display = display_cleaner(method.dataType)
                # Only show return type if not void (or implicit constructor/destructor)
                if (
                    cleaned_return_type_display
                    and cleaned_return_type_display.lower() != "void"
                ):
                    return_type_display = (
                        f": {self._quote_if_needed(cleaned_return_type_display)}"
                    )

            method_name_display = self._quote_if_needed(method.name)

            definition.append(
                f"  {access} {method_stereotype} {method_name_display}({params_str}){return_type_display}".strip()
            )

        definition.append("}")
        return definition

    def dump_relations_for_class(
        self,
        classInfo: ClassNode,
        qualified_name_map: Dict[str, ClassNode],  # Map uses BASE names as keys
        simple_name_map: Dict[str, List[str]],  # Map uses BASE names
    ) -> list[str]:
        """Dumps relationships using BASE names for source and target."""
        plantUmlList = []
        # Use BASE qualified name for source
        source_name_qualified = self._get_qualified_name(classInfo)
        source_name_quoted = self._quote_if_needed(source_name_qualified)
        processed_targets = set()

        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"

        for relation in classInfo.relations:
            try:
                # relation.name is already the BASE type from CppClassAnalyzer
                target_name_original_base = relation.name
                if not target_name_original_base:
                    continue

                # Qualify the BASE target name
                target_name_full_base = self._get_qualified_name_from_string(
                    target_name_original_base, classInfo.package
                )

                # Resolve BASE target against known BASE classes
                resolved_target_base = target_name_full_base
                if target_name_full_base not in qualified_name_map:
                    simple_target_name_base = target_name_full_base.split(separator)[
                        -1
                    ].split("<")[0]
                    possible_matches = simple_name_map.get(simple_target_name_base, [])
                    if len(possible_matches) == 1:
                        resolved_target_base = possible_matches[
                            0
                        ]  # BASE qualified name

                # Check ignore using the BASE name
                if not self._should_ignore_type(resolved_target_base):
                    arrow = ""
                    relation_type = relation.relationship
                    if relation_type == InheritanceEnum.DEPENDED:
                        arrow = "..>"
                    elif relation_type == InheritanceEnum.IMPLEMENTED:
                        arrow = "..|>"
                    elif relation_type == InheritanceEnum.EXTENDED:
                        arrow = "--|>"

                    if arrow:
                        # Quote the BASE target name
                        resolved_target_quoted = self._quote_if_needed(
                            resolved_target_base
                        )
                        link_tuple = (source_name_quoted, arrow, resolved_target_quoted)
                        if link_tuple not in processed_targets:
                            plantUmlList.append(
                                f"{source_name_quoted} {arrow} {resolved_target_quoted}"
                            )
                            processed_targets.add(link_tuple)
            except Exception as e:
                print(
                    f"Warning: Error processing relation for PlantUML ({source_name_qualified} -> {relation.name}): {e}"
                )

        return plantUmlList

    def get_variable_dependencies(self, listOfVariables) -> set:
        deps = set()
        for var in listOfVariables:
            if not self._should_ignore_type(var.dataType):
                deps.add(var.dataType)
        return deps

    def get_method_dependencies(self, listOfMethods) -> set:
        deps = set()
        for method in listOfMethods:
            if method.dataType and not self._should_ignore_type(method.dataType):
                deps.add(method.dataType)
            for param_type in method.params:
                if not self._should_ignore_type(param_type):
                    deps.add(param_type)
        return deps

    def _get_access_symbol(self, accessLevel: AccessEnum) -> str:
        if accessLevel == AccessEnum.PUBLIC:
            return "+"
        if accessLevel == AccessEnum.PRIVATE:
            return "-"
        if accessLevel == AccessEnum.PROTECTED:
            return "#"
        return "~"

    def sanitize_filename(self, name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        name = name.replace("::", "_")
        return name

    def generatePng(self, filepath):
        project_root = (
            Path(__file__).resolve().parent.parent.parent
        )  # Navigate up to project root (KudSight)
        app_root = project_root / "app"  # Path to app directory

        plantuml_jar_path_abs = (project_root / "app/plantuml/plantuml.jar").resolve()

        if not plantuml_jar_path_abs.exists():
            print(
                f"Error: plantuml.jar not found at expected location: {plantuml_jar_path_abs}"
            )
            return

        # Absolute path to the input PUML file
        puml_path_abs = Path(filepath).resolve()

        # Ensure the input file path is relative to the project root for the command if needed
        try:
            puml_path_rel_to_project = puml_path_abs.relative_to(project_root)
        except ValueError:
            # If the puml file is somehow outside the project root, use absolute
            print(
                f"Warning: PUML file {puml_path_abs} seems outside project root {project_root}. Using absolute path."
            )
            puml_path_rel_to_project = puml_path_abs

        # Output directory relative to project root (e.g., "app/static/out")
        output_directory_rel = Path("app") / "static" / "out"
        output_directory_abs = (
            project_root / output_directory_rel
        )  # Absolute path for mkdir

        # Ensure the output directory exists
        output_directory_abs.mkdir(parents=True, exist_ok=True)

        # Use relative output path and potentially relative input path in the command
        # Run the command from the project root directory
        command = f'java -jar "{plantuml_jar_path_abs}" -output "{output_directory_abs}" "{puml_path_rel_to_project}"'
        working_directory = project_root

        print(f"Executing in '{working_directory}': {command}")
        try:
            import subprocess

            process = subprocess.run(
                command,
                shell=True,
                cwd=working_directory,
                capture_output=True,
                text=True,
            )

            if process.returncode == 0:
                png_filename = puml_path_abs.with_suffix(".png").name
                print(
                    f"Successfully generated PNG: {output_directory_abs / png_filename}"
                )
                if process.stdout:
                    print(f"PlantUML STDOUT:\n{process.stdout}")
            else:
                print(
                    f"Error generating PNG for: {filepath} (Exit code: {process.returncode})"
                )
                if process.stdout:
                    print(f"PlantUML STDOUT:\n{process.stdout}")
                if process.stderr:
                    print(f"PlantUML STDERR:\n{process.stderr}")
        except Exception as e:
            print(f"Exception generating PNG for {filepath}: {e}")

    def write_list_to_file(self, file_path, list_of_str):
        try:
            with open(file_path, "w+") as f:
                f.write("\n".join(list_of_str))
            return True
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")
            return False

    def _quote_if_needed(self, name):
        if not isinstance(name, str):
            return ""
        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"
        if (
            re.search(r"[<> *&]", name)
            or separator in name
            or name in self.dataTypeToIgnore
        ):
            if not (name.startswith('"') and name.endswith('"')):
                name = name.replace('"', '\\"')
                return '"' + name + '"'
        return name


if __name__ == "__main__":
    print(sys.argv)
    test_file_type = FileTypeEnum.CPP
    classInfo = ClassNode(package="MyTest", name="TestClass", params=["T"])
    classInfo.relations.append(Inheritance("MyTest::Class1", InheritanceEnum.DEPENDED))
    classInfo.relations.append(Inheritance("Another::Class2", InheritanceEnum.EXTENDED))
    classInfo.relations.append(Inheritance("int", InheritanceEnum.DEPENDED))
    classUmlDrawer = ClassUmlDrawer(test_file_type)
    classUmlDrawer.drawUml(classInfo)
