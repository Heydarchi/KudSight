import unittest
from analyzer.java.JavaClassAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum
from utils.FileReader import FileReader
import re


class TestJavaClassAnalyzer(unittest.TestCase):
    def test_init_patterns(self):
        # Check if the variables are initialized properly
        classAnalyzer = JavaClassAnalyzer()
        self.assertNotEqual(classAnalyzer.pattern, None)

    def test_find_class_pattern_java(self):
        # Check if the class pattern is found correctly in a Java input string
        classAnalyzer = JavaClassAnalyzer()
        inputStr = "public class TestClass {"

        for pattern in classAnalyzer.pattern:
            match = classAnalyzer.find_class_pattern(pattern, inputStr)
            self.assertEqual(
                inputStr[match.start() : match.end()], "public class TestClass {"
            )

    def test_find_class_pattern_java_with_inheritance(self):
        # Check if the class pattern is found correctly in a Java input string with inheritance
        classAnalyzer = JavaClassAnalyzer()
        inputStr = "public class TestClass extends AbstractTestClass2 implements SuperTestClass{"
        for pattern in classAnalyzer.pattern:
            match = classAnalyzer.find_class_pattern(pattern, inputStr)
            self.assertEqual(
                inputStr[match.start() : match.end()],
                "public class TestClass extends AbstractTestClass2 implements SuperTestClass{",
            )

    def test_find_class_pattern_java_with_inheritance_and_comments(self):
        # Check if the class pattern is found correctly in a Java input string with inheritance and comments
        classAnalyzer = JavaClassAnalyzer()
        inputStr = """/* This is a comment */
        public class TestClass extends AbstractTestClass2 implements SuperTestClass{"""
        for pattern in classAnalyzer.pattern:
            match = classAnalyzer.find_class_pattern(pattern, inputStr)

            # Update the expected match to include the full match with comment and whitespace
            self.assertEqual(
                inputStr[match.start() : match.end()],
                """/* This is a comment */
        public class TestClass extends AbstractTestClass2 implements SuperTestClass{""",
            )

    def test_extract_class_name_java(self):
        # Check if the class name is extracted properly in a Java input string
        classAnalyzer = JavaClassAnalyzer()
        inputStr = "public class TestClass {"
        className = classAnalyzer.extract_class_name(inputStr)
        self.assertEqual(className, "TestClass")

    def test_extract_class_name_java_with_inheritance(self):
        # Check if the class name is extracted properly in a Java input string with inheritance
        classAnalyzer = JavaClassAnalyzer()
        inputStr = "public class TestClass extends AbstractTestClass2 implements SuperTestClass{"
        className = classAnalyzer.extract_class_name(inputStr)
        self.assertEqual(className, "TestClass")
