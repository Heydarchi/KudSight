import unittest
from analyzer.cpp.CppMethodAnalyzer import *
from model.AnalyzerEntities import FileTypeEnum
from utils.FileReader import FileReader
import re
import os


class TestCppMethodAnalyzer(unittest.TestCase):
    def test_init_patterns(self):
        # Check if the variables are initialized properly
        methodAnalyzer = CppMethodAnalyzer()
        self.assertNotEqual(methodAnalyzer.pattern, None)

    def test_find_method_pattern_cpp(self):
        # Check if the method pattern is found correctly in a C++ input string
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void TestMethod(int param1, string param2) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "void TestMethod(int param1, string param2) {",
        )

    def test_find_method_pattern_cpp_with_return_type(self):
        # Check if the method pattern is found correctly with complex return type
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "std::vector<int> TestMethod(int param1, std::string param2) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "std::vector<int> TestMethod(int param1, std::string param2) {",
        )

    def test_find_method_pattern_cpp_with_const_method(self):
        # Check if the method pattern is found correctly with const qualifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "int TestMethod(double value) const {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertEqual(
            inputStr[match.start() : match.end()],
            "int TestMethod(double value) const {",
        )

    def test_extract_method_info_cpp(self):
        # Check if the method info is extracted properly in a C++ input string
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void TestMethod(int param1) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PRIVATE
        )
        self.assertEqual(methodInfo.name, "TestMethod")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PRIVATE)

    def test_extract_method_info_cpp_with_class_scope(self):
        # Check if the method info is extracted properly with class scope operator
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void MyClass::TestMethod(int param1) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "TestMethod")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertEqual(methodInfo.accessLevel, AccessEnum.PUBLIC)

    def test_extract_params_cpp(self):
        # Check if parameters are extracted properly
        methodAnalyzer = CppMethodAnalyzer()
        params_str = "int param1, std::string param2"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "int")
        self.assertEqual(params[1], "std::string")

    def test_extract_params_cpp_with_complex_types(self):
        # Check if complex parameter types are extracted properly
        methodAnalyzer = CppMethodAnalyzer()
        params_str = "const std::vector<int>& vec, std::shared_ptr<MyClass> ptr"
        params = methodAnalyzer.extractParams(params_str)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "std::vector<int>&")
        self.assertEqual(params[1], "std::shared_ptr<MyClass>")

    def test_constructor_detection(self):
        # Test constructor detection
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "MyClass(int value, std::string name) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "MyClass")
        self.assertIsNone(methodInfo.dataType)  # Constructor should have no return type

    def test_destructor_detection(self):
        # Test destructor detection
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "~MyClass() {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "~MyClass")
        self.assertIsNone(methodInfo.dataType)  # Destructor should have no return type

    def test_abstract_method(self):
        # Test pure virtual (abstract) method detection
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "virtual void process() = 0;"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "process")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertTrue(methodInfo.isAbstract)

    def test_template_method(self):
        # Test method with template parameters
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "template<typename T> T convert(const std::string& value) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "convert")
        self.assertEqual(methodInfo.dataType, "T")

    def test_operator_overload(self):
        # Test operator overloading
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "bool operator==(const MyClass& other) const {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "operator==")
        self.assertEqual(methodInfo.dataType, "bool")

    def test_method_with_default_parameters(self):
        # Test method with default parameters
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "void setValues(int x = 0, int y = 0) {"
        match = re.search(methodAnalyzer.pattern, inputStr)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )
        self.assertEqual(methodInfo.name, "setValues")
        self.assertEqual(len(methodInfo.params), 2)
        self.assertEqual(methodInfo.params[0], "int")
        self.assertEqual(methodInfo.params[1], "int")

    def test_const_method_with_trailing_return(self):
        # Test method with trailing return type and const qualifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "auto computeRisk(int level) const -> double {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "computeRisk")
        self.assertEqual(methodInfo.dataType, "double")
        self.assertTrue(methodInfo.isConst)

    def test_ref_qualified_method(self):
        # Test method with reference qualifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "std::string&& rvalueDeclared() && {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "rvalueDeclared")
        self.assertEqual(methodInfo.dataType, "std::string&&")

    def test_noexcept_method(self):
        # Test method with noexcept specifier
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "double computeEnergy(int level) noexcept {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "computeEnergy")
        self.assertEqual(methodInfo.dataType, "double")
        self.assertTrue(methodInfo.hasNoexcept)

    def test_template_method_with_multiple_params(self):
        # Test template method with multiple type parameters
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "template<typename T, typename U> std::pair<T, U> mixTypes(const T& t, const U& u) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "mixTypes")
        self.assertEqual(methodInfo.dataType, "std::pair<T, U>")
        self.assertTrue(methodInfo.hasTemplate)

    def test_nodiscard_attribute_method(self):
        # Test method with [[nodiscard]] attribute
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "[[nodiscard]] auto computeRisk(int level) const -> double {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        self.assertIsNotNone(match)

    def test_variadic_template_method(self):
        # Test variadic template method
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "template<typename... Args> void variadicDeclared(Args&&... args) {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "variadicDeclared")
        self.assertEqual(methodInfo.dataType, "void")
        self.assertTrue(methodInfo.hasTemplate)

    def test_method_with_same_name_as_return_type(self):
        # Test method where name is same as return type
        methodAnalyzer = CppMethodAnalyzer()
        inputStr = "Fake::Namespace::Example_1 Example_1() {"

        match = re.search(methodAnalyzer.pattern, inputStr)
        self.assertIsNotNone(match)
        methodInfo = methodAnalyzer.extractMethodInfo(
            inputStr, match, AccessEnum.PUBLIC
        )

        self.assertEqual(methodInfo.name, "Example_1")
        self.assertEqual(methodInfo.dataType, "Fake::Namespace::Example_1")

    def test_analyze_method_footprints_file(self):
        # Test parsing the entire MethodFootprintsExtended.hpp file
        methodAnalyzer = CppMethodAnalyzer()

        file_path = "/home/mhh/Projects/KudSight/app/tests/ref_files/cpp/MethodFootprintsExtended.hpp"

        if not os.path.exists(file_path):
            os.makedirs(
                "/home/mhh/Projects/KudSight/app/tests/ref_files/cpp", exist_ok=True
            )

            with open(file_path, "w") as f:
                f.write(
                    """
#ifndef METHOD_FOOTPRINTS_EXTENDED_HPP
#define METHOD_FOOTPRINTS_EXTENDED_HPP

#include <string>
#include <vector>
#include <memory>
#include <optional>
#include <map>
#include <initializer_list>
#include <tuple>
#include <array>
#include <functional>
#include <type_traits>
#include <iostream>

class MethodFootprintsExtended {
public:
    void initialize() { initialized = true; }
    int compute(int x, double y) { return static_cast<int>(x + y); }
    std::string getName() const { return name; }
    static bool isValid(int code) { return code >= 0; }
    virtual void draw() const {}
    void update(double deltaTime) override { this->delta += deltaTime; }

    void declaredOnlyMethod();
    int declaredWithParams(int a, float b);
    std::string declaredConstMethod() const;
    const std::vector<int>& fetchReadOnlyData() const;
    static bool isFeatureEnabled();
    double computeEnergy(int level) noexcept;
    template<typename T>
    T genericMethod(T value);
    template<typename T, typename U>
    std::pair<T, U> mixTypes(const T& t, const U& u);
    virtual void declaredVirtual() const;
    void mustOverrideLater() override;
    [[nodiscard]] auto computeRisk(int level) const -> double;
    std::string&& rvalueDeclared() &&;
    std::string& lvalueDeclared() &;
    template<typename... Args>
    void variadicDeclared(Args&&... args);
    bool operator!=(const MethodFootprintsExtended& other) const;
    friend bool areEqual(const MethodFootprintsExtended& a, const MethodFootprintsExtended& b);
    Fake::Namespace::Example_1 Example_1();
    Fake::Namespace::Example_2 Example_2() const;
    Fake::Namespace::Example_3 Example_3(int x);
    mylib::CustomType CustomType();
    std::vector<int> vector();
    std::tuple<int, double, std::string> tuple();
    std::optional<std::string> optional();
    std::array<int, 3> array();
    std::function<void()> function();
    std::unique_ptr<int> unique_ptr();
    std::shared_ptr<std::string> shared_ptr();

private:
    bool initialized = false;
    std::string name = "default";
    double delta = 0.0;
};

#endif // METHOD_FOOTPRINTS_EXTENDED_HPP
                """
                )

        file_content = FileReader().read_file(file_path)

        methods = methodAnalyzer.analyze(None, None, file_content)

        self.assertTrue(len(methods) > 25)

        method_names = [m.name for m in methods]
        self.assertIn("initialize", method_names)
        self.assertIn("getName", method_names)
        self.assertIn("declaredOnlyMethod", method_names)
        self.assertIn("declaredConstMethod", method_names)
        self.assertIn("computeRisk", method_names)
        self.assertIn("Example_1", method_names)
        self.assertIn("vector", method_names)

        const_methods = [m for m in methods if m.isConst]
        self.assertTrue(len(const_methods) >= 5)

        virtual_methods = [m for m in methods if m.isVirtual]
        self.assertTrue(len(virtual_methods) >= 2)
