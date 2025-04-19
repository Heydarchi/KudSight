import unittest
from analyzer.java.JavaVariableAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum, AccessEnum
from utils.FileReader import FileReader
import re


class TestJavaVariableAnalyzer(unittest.TestCase):
    def test_init_patterns(self):
        # Check if the variables are initialized properly
        variableAnalyzer = JavaVariableAnalyzer()
        self.assertNotEqual(variableAnalyzer.pattern, None)

    def test_basic_variable_pattern(self):
        # Test detection of basic variable declaration
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = "private int counter;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "private")
        self.assertEqual(match.group(4).strip(), "int")
        self.assertEqual(match.group(5), "counter")

    def test_static_variable_pattern(self):
        # Test detection of static variable
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = "private static final int MAX_VALUE = 100;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "private")
        self.assertEqual(match.group(2), "static")
        self.assertEqual(match.group(3), "final")
        self.assertEqual(match.group(4).strip(), "int")
        self.assertEqual(match.group(5), "MAX_VALUE")

    def test_generic_variable_pattern(self):
        # Test detection of variable with generic type
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = "private List<String> names;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "private")
        self.assertEqual(match.group(4).strip(), "List<String>")
        self.assertEqual(match.group(5), "names")

    def test_array_variable_pattern(self):
        # Test detection of array variable
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = "private int[] scores;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "private")
        self.assertEqual(match.group(4).strip(), "int[]")
        self.assertEqual(match.group(5), "scores")

    def test_nested_generic_variable_pattern(self):
        # Test detection of nested generic variable
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = "private Map<String, List<User>> userGroups;"

        match = re.search(variableAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "private")
        self.assertEqual(match.group(4).strip(), "Map<String, List<User>>")
        self.assertEqual(match.group(5), "userGroups")

    def test_extract_variable_info_basic(self):
        # Test extraction of basic variable info
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = "private int counter = 0;"
        match = re.search(variableAnalyzer.pattern, inputStr)
        variableInfo = variableAnalyzer.extractVariableInfo(match)

        self.assertEqual(variableInfo.name, "counter")
        self.assertEqual(variableInfo.dataType, "int")
        self.assertEqual(variableInfo.accessLevel, AccessEnum.PRIVATE)
        self.assertFalse(variableInfo.isStatic)
        self.assertFalse(variableInfo.isFinal)

    def test_extract_variable_info_public_static_final(self):
        # Test extraction of public static final variable info
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = 'public static final String VERSION = "1.0";'
        match = re.search(variableAnalyzer.pattern, inputStr)
        variableInfo = variableAnalyzer.extractVariableInfo(match)

        self.assertEqual(variableInfo.name, "VERSION")
        self.assertEqual(variableInfo.dataType, "String")
        self.assertEqual(variableInfo.accessLevel, AccessEnum.PUBLIC)
        self.assertTrue(variableInfo.isStatic)
        self.assertTrue(variableInfo.isFinal)

    def test_extract_variable_info_protected(self):
        # Test extraction of protected variable info
        variableAnalyzer = JavaVariableAnalyzer()
        inputStr = "protected List<Integer> values;"
        match = re.search(variableAnalyzer.pattern, inputStr)
        variableInfo = variableAnalyzer.extractVariableInfo(match)

        self.assertEqual(variableInfo.name, "values")
        self.assertEqual(variableInfo.dataType, "List<Integer>")
        self.assertEqual(variableInfo.accessLevel, AccessEnum.PROTECTED)

    def test_analyze_class_content(self):
        # Test analyzing variables in class content
        variableAnalyzer = JavaVariableAnalyzer()
        class_content = """
        public class MyClass {
            private int id;
            private String name;
            public static final int MAX_SIZE = 100;
            protected List<String> items;
        }
        """

        variables = variableAnalyzer.analyze(None, None, class_content)
        self.assertEqual(len(variables), 4)

        # Check that we have private, public, and protected variables
        private_vars = [v for v in variables if v.accessLevel == AccessEnum.PRIVATE]
        public_vars = [v for v in variables if v.accessLevel == AccessEnum.PUBLIC]
        protected_vars = [v for v in variables if v.accessLevel == AccessEnum.PROTECTED]

        self.assertEqual(len(private_vars), 2)
        self.assertEqual(len(public_vars), 1)
        self.assertEqual(len(protected_vars), 1)

        # Verify static final variable was detected
        static_final_vars = [v for v in variables if v.isStatic and v.isFinal]
        self.assertEqual(len(static_final_vars), 1)
        self.assertEqual(static_final_vars[0].name, "MAX_SIZE")

        # Verify generic type variable
        generic_vars = [v for v in variables if "<" in v.dataType]
        self.assertEqual(len(generic_vars), 1)
        self.assertEqual(generic_vars[0].name, "items")
