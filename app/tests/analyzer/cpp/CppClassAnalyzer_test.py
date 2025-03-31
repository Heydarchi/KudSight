import unittest
from analyzer.cpp.CppClassAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum
from PythonUtilityClasses.FileReader import FileReader
import re


class TestCppClassAnalyzer(unittest.TestCase):
    def test_init_patterns(self):
        # Check if the variables are initialized properly
        classAnalyzer = CppClassAnalyzer()
        self.assertNotEqual(classAnalyzer.pattern, None)

    def test_find_class_pattern_cpp(self):
        # Check if the class pattern is found correctly in a Cpp input string
        classAnalyzer = CppClassAnalyzer()
        inputStr = "public class TestClass {"

        for pattern in classAnalyzer.pattern:
            match = classAnalyzer.find_class_pattern(pattern, inputStr)
            self.assertEqual(
                inputStr[match.start() : match.end()], "public class TestClass {"
            )

    def test_find_class_pattern_cpp_with_inheritance(self):
        # Check if the class pattern is found correctly in a Cpp input string with inheritance
        classAnalyzer = CppClassAnalyzer()
        inputStr = (
            "public class TestClass : public AbstractTestClass2, public SuperTestClass{"
        )
        for pattern in classAnalyzer.pattern:
            match = classAnalyzer.find_class_pattern(pattern, inputStr)
            self.assertEqual(
                inputStr[match.start() : match.end()],
                "public class TestClass : public AbstractTestClass2, public SuperTestClass{",
            )

    def test_find_class_pattern_cpp_with_inheritance_and_comments(self):
        # Check if the class pattern is found correctly in a Cpp input string with inheritance and comments
        classAnalyzer = CppClassAnalyzer()
        inputStr = "/* This is a comment */ public class TestClass : public AbstractTestClass2, public SuperTestClass{"
        for pattern in classAnalyzer.pattern:
            match = classAnalyzer.find_class_pattern(pattern, inputStr)
            self.assertEqual(
                inputStr[match.start() : match.end()],
                " public class TestClass : public AbstractTestClass2, public SuperTestClass{",
            )

    def test_extract_class_name_cpp(self):
        # Check if the class name is extracted properly in a C++ input string
        classAnalyzer = CppClassAnalyzer()
        inputStr = "class TestClass {"
        className = classAnalyzer.extract_class_name(inputStr)
        self.assertEqual(className, "TestClass")

    def test_extract_class_name_cpp_with_inheritance(self):
        # Check if the class name is extracted properly in a C++ input string with inheritance
        classAnalyzer = CppClassAnalyzer()
        inputStr = (
            "class TestClass : public AbstractTestClass2, public SuperTestClass {"
        )
        className = classAnalyzer.extract_class_name(inputStr)
        self.assertEqual(className, "TestClass")

    # def test_extract_class_inheritances(self):
    #    self.fail()

    # def test_extract_class_spec(self):
    #    self.fail()
