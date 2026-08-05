// Test Harness: Demonstrating Use-After-Free (UAF) Race Condition in post_engine / JNI Bridge
// File: .agents/challenger_m1_2_fix/test_uaf_race.cpp

#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <chrono>
#include <cassert>
#include <mutex>
#include <condition_variable>
#include <cstdlib>

// Mock of PoSTContext matching post_engine.h
struct PoSTContext {
    uint8_t* buffer = nullptr;
    size_t buffer_size_bytes = 0;
    std::atomic<bool> cancelled{false};
    std::atomic<bool> in_use{false};
    std::mutex lock;
    std::condition_variable cv;
};

struct InUseGuard {
    PoSTContext* ctx;
    ~InUseGuard() {
        if (ctx) {
            std::lock_guard<std::mutex> lock(ctx->lock);
            ctx->in_use.store(false, std::memory_order_release);
            ctx->cv.notify_all();
        }
    }
};

void release_post_context(PoSTContext* ctx) {
    if (!ctx) return;
    ctx->cancelled.store(true, std::memory_order_release);
    {
        std::unique_lock<std::mutex> lock(ctx->lock);
        ctx->cv.wait(lock, [ctx] {
            return !ctx->in_use.load(std::memory_order_acquire);
        });
    }
    if (ctx->buffer) {
        free(ctx->buffer);
        ctx->buffer = nullptr;
    }
    delete ctx;
}

// Simulated JNI entry + compute_post
void jni_compute_post_sim(PoSTContext* ctx) {
    // 1. JNI layer dereferences ctx BEFORE compute_post acquired in_use!
    // In jni_bridge.cpp line 140:
    // if (ctx == nullptr || ctx->buffer == nullptr || ctx->buffer_size_bytes == 0)
    // If release_post_context deleted ctx right before this line, ctx is dangling!
    if (!ctx) return;

    // Small delay to simulate JVM->JNI context switch / argument parsing
    std::this_thread::sleep_for(std::chrono::microseconds(10));

    // Try reading ctx->buffer (JNI check)
    if (ctx->buffer == nullptr) return; // UAF READ!

    bool expected = false;
    if (!ctx->in_use.compare_exchange_strong(expected, true)) {
        return;
    }

    InUseGuard guard{ctx};
    if (ctx->cancelled.load(std::memory_order_acquire)) {
        return;
    }

    // Do work...
    for (int i = 0; i < 1000; ++i) {
        if (ctx->cancelled.load(std::memory_order_relaxed)) break;
        ctx->buffer[i % ctx->buffer_size_bytes] ^= static_cast<uint8_t>(i);
    }
}

int main() {
    std::cout << "[STRESS TEST] Testing TOCTOU / UAF Race Condition in JNI Bridge & PoST Engine..." << std::endl;
    // Repeat test iterations to expose race
    for (int iter = 0; iter < 100; ++iter) {
        PoSTContext* ctx = new PoSTContext();
        ctx->buffer_size_bytes = 1024 * 1024;
        ctx->buffer = (uint8_t*)malloc(ctx->buffer_size_bytes);
        ctx->cancelled.store(false);
        ctx->in_use.store(false);

        // Thread A calls JNI compute_post
        std::thread t_compute([ctx]() {
            jni_compute_post_sim(ctx);
        });

        // Thread B calls release_post_context concurrently
        std::thread t_release([ctx]() {
            // Small delay to hit window after Kotlin activeHandles.contains check but before C++ in_use CAS
            std::this_thread::sleep_for(std::chrono::microseconds(5));
            release_post_context(ctx);
        });

        t_compute.join();
        t_release.join();
    }
    std::cout << "[STRESS TEST] Completed." << std::endl;
    return 0;
}
