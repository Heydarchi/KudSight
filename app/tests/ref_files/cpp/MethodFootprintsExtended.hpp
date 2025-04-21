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
    // -------------------- [Defined methods] --------------------
    void initialize() { initialized = true; }
    int compute(int x, double y) { return static_cast<int>(x + y); }
    std::string getName() const { return name; }
    static bool isValid(int code) { return code >= 0; }
    virtual void draw() const {}
    void update(double deltaTime) override { this->delta += deltaTime; }
    // [... all previous implementations remain unchanged ...]

    // -------------------- [Declarations only — no implementation] --------------------

    // Basic
    void declaredOnlyMethod();
    int declaredWithParams(int a, float b);
    
    // Const and reference
    std::string declaredConstMethod() const;
    const std::vector<int>& fetchReadOnlyData() const;

    // Static and noexcept
    static bool isFeatureEnabled();
    double computeEnergy(int level) noexcept;

    // Template
    template<typename T>
    T genericMethod(T value);

    template<typename T, typename U>
    std::pair<T, U> mixTypes(const T& t, const U& u);

    // Virtual and override
    virtual void declaredVirtual() const;
    void mustOverrideLater() override;

    // Attributes and trailing return type
    [[nodiscard]] auto computeRisk(int level) const -> double;

    // Reference qualifiers
    std::string&& rvalueDeclared() &&;
    std::string& lvalueDeclared() &;

    // Variadic
    template<typename... Args>
    void variadicDeclared(Args&&... args);

    // Operator overloads
    bool operator!=(const MethodFootprintsExtended& other) const;

    // Friend function declared inside class
    friend bool areEqual(const MethodFootprintsExtended& a, const MethodFootprintsExtended& b);

#if __cpp_explicit_this_parameter >= 202110L
    auto declaredWithExplicitThis(this MethodFootprintsExtended& self) -> std::string;
#endif

    // --- Methods where the name is the same as the return type ---
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

    // --- Template-style return types with identical names ---
    Fake::Namespace::TemplateType<int> TemplateType();
    std::map<std::string, std::string> map();
    std::pair<int, std::string> pair();

    // --- Also with trailing return types ---
    auto Example_1_2() -> Fake::Namespace::Example_1;
    auto TemplateType2() -> Fake::Namespace::TemplateType<std::string>;


private:
    template<typename T>
    void logArg(const T&) {}

    bool initialized = false;
    std::string name = "default";
    double delta = 0.0;
    double radius = 1.0;
    std::string config;
    std::vector<int> buffer;
    std::vector<std::string> items;
    std::unique_ptr<int> owned;
};

#endif // METHOD_FOOTPRINTS_EXTENDED_HPP
