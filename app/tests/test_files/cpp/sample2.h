#ifndef COMPANY_B_WIDGETS_HPP
#define COMPANY_B_WIDGETS_HPP

#include "company_a_logging.hpp" // Include header from different namespace
#include <string>

namespace CompanyB::UI {

    class Widget {
    protected:
        int x = 0, y = 0;
        CompanyA::Logging::Logger widgetLogger{2}; // Composition using another namespace

    public:
        virtual ~Widget() = default;
        virtual void draw() = 0; // Abstract method
        void setPosition(int x, int y);
    };

    class Button : public Widget {
    private:
        std::string label;
    public:
        Button(const std::string& lbl);
        void draw() override; // Override abstract method
        void click();
    };

} // namespace CompanyB::UI

#endif // COMPANY_B_WIDGETS_HPP