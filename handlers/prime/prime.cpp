#include <vector>
#include <chrono>
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
    int limit = task.task_data.value("limit", 1000000);
    
    auto start = std::chrono::high_resolution_clock::now();
    auto primes = sieve_primes(limit);
    auto end = std::chrono::high_resolution_clock::now();
    
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
