import os
import sys
from analyzer.common import AnalyzerHelper  # if needed elsewhere
from analyzer.java.JavaClassAnalyzer import JavaClassAnalyzer
from analyzer.cpp.CppClassAnalyzer import CppClassAnalyzer
from analyzer.kotlin.KotlinClassAnalyzer import KotlinClassAnalyzer
from analyzer.csharp.CSharpClassAnalyzer import CSharpClassAnalyzer
from model.AnalyzerEntities import FileTypeEnum
from utils.SystemUtility import *
from drawer.DataGenerator import DataGenerator
from analyzer.AbstractAnalyzer import AbstractAnalyzer
from drawer.ClassUmlDrawer import *

class FileAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        if not os.path.exists("static/out"):
            os.makedirs("static/out")

    def analyze(self, targetPath, pattern=None):
        systemUtility = SystemUtility()
        listOfFiles = systemUtility.get_list_of_files(targetPath, "*")
        print(listOfFiles)

        listOfClassNodes = []
        analyzed_languages = set()  # Keep track of languages found

        for filePath in listOfFiles:
            language = self.detectLang(filePath)
            if language != FileTypeEnum.UNDEFINED:
                print(f"- Analyzing: {filePath} {language}")
                analyzed_languages.add(language)  # Record the language
                classAnalyzer = self.get_class_analyzer(language)
                if classAnalyzer:
                    try:
                        listOfClasses = classAnalyzer.analyze(filePath, language)
                        listOfClassNodes.extend(listOfClasses)
                    except Exception as e:
                        print(f"ERROR analyzing file {filePath}: {e}")  # Add error logging
            else:
                print(f"- Skipping unsupported file: {filePath}")

        if listOfClassNodes:
            primary_language = list(analyzed_languages)[0] if len(analyzed_languages) == 1 else FileTypeEnum.CPP  # Simple heuristic
            print(f"Generating consolidated UML for language context: {primary_language.name}")
            try:
                umlDrawer = ClassUmlDrawer(primary_language)
                umlDrawer.draw_multiple_uml(listOfClassNodes, "consolidated_uml.puml")
            except Exception as e:
                print(f"ERROR generating consolidated UML: {e}")
        else:
            print("No classes found to generate consolidated UML.")

        self.generateData(listOfClassNodes)

    def get_class_analyzer(self, language):
        if language == FileTypeEnum.JAVA:
            return JavaClassAnalyzer()
        elif language == FileTypeEnum.CPP:
            return CppClassAnalyzer()
        elif language == FileTypeEnum.KOTLIN:
            return KotlinClassAnalyzer()
        elif language == FileTypeEnum.CSHARP:
            return CSharpClassAnalyzer()
        return None

    def generateData(self, listOfClassNodes):
        dataGenerator = DataGenerator()
        dataGenerator.generateData(listOfClassNodes)

    def detectLang(self, fileName):
        if fileName.endswith(".java"):
            return FileTypeEnum.JAVA
        elif (
            fileName.endswith(".cpp")
            or fileName.endswith(".h")
            or fileName.endswith(".hpp")
        ):
            return FileTypeEnum.CPP
        elif fileName.endswith(".cs"):
            return FileTypeEnum.CSHARP
        elif fileName.endswith(".kt"):
            return FileTypeEnum.KOTLIN
        else:
            return FileTypeEnum.UNDEFINED


if __name__ == "__main__":
    print(sys.argv)
    fileAnalyzer = FileAnalyzer()
    fileAnalyzer.analyze(sys.argv[1])
