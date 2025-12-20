#ifndef TASKDAEMON_HPP
#define TASKDAEMON_HPP

#include <iostream>
#include <string>
#include <functional>
#include <variant>
#include <nlohmann/json.hpp>

namespace taskdaemon {

using json = nlohmann::json;

struct Task {
    std::string task_id;
    std::string task_type;
    json task_data;
    int attempt;
};

struct Success {
    json result;
};

struct Error {
    std::string error;
    bool retryable = false;
};

using Result = std::variant<Success, Error>;

inline Result success(const json& result) {
    return Success{result};
}

inline Result error(const std::string& msg, bool retryable = false) {
    return Error{msg, retryable};
}

inline void run(std::function<Result(const Task&)> handler) {
    std::string line;
    while (std::getline(std::cin, line)) {
        json response;
        try {
            auto j = json::parse(line);
            Task task{
                j["task_id"].get<std::string>(),
                j["task_type"].get<std::string>(),
                j["task_data"],
                j["attempt"].get<int>()
            };
            
            auto result = handler(task);
            if (auto* s = std::get_if<Success>(&result)) {
                response = {{"status", "success"}, {"result", s->result}};
            } else if (auto* e = std::get_if<Error>(&result)) {
                response = {{"status", "error"}, {"error", e->error}, {"retryable", e->retryable}};
            }
        } catch (const std::exception& e) {
            response = {{"status", "error"}, {"error", e.what()}, {"retryable", false}};
        }
        std::cout << response.dump() << std::endl;
    }
}

} // namespace taskdaemon

#endif
