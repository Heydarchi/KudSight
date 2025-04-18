#ifndef INTEGRATION_TEST_HPP
#define INTEGRATION_TEST_HPP

// Include headers from various namespaces
#include "sample1.hpp"
#include "utils.h"
#include "company_a_logging.hpp"
#include "company_b_widgets.hpp"

#include <vector>

namespace Integration {

    class TestRunner {
    private:
        MyCompany::Core::ExampleClass<int> testSubject; // Use template class from MyCompany::Core
        CompanyA::Logging::Logger mainLogger;           // Use Logger from CompanyA::Logging
        std::vector<CompanyB::UI::Widget*> widgets;     // Use Widget from CompanyB::UI

    public:
        TestRunner();
        ~TestRunner();

        void setupWidgets();
        void runAllTests();

        // Method demonstrating cross-namespace usage
        void logWidgetInteractions(CompanyB::UI::Button* button);
    };

} // namespace Integration

#endif // INTEGRATION_TEST_HPP