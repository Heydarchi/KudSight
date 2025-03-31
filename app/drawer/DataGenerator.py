import os, sys
from model.AnalyzerEntities import *
from model.DataGeneratorEntities import *

from PythonUtilityClasses import FileWriter as FW
from datetime import datetime


class DataGenerator:
    def __init__(self) -> None:
        self.graphData = GraphData()
        self.mapList = list()
        self.mapList.append(UmlRelationMap("", InheritanceEnum.DEPENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.EXTENDED))
        self.mapList.append(UmlRelationMap("", InheritanceEnum.IMPLEMENTED))

        self.dataTypeToIgnore = [
            "boolean",
            "byte",
            "char",
            "short",
            "int",
            "long",
            "float",
            "double",
            "void",
            "Int",
            "return",
            "var",
        ]

    def generateData(self, listOfClassNodes: list[ClassNode]):
        dataList = list()

        for node in listOfClassNodes:
            self.dumpClass(node)

        json_output = self.graphData.to_json()

        date_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        filePath = "static/out/data" + date_time + ".json"
        self.writeToFile(filePath, json_output)

    def dumpClass(self, classInfo: ClassNode):
        classData = ClassData()
        classData.package = classInfo.package or ""  # Default to empty string
        classData.id = classInfo.name
        classData.type = "class"  # Explicitly set type

        # Include methods by name
        classData.methods = [
            method.name if hasattr(method, "name") else str(method)
            for method in classInfo.methods
        ]

        classData.attributes = [
            f"{var.accessLevel.name.lower()} {'static ' if var.isStatic else ''}{var.dataType} {var.name}".replace(
                ";", ""
            ).strip()
            for var in classInfo.variables
            if var.name not in ["return"]  # Avoid junk extracted from method bodies
        ]

        self.graphData.nodes.append(classData)

        # Include relationships
        for relation in classInfo.relations:
            dependency = Dependency()
            dependency.source = classInfo.name
            dependency.target = self.fix_name_issue(relation.name)
            dependency.relation = relation.relationship.name.lower()
            self.graphData.links.append(dependency)

    def writeToFile(self, fileName, json_output):
        with open(fileName, "w") as f:
            f.write(json_output)

    def fix_name_issue(self, name):
        if ">" in name or "<" in name:
            return '"' + name + '"'
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
