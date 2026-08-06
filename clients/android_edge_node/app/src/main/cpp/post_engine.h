#ifndef AION_POST_ENGINE_H
#define AION_POST_ENGINE_H

#include <cstdint>
#include <cstddef>
#include <atomic>
#include <mutex>
#include <condition_variable>

namespace aion {
namespace post {

enum class StatusCode : int32_t {
    SUCCESS = 0,
    OOM = 1,
    CANCELLED = 2,
    INVALID_PARAM = 3
};

struct ExecutionResult {
    uint8_t proof_digest[32];
    uint64_t execution_time_ms;
    size_t allocated_ram_bytes;
    uint32_t iterations_completed;
    StatusCode status;
};

struct PoSTContext {
    uint8_t* buffer = nullptr;
    size_t buffer_size_bytes = 0;
    std::atomic<bool> cancelled{false};
    std::atomic<bool> paused{false};
    std::atomic<uint32_t> progress{0};
    std::atomic<bool> in_use{false};
    std::mutex lock;
    std::condition_variable cv;
};

void secure_zero(void* ptr, size_t len);
PoSTContext* allocate_post_context(int size_mb);
ExecutionResult compute_post(PoSTContext* ctx, const uint8_t* seed, size_t seed_len, const uint8_t* shard_data, size_t shard_len, int iterations);
void cancel_post(PoSTContext* ctx);
void pause_post(PoSTContext* ctx);
void resume_post(PoSTContext* ctx);
void release_post_context(PoSTContext* ctx);

} // namespace post
} // namespace aion

#endif // AION_POST_ENGINE_H
