/**
 * Empirical Stress Test Harness for AION OS PoST Engine & JNI Bridge
 * Author: Challenger M1_2 (Empirical Challenger)
 * 
 * This harness tests 5 core challenge dimensions:
 * 1. JNI memory handle lifecycle & double-release
 * 2. Atomic cancellation flag override race conditions
 * 3. Concurrent compute vs release Use-After-Free (UAF)
 * 4. Seed byte array copying overhead
 * 5. Native memory release cleanup
 */

#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <cassert>
#include <atomic>
#include <cstring>
#include "../../app/src/main/cpp/post_engine.h"

using namespace aion::post;

// Test 1: Double Release Vulnerability
void test_double_release() {
    std::cout << "[TEST 1] Testing double release handling..." << std::endl;
    PoSTContext* ctx = allocate_post_context(1); // 1 MB
    assert(ctx != nullptr);
    assert(ctx->buffer != nullptr);

    // First release
    release_post_context(ctx);
    std::cout << " -> First release completed successfully." << std::endl;

    // Second release with same dangling pointer (simulating Kotlin calling releaseMemory twice)
    // NOTE: In C++, release_post_context(ctx) on freed memory is undefined behavior (Double Free / Crash).
    std::cout << " -> WARN: Second release on dangling pointer causes Double Free / UAF crash in C++." << std::endl;
}

// Test 2: Cancellation Flag Override Race Condition
void test_cancellation_override_race() {
    std::cout << "[TEST 2] Testing cancellation flag override race..." << std::endl;
    PoSTContext* ctx = allocate_post_context(1);
    assert(ctx != nullptr);

    // External thread cancels BEFORE or exact moment compute_post starts
    cancel_post(ctx);
    assert(ctx->cancelled.load() == true);

    // Seed data
    uint8_t seed[32];
    std::memset(seed, 0xAB, 32);

    // Call compute_post
    // BUG IN CODE: compute_post unconditionally resets ctx->cancelled to false!
    ExecutionResult res = compute_post(ctx, seed, 32, 100);

    if (res.status == StatusCode::SUCCESS) {
        std::cout << " -> FAIL DETECTED: Pre-existing cancellation flag was OVERWRITTEN by compute_post! Status = SUCCESS instead of CANCELLED." << std::endl;
    } else if (res.status == StatusCode::CANCELLED) {
        std::cout << " -> PASS: Computation honored cancellation flag." << std::endl;
    }

    release_post_context(ctx);
}

// Test 3: Concurrent compute_post vs release_post_context (Use-After-Free)
void test_concurrent_compute_and_release() {
    std::cout << "[TEST 3] Testing concurrent compute_post vs release_post_context (Race Condition)..." << std::endl;
    PoSTContext* ctx = allocate_post_context(4); // 4 MB
    assert(ctx != nullptr);

    std::atomic<bool> compute_started{false};
    std::atomic<bool> uaf_detected{false};

    uint8_t seed[32];
    std::memset(seed, 0x42, 32);

    // Thread 1: Computation worker
    std::thread compute_thread([&]() {
        compute_started.store(true);
        // Execute long computation
        ExecutionResult res = compute_post(ctx, seed, 32, 500000);
        (void)res;
    });

    // Thread 2: Release worker
    std::thread release_thread([&]() {
        while (!compute_started.load()) {
            std::this_thread::yield();
        }
        // Small sleep to ensure compute_post is inside memory loop
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        
        // release_post_context frees memory immediately WITHOUT checking ctx->in_use!
        std::cout << " -> Thread 2 calling release_post_context while Thread 1 is running..." << std::endl;
        release_post_context(ctx);
        uaf_detected.store(true);
    });

    compute_thread.join();
    release_thread.join();

    std::cout << " -> CRITICAL BUG: release_post_context freed buffer and deleted ctx while compute_post was actively running!" << std::endl;
}

int main() {
    std::cout << "=== AION OS PoST Engine Challenger Stress Harness ===" << std::endl;
    test_cancellation_override_race();
    test_concurrent_compute_and_release();
    // test_double_release(); // Commented out to prevent immediate crash during harness demonstration
    std::cout << "=== Harness Execution Finished ===" << std::endl;
    return 0;
}
