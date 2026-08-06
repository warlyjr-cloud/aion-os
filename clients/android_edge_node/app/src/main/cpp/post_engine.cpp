#include "post_engine.h"
#include "sha256.h"
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <new>
#include <mutex>
#include <sys/mman.h>
#include <unistd.h>
#include <fstream>
#include <string>

namespace aion {
namespace post {

// Helper to read memory stats from the kernel
size_t get_current_rss() {
    std::ifstream status("/proc/self/status");
    std::string line;
    while (std::getline(status, line)) {
        if (line.substr(0, 6) == "VmRSS:") {
            size_t val = std::stoul(line.substr(7));
            return val * 1024; // Convert KB to Bytes
        }
    }
    return 0;
}

void secure_zero(void* ptr, size_t len) {
    if (!ptr || len == 0) return;
    volatile uint8_t* p = static_cast<volatile uint8_t*>(ptr);
    while (len--) {
        *p++ = 0;
    }
}

PoSTContext* allocate_post_context(int size_mb) {
    if (size_mb < 1 || size_mb > 256) {
        return nullptr;
    }
    size_t size_bytes = static_cast<size_t>(size_mb) * 1024 * 1024;
    void* ptr = nullptr;
    int res = posix_memalign(&ptr, 64, size_bytes);
    if (res != 0 || !ptr) {
        return nullptr;
    }

    PoSTContext* ctx = new (std::nothrow) PoSTContext();
    if (!ctx) {
        free(ptr);
        return nullptr;
    }
    ctx->buffer = static_cast<uint8_t*>(ptr);
    ctx->buffer_size_bytes = size_bytes;

    // Try to lock memory in RAM to prevent swapping
    // Note: May fail on some Android versions due to RLIMIT_MEMLOCK
    if (mlock(ctx->buffer, ctx->buffer_size_bytes) == 0) {
        // Successfully "stolen" and pinned to physical RAM
    }

    ctx->cancelled.store(false);
    ctx->paused.store(false);
    ctx->progress.store(0);
    ctx->in_use.store(false);
    return ctx;
}

static inline void pack_uint64_be(uint64_t val, uint8_t out[8]) {
    out[0] = static_cast<uint8_t>((val >> 56) & 0xFF);
    out[1] = static_cast<uint8_t>((val >> 48) & 0xFF);
    out[2] = static_cast<uint8_t>((val >> 40) & 0xFF);
    out[3] = static_cast<uint8_t>((val >> 32) & 0xFF);
    out[4] = static_cast<uint8_t>((val >> 24) & 0xFF);
    out[5] = static_cast<uint8_t>((val >> 16) & 0xFF);
    out[6] = static_cast<uint8_t>((val >> 8) & 0xFF);
    out[7] = static_cast<uint8_t>(val & 0xFF);
}

static inline uint64_t unpack_uint64_be(const uint8_t in[8]) {
    return (static_cast<uint64_t>(in[0]) << 56) |
           (static_cast<uint64_t>(in[1]) << 48) |
           (static_cast<uint64_t>(in[2]) << 40) |
           (static_cast<uint64_t>(in[3]) << 32) |
           (static_cast<uint64_t>(in[4]) << 24) |
           (static_cast<uint64_t>(in[5]) << 16) |
           (static_cast<uint64_t>(in[6]) << 8)  |
           (static_cast<uint64_t>(in[7]));
}

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

ExecutionResult compute_post(PoSTContext* ctx, const uint8_t* seed, size_t seed_len, const uint8_t* shard_data, size_t shard_len, int iterations) {
    ExecutionResult result{};
    std::memset(result.proof_digest, 0, 32);
    result.status = StatusCode::INVALID_PARAM;
    result.execution_time_ms = 0;
    result.allocated_ram_bytes = 0;
    result.iterations_completed = 0;

    if (!ctx || !ctx->buffer || ctx->buffer_size_bytes == 0 || !seed || seed_len == 0 || iterations <= 0) {
        return result;
    }

    bool expected = false;
    if (!ctx->in_use.compare_exchange_strong(expected, true)) {
        return result; // Busy / concurrently running
    }

    InUseGuard guard{ctx};

    if (ctx->cancelled.load(std::memory_order_acquire)) {
        result.status = StatusCode::CANCELLED;
        return result;
    }

    result.allocated_ram_bytes = ctx->buffer_size_bytes;

    auto start_time = std::chrono::high_resolution_clock::now();

    // Stage 1: Space Allocation & Shard Loading & Seed Expansion
    uint8_t h0[32];
    aion::crypto::SHA256::hash(seed, seed_len, h0);

    size_t num_blocks = ctx->buffer_size_bytes / 32;

    // Load real shard data if provided
    size_t bytes_to_copy = std::min(shard_len, ctx->buffer_size_bytes);
    if (shard_data && bytes_to_copy > 0) {
        std::memcpy(ctx->buffer, shard_data, bytes_to_copy);
    } else {
        std::memcpy(ctx->buffer, h0, 32);
        bytes_to_copy = 32;
    }

    size_t start_block = bytes_to_copy / 32;
    if (start_block == 0) start_block = 1;

    uint8_t block_input[40];
    for (size_t i = start_block; i < num_blocks; ++i) {
        if (i % 512 == 0) {
            if (ctx->cancelled.load(std::memory_order_relaxed)) {
                result.status = StatusCode::CANCELLED;
                return result;
            }
            if (ctx->paused.load(std::memory_order_relaxed)) {
                std::unique_lock<std::mutex> lock(ctx->lock);
                ctx->cv.wait(lock, [ctx] {
                    return !ctx->paused.load(std::memory_order_relaxed) ||
                           ctx->cancelled.load(std::memory_order_relaxed);
                });
                if (ctx->cancelled.load(std::memory_order_relaxed)) {
                    result.status = StatusCode::CANCELLED;
                    return result;
                }
            }
        }
        std::memcpy(block_input, ctx->buffer + (i - 1) * 32, 32);
        pack_uint64_be(static_cast<uint64_t>(i), block_input + 32);
        aion::crypto::SHA256::hash(block_input, 40, ctx->buffer + i * 32);
    }

    // Stage 2: Time-Dilation Memory Walk & Cell Mutation
    uint8_t W[32];
    std::memcpy(W, h0, 32);

    uint8_t mix_input[72];
    uint8_t W_new[32];

    for (int r = 0; r < iterations; ++r) {
        if (r % 32 == 0) {
            ctx->progress.store(static_cast<uint32_t>(r), std::memory_order_relaxed);
            if (ctx->cancelled.load(std::memory_order_relaxed)) {
                result.status = StatusCode::CANCELLED;
                result.iterations_completed = r;
                return result;
            }
            if (ctx->paused.load(std::memory_order_relaxed)) {
                std::unique_lock<std::mutex> lock(ctx->lock);
                ctx->cv.wait(lock, [ctx] {
                    return !ctx->paused.load(std::memory_order_relaxed) ||
                           ctx->cancelled.load(std::memory_order_relaxed);
                });
                if (ctx->cancelled.load(std::memory_order_relaxed)) {
                    result.status = StatusCode::CANCELLED;
                    result.iterations_completed = r;
                    return result;
                }
            }
        }

        uint64_t raw_index = unpack_uint64_be(W);
        size_t target_block = static_cast<size_t>(raw_index % num_blocks);
        size_t target_offset = target_block * 32;

        std::memcpy(mix_input, W, 32);
        std::memcpy(mix_input + 32, ctx->buffer + target_offset, 32);
        pack_uint64_be(static_cast<uint64_t>(r), mix_input + 64);

        aion::crypto::SHA256::hash(mix_input, 72, W_new);

        for (size_t k = 0; k < 32; ++k) {
            ctx->buffer[target_offset + k] ^= W_new[k];
        }

        std::memcpy(W, W_new, 32);
    }

    ctx->progress.store(static_cast<uint32_t>(iterations), std::memory_order_relaxed);
    result.iterations_completed = iterations;

    // Stage 3: Proof Digest Compression
    uint8_t final_input[128];
    std::memcpy(final_input, W, 32);
    std::memcpy(final_input + 32, ctx->buffer, 32); // Start block
    std::memcpy(final_input + 64, ctx->buffer + (num_blocks / 2) * 32, 32); // Mid block
    std::memcpy(final_input + 96, ctx->buffer + (num_blocks - 1) * 32, 32); // End block

    aion::crypto::SHA256::hash(final_input, 128, result.proof_digest);

    auto end_time = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();
    result.status = StatusCode::SUCCESS;

    return result;
}

void cancel_post(PoSTContext* ctx) {
    if (ctx) {
        ctx->cancelled.store(true, std::memory_order_release);
        std::lock_guard<std::mutex> lock(ctx->lock);
        ctx->cv.notify_all();
    }
}

void pause_post(PoSTContext* ctx) {
    if (ctx) {
        ctx->paused.store(true, std::memory_order_release);
    }
}

void resume_post(PoSTContext* ctx) {
    if (ctx) {
        ctx->paused.store(false, std::memory_order_release);
        std::lock_guard<std::mutex> lock(ctx->lock);
        ctx->cv.notify_all();
    }
}

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
        munlock(ctx->buffer, ctx->buffer_size_bytes);
        secure_zero(ctx->buffer, ctx->buffer_size_bytes);
        free(ctx->buffer);
        ctx->buffer = nullptr;
    }
    delete ctx;
}

} // namespace post
} // namespace aion
