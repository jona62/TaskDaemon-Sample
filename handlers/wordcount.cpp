#include <iostream>
#include <string>
#include <algorithm>
#include <sstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

int main() {
    std::string line;
    while (std::getline(std::cin, line)) {
        json response;
        try {
            auto task = json::parse(line);
            std::string text = task["task_data"].value("text", "");
            
            // Count words
            int words = 0;
            std::istringstream iss(text);
            std::string word;
            while (iss >> word) words++;
            
            // Count characters (excluding spaces)
            int chars = std::count_if(text.begin(), text.end(), [](char c) { return !std::isspace(c); });
            
            response = {
                {"status", "success"},
                {"result", {
                    {"words", words},
                    {"characters", chars},
                    {"lines", std::count(text.begin(), text.end(), '\n') + 1}
                }}
            };
        } catch (const std::exception& e) {
            response = {{"status", "error"}, {"error", e.what()}, {"retryable", false}};
        }
        std::cout << response.dump() << std::endl;
    }
}
