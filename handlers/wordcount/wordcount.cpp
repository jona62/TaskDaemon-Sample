#include "taskdaemon.hpp"
#include <algorithm>
#include <sstream>

int main() {
    taskdaemon::run([](const taskdaemon::Task& task) {
        std::string text = task.task_data.value("text", "");
        
        // Count words
        int words = 0;
        std::istringstream iss(text);
        std::string word;
        while (iss >> word) words++;
        
        // Count characters (excluding spaces)
        int chars = std::count_if(text.begin(), text.end(), [](char c) { return !std::isspace(c); });
        
        // Count lines
        int lines = std::count(text.begin(), text.end(), '\n') + 1;
        
        return taskdaemon::success({
            {"words", words},
            {"characters", chars},
            {"lines", lines}
        });
    });
}
