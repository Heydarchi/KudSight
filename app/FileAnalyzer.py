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


class FileAnalyzer(AbstractAnalyzer):
    def __init__(self) -> None:
        if not os.path.exists("static/out"):
            os.makedirs("static/out")

    def analyze(self, targetPath, pattern=None):
        systemUtility = SystemUtility()
        listOfFiles = systemUtility.get_list_of_files(targetPath, "*")
        print(listOfFiles)

        listOfClassNodes = []
        for filePath in listOfFiles:
            language = self.detectLang(filePath)
            if language != FileTypeEnum.UNDEFINED:
                print(f"- Analyzing: {filePath} {language}")
                classAnalyzer = self.get_class_analyzer(language)
                if classAnalyzer:
                    listOfClasses = classAnalyzer.analyze(filePath, language)
                    listOfClassNodes.extend(listOfClasses)
            else:
                print(f"- Skipping unsupported file: {filePath}")

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
