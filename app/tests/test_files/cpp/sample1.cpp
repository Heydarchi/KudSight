// ExampleClass.cpp

#include "ExampleClass.hpp"

namespace MyCompany::Core {

    template <typename T>
    ExampleClass<T>::ExampleClass() : data(nullptr), name("default") {}

    template <typename T>
    ExampleClass<T>::~ExampleClass() {}

    template <typename T>
    void ExampleClass<T>::setName(const std::string& newName) {
        this->name = newName;
    }

    template <typename T>
    std::string ExampleClass<T>::getName() const {
        return name;
    }

    // This won't be picked up as a method due to keyword
    void* operator new(size_t size) {
        return malloc(size);
    }

}
