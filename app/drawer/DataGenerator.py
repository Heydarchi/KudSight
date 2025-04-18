import os, sys
from model.AnalyzerEntities import *
from model.DataGeneratorEntities import *
# --- Start Change: Import ClassUmlDrawer for its filtering logic ---
from drawer.ClassUmlDrawer import ClassUmlDrawer # Assuming CPP for now, might need adjustment for multi-lang
# --- End Change ---

from utils.FileWriter import *
from datetime import datetime


class DataGenerator:
    def __init__(self) -> None:
        self.graphData = GraphData()
        # --- Start Change: Instantiate a drawer to use its filtering ---
        # TODO: Handle multi-language scenarios appropriately if needed
        try:
            # Assuming CPP context for filtering based on the example
            self._uml_drawer_for_filtering = ClassUmlDrawer(FileTypeEnum.CPP)
        except Exception as e:
            print(f"Warning: Could not instantiate ClassUmlDrawer for filtering: {e}")
            self._uml_drawer_for_filtering = None
        # --- End Change ---


    def generateData(self, listOfClassNodes: list[ClassNode]):
        dataList = list()

        for node in listOfClassNodes:
            self.dumpClass(node)

        # --- Start Change: Add blank classes *before* removing duplicates ---
        # This ensures referenced nodes exist before duplicate removal logic
        self.graphData.add_blank_classes()
        # --- End Change ---
        
        # --- Start Change: Remove duplicates *after* adding all nodes/links ---
        self.graphData.remove_duplicates()
        # --- End Change ---

        json_output = self.graphData.to_json()

        date_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        filePath = "static/out/data" + date_time + ".json"
        self.writeToFile(filePath, json_output)

    def dumpClass(self, classInfo: ClassNode):
        # --- Start Debug Logging ---
        print(f"DataGenerator dumping: {classInfo.name}")
        print(f"  - Package: {classInfo.package}")
        print(f"  - Variables: {classInfo.variables}")
        print(f"  - Relations: {classInfo.relations}")
        # --- End Debug Logging ---

        classData = ClassData()
        classData.package = classInfo.package if classInfo.package is not None else ""
        # --- Start Change: Use fix_name_issue for ID consistency ---
        classData.id = self.fix_name_issue(classInfo.name)
        # Add template params to ID if they exist, similar to UML drawer logic
        if classInfo.params:
             classData.id = f'"{classInfo.name}<{", ".join(classInfo.params)}>"'
        # --- End Change ---
        classData.type = "interface" if classInfo.isInterface else "class" # Set type based on flag

        # --- Start Change: Add flags ---
        classData.isAbstract = classInfo.isAbstract
        classData.isFinal = classInfo.isFinal
        classData.isStatic = classInfo.isStatic
        # --- End Change ---

        # Include methods by name
        classData.methods = [
            method.name if hasattr(method, "name") else str(method)
            for method in classInfo.methods
        ]

        # --- Start Debug Logging for Attributes ---
        attributes_to_add = []
        print(f"  - Processing variables for {classInfo.name}:")
        for var in classInfo.variables:
            if var.name not in ["return"]:
                # Ensure var has expected attributes before formatting
                try:
                    attr_str = f"{var.accessLevel.name.lower()} {'static ' if var.isStatic else ''}{var.dataType} {var.name}".replace(";", "").strip()
                    attributes_to_add.append(attr_str)
                    print(f"    - Adding attribute: {attr_str}")
                except AttributeError as e:
                    print(f"    - Error processing variable {var}: {e}")
            else:
                print(f"    - Skipping variable named 'return': {var}")
        classData.attributes = attributes_to_add
        # --- End Debug Logging for Attributes ---

        self.graphData.nodes.append(classData)

        # --- Start Change: Use potentially templated ID for source ---
        print(f"  - Processing relations for {classData.id}:") # Use the potentially templated ID
        for relation in classInfo.relations:
            try:
                target_name_raw = relation.name
                target_name_fixed = self.fix_name_issue(target_name_raw)
                # Add template params to target if it's a known templated class (more advanced, skip for now)

                # Use the drawer's filtering logic if available
                should_ignore = False
                if self._uml_drawer_for_filtering:
                    # Pass the raw name for filtering check
                    should_ignore = self._uml_drawer_for_filtering._should_ignore_type(target_name_raw)
                else:
                    # Basic fallback if drawer init failed (less accurate)
                    if target_name_fixed.lower() in ["string", "int", "void", "char", "bool", "t"]:
                         should_ignore = True

                if not should_ignore:
                    dependency = Dependency()
                    dependency.source = classData.id # Use the potentially templated source ID
                    dependency.target = target_name_fixed # Use fixed target name
                    # Add template params to target if needed (complex)
                    # if target_name_raw in known_template_classes:
                    #    dependency.target = f'"{target_name_raw}<...>"' # Placeholder

                    dependency.relation = relation.relationship.name.lower()
                    print(f"    - Adding link: {dependency.source} -> {dependency.target} ({dependency.relation})")
                    self.graphData.links.append(dependency)
                else:
                    print(f"    - Skipping ignored/primitive relation: {classData.id} -> {target_name_fixed} ({relation.relationship.name.lower()})")

            except AttributeError as e:
                print(f"    - Error processing relation {relation}: {e}")
        # --- End Change ---

    def writeToFile(self, fileName, json_output):
        with open(fileName, "w") as f:
            f.write(json_output)

    def fix_name_issue(self, name):
        if not isinstance(name, str):
            return ""
        # Keep quoting for names containing '<' or '>' only if NOT handled by template logic
        # This function is now simpler, mainly for ensuring string type
        # Quoting for templates is handled in dumpClass and ClassUmlDrawer directly
        return name


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
