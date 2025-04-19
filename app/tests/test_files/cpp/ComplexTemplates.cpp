#include <iostream>
#include <vector>
#include <map>
#include <memory>
#include <string>

namespace complex {
namespace templates {

// A class with nested templates and complex types
template<typename T, typename U>
class ComplexContainer {
private:
    // Nested template variable
    std::map<std::string, std::vector<T>> dataMap;
    
    // Complex pointer type
    std::shared_ptr<U> sharedInstance;
    
    // Simple variable
    int counter;
    
    // Static constant
    static const int MAX_SIZE = 100;

public:
    // Constructor with complex parameter types
    ComplexContainer(const std::vector<T>& initialData, std::shared_ptr<U> instance)
        : sharedInstance(instance), counter(0) {
        // Implementation
    }
    
    // Method with complex parameter and return types
    std::vector<std::pair<std::string, T>> processData(const std::map<int, U>& inputMap) const {
        std::vector<std::pair<std::string, T>> result;
        // Implementation
        return result;
    }
    
    // Template method with nested templates
    template<typename V>
    std::map<std::string, V> convertData(const std::vector<V>& input) {
        std::map<std::string, V> result;
        // Implementation
        return result;
    }
    
    // Virtual method for inheritance testing
    virtual void update(T value) = 0;
    
    // Destructor
    ~ComplexContainer() {
        // Cleanup
    }
};

// Implementation class that extends the template class
class StringIntContainer : public ComplexContainer<std::string, int> {
private:
    // Additional member variables
    bool isModified;

public:
    // Constructor implementation
    StringIntContainer(const std::vector<std::string>& data, std::shared_ptr<int> value)
        : ComplexContainer<std::string, int>(data, value), isModified(false) {
        // Implementation
    }
    
    // Override of virtual method
    void update(std::string value) override {
        isModified = true;
        // Implementation
    }
};

} // namespace templates
} // namespace complex