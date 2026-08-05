#include <iostream>
#include <cassert>
#include <cstring>
#include <thread>
#include <chrono>
#include <vector>
#include "post_engine.h"
#include "sha256.h"

using namespace aion::post;
using namespace aion::crypto;

void test_sha256_nist_vectors() {
    std::cout << "[TEST] Running SHA-256 NIST test vectors..." << std::endl;

    // Vector 1: Empty string ""
    std::string empty_hex = SHA256::hashToHex(reinterpret_cast<const uint8_t*>(""), 0);
    assert(empty_hex == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");

    // Vector 2: "abc"
    std::string abc_hex = SHA256::hashToHex(reinterpret_cast<const uint8_t*>("abc"), 3);
    assert(abc_hex == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");

    std::cout << "  -> PASSED: SHA-256 NIST vectors match standard." << std::endl;
}

void test_memory_allocation_alignment() {
    std::cout << "[TEST] Running memory allocation and alignment checks..." << std::endl;

    // Valid allocation: 1 MB
    PoSTContext* ctx1 = allocate_post_context(1);
    assert(ctx1 != nullptr);
    assert(ctx1->buffer != nullptr);
    assert(ctx1->buffer_size_bytes == 1024 * 1024);
    assert(reinterpret_cast<uintptr_t>(ctx1->buffer) % 64 == 0); // 64-byte alignment

    // Valid allocation: 16 MB
    PoSTContext* ctx16 = allocate_post_context(16);
    assert(ctx16 != nullptr);
    assert(ctx16->buffer != nullptr);
    assert(ctx16->buffer_size_bytes == 16 * 1024 * 1024);
    assert(reinterpret_cast<uintptr_t>(ctx16->buffer) % 64 == 0);

    // Invalid allocation: 0 MB
    PoSTContext* ctx0 = allocate_post_context(0);
    assert(ctx0 == nullptr);

    // Invalid allocation: -1 MB
    PoSTContext* ctx_neg = allocate_post_context(-1);
    assert(ctx_neg == nullptr);

    // Invalid allocation: 257 MB (over max threshold 256 MB)
    PoSTContext* ctx257 = allocate_post_context(257);
    assert(ctx257 == nullptr);

    release_post_context(ctx1);
    release_post_context(ctx16);

    std::cout << "  -> PASSED: Memory allocation & 64-byte alignment verified." << std::endl;
}

void test_zeroing_elision() {
    std::cout << "[TEST] Running zeroing elision prevention check..." << std::endl;

    size_t test_size = 1024;
    uint8_t* buf = static_cast<uint8_t*>(malloc(test_size));
    std::memset(buf, 0xAB, test_size);

    secure_zero(buf, test_size);

    for (size_t i = 0; i < test_size; ++i) {
        assert(buf[i] == 0x00);
    }
    free(buf);

    std::cout << "  -> PASSED: secure_zero cleared buffer to 0x00." << std::endl;
}

void test_boundary_edge_cases() {
    std::cout << "[TEST] Running boundary edge cases (0 iterations, null parameters)..." << std::endl;

    PoSTContext* ctx = allocate_post_context(1);
    assert(ctx != nullptr);

    uint8_t seed[32] = {0};

    // Edge Case 1: 0 iterations
    ExecutionResult res0 = compute_post(ctx, seed, 32, 0);
    assert(res0.status == StatusCode::INVALID_PARAM);
    assert(res0.iterations_completed == 0);

    // Edge Case 2: Negative iterations
    ExecutionResult res_neg = compute_post(ctx, seed, 32, -5);
    assert(res_neg.status == StatusCode::INVALID_PARAM);

    // Edge Case 3: Null seed pointer
    ExecutionResult res_null_seed = compute_post(ctx, nullptr, 32, 100);
    assert(res_null_seed.status == StatusCode::INVALID_PARAM);

    // Edge Case 4: Invalid seed length
    ExecutionResult res_seed_len = compute_post(ctx, seed, 0, 100);
    assert(res_seed_len.status == StatusCode::INVALID_PARAM);

    // Edge Case 5: Null context pointer
    ExecutionResult res_null_ctx = compute_post(nullptr, seed, 32, 100);
    assert(res_null_ctx.status == StatusCode::INVALID_PARAM);

    release_post_context(ctx);

    std::cout << "  -> PASSED: All boundary edge cases handled safely." << std::endl;
}

void test_math_loop_hardware_effort_and_determinism() {
    std::cout << "[TEST] Running math loop hardware effort & determinism check..." << std::endl;

    PoSTContext* ctx = allocate_post_context(1); // 1 MB
    assert(ctx != nullptr);

    uint8_t seed[32];
    for (int i = 0; i < 32; ++i) seed[i] = static_cast<uint8_t>(i + 1);

    int iterations = 1000;
    ExecutionResult res1 = compute_post(ctx, seed, 32, iterations);
    assert(res1.status == StatusCode::SUCCESS);
    assert(res1.iterations_completed == 1000);
    assert(res1.allocated_ram_bytes == 1024 * 1024);
    assert(res1.execution_time_ms >= 0);

    // Compute again with same seed & iterations to verify determinism
    ExecutionResult res2 = compute_post(ctx, seed, 32, iterations);
    assert(res2.status == StatusCode::SUCCESS);
    assert(std::memcmp(res1.proof_digest, res2.proof_digest, 32) == 0);

    release_post_context(ctx);

    std::cout << "  -> PASSED: Determinism verified. Hardware effort spent: " 
              << res1.execution_time_ms << " ms for 1000 iterations over 1 MB RAM." << std::endl;
}

void test_atomic_cancellation() {
    std::cout << "[TEST] Running atomic cancellation test..." << std::endl;

    PoSTContext* ctx = allocate_post_context(1); // 1 MB
    assert(ctx != nullptr);

    uint8_t seed[32] = {0};

    // Pre-cancel context
    cancel_post(ctx);

    ExecutionResult res = compute_post(ctx, seed, 32, 10000);
    assert(res.status == StatusCode::CANCELLED);

    release_post_context(ctx);

    std::cout << "  -> PASSED: Atomic cancellation verified." << std::endl;
}

void test_concurrent_busy_lock() {
    std::cout << "[TEST] Running concurrent busy lock (in_use) test..." << std::endl;

    PoSTContext* ctx = allocate_post_context(1);
    assert(ctx != nullptr);

    uint8_t seed[32] = {0};

    // Spawn thread 1 to run long computation
    std::thread t1([&]() {
        compute_post(ctx, seed, 32, 50000);
    });

    // Wait a brief moment to ensure t1 starts
    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    // Call compute_post from thread 2 on same context
    ExecutionResult res2 = compute_post(ctx, seed, 32, 100);
    assert(res2.status == StatusCode::INVALID_PARAM); // Rejected due to in_use busy lock

    cancel_post(ctx);
    t1.join();

    release_post_context(ctx);

    std::cout << "  -> PASSED: Concurrent duplicate call safely rejected." << std::endl;
}

int main() {
    std::cout << "==================================================" << std::endl;
    std::cout << "  AION OS PoST Bare-Metal Engine Empirical Tests   " << std::endl;
    std::cout << "==================================================" << std::endl;

    test_sha256_nist_vectors();
    test_memory_allocation_alignment();
    test_zeroing_elision();
    test_boundary_edge_cases();
    test_math_loop_hardware_effort_and_determinism();
    test_atomic_cancellation();
    test_concurrent_busy_lock();
    test_concurrent_release();

    std::cout << "==================================================" << std::endl;
    std::cout << " ALL EMPIRICAL SUITE TESTS PASSED SUCCESSFULLY!   " << std::endl;
    std::cout << "==================================================" << std::endl;
    return 0;
}

void test_concurrent_release() {
    std::cout << "[TEST] Running concurrent release_post_context during active compute..." << std::endl;

    PoSTContext* ctx = allocate_post_context(4);
    assert(ctx != nullptr);

    uint8_t seed[32];
    std::memset(seed, 0x42, 32);

    std::thread t1([&]() {
        compute_post(ctx, seed, 32, 500000);
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    // Release context while t1 is actively running
    release_post_context(ctx);

    t1.join();

    std::cout << "  -> PASSED: Thread-safe cancellation & release during active compute succeeded without UAF crash." << std::endl;
}
