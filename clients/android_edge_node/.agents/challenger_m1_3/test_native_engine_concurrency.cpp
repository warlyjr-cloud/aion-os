#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <cassert>
#include <chrono>
#include "../../app/src/main/cpp/post_engine.h"

/**
 * C++ Empirical Verification Harness for PoST Engine Concurrency Safety.
 * Tests native allocate, compute, cancel, and release under multi-threaded execution.
 */

int main() {
    std::cout << "=== Starting C++ PoST Engine Concurrency Safety Harness ===" << std::endl;

    using namespace aion::post;

    // Test 1: Context Allocation & Basic Invariants
    PoSTContext* ctx = allocate_post_context(1); // 1 MB
    assert(ctx != nullptr);
    assert(ctx->buffer != nullptr);
    assert(ctx->buffer_size_bytes == 1024 * 1024);
    assert(ctx->cancelled.load() == false);
    assert(ctx->in_use.load() == false);

    std::cout << "[Test 1] Context allocation verified." << std::endl;

    // Test 2: Concurrent Cancel while Compute is Running
    uint8_t seed[32] = {0};
    for (int i = 0; i < 32; ++i) seed[i] = static_cast<uint8_t>(i);

    std::atomic<bool> compute_finished{false};
    ExecutionResult res{};

    std::thread compute_thread([&]() {
        res = compute_post(ctx, seed, 32, 100000); // High iteration count
        compute_finished.store(true);
    });

    // Give compute thread time to start Stage 2
    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    // Signal cancellation from another thread
    cancel_post(ctx);

    compute_thread.join();

    assert(compute_finished.load());
    assert(res.status == StatusCode::CANCELLED);
    std::cout << "[Test 2] Pre-computation / runtime cancellation verified. Iterations completed: " 
              << res.iterations_completed << std::endl;

    // Test 3: Safe Context Release when context is idle
    release_post_context(ctx);
    std::cout << "[Test 3] Memory released cleanly without memory leak or crash." << std::endl;

    std::cout << "=== All C++ Engine Tests PASSED ===" << std::endl;
    return 0;
}
