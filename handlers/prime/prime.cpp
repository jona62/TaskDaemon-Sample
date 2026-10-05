#include <vector>
#include <chrono>
#include <cstdint>
#include "taskdaemon.hpp"

using namespace taskdaemon;

// Find prime numbers up to n using Sieve of Eratosthenes
std::vector<int> sieve_primes(int n) {
    std::vector<bool> is_prime(n + 1, true);
    std::vector<int> primes;
    
    for (int i = 2; i <= n; i++) {
        if (is_prime[i]) {
            primes.push_back(i);
            for (long long j = (long long)i * i; j <= n; j += i) {
                is_prime[j] = false;
            }
        }
    }
    return primes;
}

Result handle(const Task& task) {
    constexpr int max_limit = 10000000;
    constexpr auto range_error = "limit must be between 2 and 10000000";
    if (!task.task_data.is_object()) {
        return error("task_data must be an object");
    }
    int limit = 1000000;
    const auto requested = task.task_data.find("limit");
    if (requested != task.task_data.end()) {
        if (!requested->is_number_integer()) {
            return error("limit must be an integer");
        }
        if (requested->is_number_unsigned() && requested->get<std::uint64_t>() > max_limit) {
            return error(range_error);
        }
        const auto value = requested->get<std::int64_t>();
        if (value < 2 || value > max_limit) {
            return error(range_error);
        }
        limit = static_cast<int>(value);
    }
    
    auto start = std::chrono::steady_clock::now();
    auto primes = sieve_primes(limit);
    auto end = std::chrono::steady_clock::now();
    
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    return success({
        {"limit", limit},
        {"count", primes.size()},
        {"largest", primes.empty() ? 0 : primes.back()},
        {"duration_ms", duration.count()}
    });
}

int main() {
    run(handle);
    return 0;
}
