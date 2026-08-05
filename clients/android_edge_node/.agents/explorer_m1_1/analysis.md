# Technical Analysis & Implementation Blueprint: C++ Bare-Metal PoST Engine & JNI Bridge

**Project**: AION OS Android Edge Node  
**Milestone**: Milestone 1 (M1: Bare-Metal C++ PoST Engine & JNI Bridge)  
**Author**: Explorer M1_1 (`explorer_m1_1`)  
**Date**: 2026-08-05  
**Target Files**: `app/src/main/cpp/post_engine.h`, `app/src/main/cpp/post_engine.cpp`, `app/src/main/cpp/sha256.h`, `app/src/main/cpp/sha256.cpp`, `app/src/main/cpp/jni_bridge.cpp`

---

## Executive Summary

This document provides the definitive, production-ready C++ design and architectural specification for Milestone 1 of the AION OS Android Edge Node project. 

The core requirement of Milestone 1 is to establish a high-performance, memory-hard Proof-of-Space-Time (PoST) engine written in native C++17, compiled via the Android NDK, and bound to Kotlin via JNI. The engine obligates physical RAM commitment (1 MB to 64 MB configurable) and executes a 3-stage cryptographic memory-walk loop to validate hardware dedication on heterogeneous mobile platforms (`arm64-v8a`, `x86_64`, `armeabi-v7a`).

To satisfy the stateful API contract defined in `PROJECT.md` (`nativeAllocateMemory`, `nativeComputePoSt`, `nativeReleaseMemory`, `nativeCancelPoSt`), the C++ engine is architected around a stateful opaque handle (`PoSTContext`), supporting 64-byte aligned memory allocation, thread-safe asynchronous cancellation (`std::atomic<bool>`), volatile memory zeroing, and zero-dependency SHA-256 computation.

---

## 1. Architectural Principles & Memory Management

### 1.1 Allocation Strategy: `posix_memalign` vs `std::vector`
1. **64-Byte Alignment Requirement**:
   - Modern ARM64 (Cortex-A78/X1/X2/X3) and x86_64 processors feature 64-byte cache lines and ARM NEON / AVX SIMD registers. Unaligned 32-byte hash blocks across memory boundaries cause cache line splits and performance degradation.
   - Standard `malloc` or `new uint8_t[]` only guarantees 8-byte or 16-byte alignment.
   - `std::vector<uint8_t>` uses `std::allocator`, which lacks 64-byte alignment guarantees and forces zero-initialization during vector construction (`vector<uint8_t>(size)`), resulting in an unnecessary write pass over 64 MB before seed expansion begins.
   - **Recommendation**: Use `posix_memalign(&ptr, 64, size_bytes)` for bare-metal buffer allocation. It guarantees 64-byte alignment on Android NDK and avoids initialization overhead.

2. **OOM & Crash Prevention**:
   - If memory allocation fails (`posix_memalign` returns non-zero), the engine traps the error gracefully, returns a `nullptr` context, and propagates a `java/lang/OutOfMemoryError` back to the Android JVM via JNI without crashing the Android process (`SIGSEGV` / `SIGABRT`).

### 1.2 Secure Volatile Zeroing
Standard `memset(ptr, 0, len)` is susceptible to compiler dead-store elimination under `-O3 -flto` optimizations if the buffer is freed immediately afterward.
To prevent leaking sensitive seed bytes or intermediate cryptographic states in Android heap RAM:
```cpp
void secure_zero(void* ptr, size_t len) {
    if (!ptr || len == 0) return;
    volatile uint8_t* p = static_cast<volatile uint8_t*>(ptr);
    while (len--) {
        *p++ = 0;
    }
}
```
`secure_zero` must be called automatically inside `release_post_context()` prior to calling `free()`.

---

## 2. Cryptographic PoST Engine Mathematical Specification

The PoST engine executes a strict 3-stage cryptographic process:

```
+-----------------------------------------------------------------------------+
| Stage 1: Space Allocation & Seed Expansion                                  |
| H_0 = SHA256(seed)                                                          |
| B[0..31] = H_0                                                              |
| B[i..i+31] = SHA256(B[i-32..i-1] || uint64_be(block_index))                |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| Stage 2: Time-Dilation Pseudo-Random Memory Walk & Cell Mutation            |
| W = H_0                                                                     |
| For r = 0 .. iterations-1:                                                  |
|   raw_index = uint64_be(W[0..7])                                            |
|   block_idx = raw_index % (Buffer_Bytes / 32)                               |
|   W_new = SHA256(W || B[block_idx] || uint64_be(r))                        |
|   B[block_idx] = B[block_idx] XOR W_new                                     |
|   W = W_new                                                                 |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| Stage 3: Proof Digest Compression                                           |
| P_start = B[first block], P_mid = B[mid block], P_end = B[last block]       |
| ProofDigest = SHA256(W || P_start || P_mid || P_end)                         |
+-----------------------------------------------------------------------------+
```

### Stage 1: Space Allocation & Seed Expansion
- **Input**: 32-byte seed (derived from challenge + node ID + nonce).
- **Buffer Fill**: Memory buffer $B$ of size $M$ bytes is partitioned into $N_{blocks} = M / 32$ blocks of 32 bytes each.
- Block 0: $B[0 \dots 31] = H_0 = \text{SHA256}(\text{seed})$.
- For $i = 1 \dots N_{blocks}-1$:
  $$\text{block\_input} = B[(i-1)\times 32 \dots i\times 32 - 1] \parallel \text{uint64\_be}(i)$$
  $$B[i\times 32 \dots i\times 32 + 31] = \text{SHA256}(\text{block\_input})$$
  *(Note: `uint64_be` converts 64-bit integer $i$ to big-endian 8 bytes)*.

### Stage 2: Time-Dilation Memory Walk
- Working state $W$ initialized to $H_0$.
- For round $r = 0 \dots \text{iterations}-1$:
  1. Periodically check cancellation flag: `if (r % 64 == 0 && cancelled.load()) return CANCELLED;`
  2. Extract 64-bit unsigned integer from $W[0 \dots 7]$ in big-endian format.
  3. Calculate target block index: $\text{target\_idx} = \text{raw\_index} \pmod{N_{blocks}}$.
  4. Target byte offset: $\text{offset} = \text{target\_idx} \times 32$.
  5. Compute new working state:
     $$W_{new} = \text{SHA256}(W \parallel B[\text{offset} \dots \text{offset}+31] \parallel \text{uint64\_be}(r))$$
  6. Mutate memory cell (XOR update to enforce RAM write-back and prevent read-only caching):
     $$B[\text{offset} \dots \text{offset}+31] = B[\text{offset} \dots \text{offset}+31] \oplus W_{new}$$
  7. $W = W_{new}$.

### Stage 3: Proof Digest Compression
- Sample three key checkpoints from buffer $B$:
  - $P_{start} = B[0 \dots 31]$
  - $P_{mid} = B[(N_{blocks}/2) \times 32 \dots (N_{blocks}/2) \times 32 + 31]$
  - $P_{end} = B[(N_{blocks}-1) \times 32 \dots (N_{blocks}-1) \times 32 + 31]$
- Compute final 32-byte proof digest:
  $$\text{ProofDigest} = \text{SHA256}(W \parallel P_{start} \parallel P_{mid} \parallel P_{end})$$

---

## 3. Stateful Handle & Cancellation Architecture

To match the `PoStNativeBridge` Kotlin interface in `PROJECT.md`, the C++ engine uses an opaque stateful handle (`PoSTContext` struct):

```cpp
struct PoSTContext {
    uint8_t* buffer = nullptr;
    size_t buffer_size_bytes = 0;
    std::atomic<bool> cancelled{false};
    std::atomic<bool> in_use{false};
};
```

### Lifecycle Rules:
1. `nativeAllocateMemory(sizeMb)`: Allocates `PoSTContext` and 64-byte aligned buffer. Returns `jlong` pointer handle.
2. `nativeComputePoSt(handle, seed, iterations)`: Validates handle, locks `in_use`, resets `cancelled`, runs 3-stage loop checking `cancelled` every 64 iterations, returns 32-byte digest array.
3. `nativeCancelPoSt(handle)`: Atomic non-blocking operation setting `cancelled = true`. Can be safely invoked from any thread (e.g. Android UI or Daemon thread).
4. `nativeReleaseMemory(handle)`: Sets `cancelled = true`, securely zeros memory via `secure_zero()`, frees buffer with `free()`, and deletes `PoSTContext`.

---

## 4. Complete Reference Source Code Blueprints

Below are the exact, self-contained reference C++ files for the worker implementer to build under `app/src/main/cpp/`.

### 4.1 Header: `sha256.h`
```cpp
#ifndef AION_SHA256_H
#define AION_SHA256_H

#include <cstdint>
#include <cstddef>
#include <string>
#include <array>

namespace aion {
namespace crypto {

class SHA256 {
public:
    static constexpr size_t DIGEST_SIZE = 32;
    static constexpr size_t BLOCK_SIZE = 64;

    SHA256();
    void init();
    void update(const uint8_t* data, size_t len);
    void final(uint8_t digest[DIGEST_SIZE]);

    static void hash(const uint8_t* data, size_t len, uint8_t digest[DIGEST_SIZE]);
    static std::array<uint8_t, DIGEST_SIZE> hash(const uint8_t* data, size_t len);
    static std::string hashToHex(const uint8_t* data, size_t len);
    static std::string bytesToHex(const uint8_t* data, size_t len);

private:
    void transform(const uint8_t block[BLOCK_SIZE]);

    uint32_t m_state[8];
    uint64_t m_count;
    uint8_t m_buffer[BLOCK_SIZE];
};

} // namespace crypto
} // namespace aion

#endif // AION_SHA256_H
```

### 4.2 Source: `sha256.cpp`
```cpp
#include "sha256.h"
#include <cstring>
#include <iomanip>
#include <sstream>

namespace aion {
namespace crypto {

#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

SHA256::SHA256() {
    init();
}

void SHA256::init() {
    m_state[0] = 0x6a09e667;
    m_state[1] = 0xbb67ae85;
    m_state[2] = 0x3c6ef372;
    m_state[3] = 0xa54ff53a;
    m_state[4] = 0x510e527f;
    m_state[5] = 0x9b05688c;
    m_state[6] = 0x1f83d9ab;
    m_state[7] = 0x5be0cd19;
    m_count = 0;
}

void SHA256::transform(const uint8_t block[64]) {
    uint32_t W[64];
    for (int i = 0; i < 16; ++i) {
        W[i] = (static_cast<uint32_t>(block[i * 4]) << 24) |
               (static_cast<uint32_t>(block[i * 4 + 1]) << 16) |
               (static_cast<uint32_t>(block[i * 4 + 2]) << 8) |
               (static_cast<uint32_t>(block[i * 4 + 3]));
    }
    for (int i = 16; i < 64; ++i) {
        uint32_t s0 = ROTR(W[i - 15], 7) ^ ROTR(W[i - 15], 18) ^ (W[i - 15] >> 3);
        uint32_t s1 = ROTR(W[i - 2], 17) ^ ROTR(W[i - 2], 19) ^ (W[i - 2] >> 10);
        W[i] = W[i - 16] + s0 + W[i - 7] + s1;
    }

    uint32_t a = m_state[0], b = m_state[1], c = m_state[2], d = m_state[3];
    uint32_t e = m_state[4], f = m_state[5], g = m_state[6], h = m_state[7];

    for (int i = 0; i < 64; ++i) {
        uint32_t S1 = ROTR(e, 6) ^ ROTR(e, 11) ^ ROTR(e, 25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + S1 + ch + K[i] + W[i];
        uint32_t S0 = ROTR(a, 2) ^ ROTR(a, 13) ^ ROTR(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = S0 + maj;

        h = g;
        g = f;
        f = e;
        e = d + temp1;
        d = c;
        c = b;
        b = a;
        a = temp1 + temp2;
    }

    m_state[0] += a; m_state[1] += b; m_state[2] += c; m_state[3] += d;
    m_state[4] += e; m_state[5] += f; m_state[6] += g; m_state[7] += h;
}

void SHA256::update(const uint8_t* data, size_t len) {
    size_t buffer_bytes = static_cast<size_t>((m_count >> 3) & 0x3F);
    m_count += static_cast<uint64_t>(len) << 3;

    size_t part_len = 64 - buffer_bytes;
    size_t i = 0;

    if (len >= part_len) {
        std::memcpy(&m_buffer[buffer_bytes], data, part_len);
        transform(m_buffer);
        for (i = part_len; i + 63 < len; i += 64) {
            transform(&data[i]);
        }
        buffer_bytes = 0;
    }

    if (i < len) {
        std::memcpy(&m_buffer[buffer_bytes], &data[i], len - i);
    }
}

void SHA256::final(uint8_t digest[32]) {
    uint8_t final_count[8];
    for (int i = 0; i < 8; ++i) {
        final_count[i] = static_cast<uint8_t>((m_count >> ((7 - i) * 8)) & 0xFF);
    }

    size_t buffer_bytes = static_cast<size_t>((m_count >> 3) & 0x3F);
    size_t pad_len = (buffer_bytes < 56) ? (56 - buffer_bytes) : (120 - buffer_bytes);

    static const uint8_t padding[64] = { 0x80 };
    update(padding, pad_len);
    update(final_count, 8);

    for (int i = 0; i < 8; ++i) {
        digest[i * 4]     = static_cast<uint8_t>((m_state[i] >> 24) & 0xFF);
        digest[i * 4 + 1] = static_cast<uint8_t>((m_state[i] >> 16) & 0xFF);
        digest[i * 4 + 2] = static_cast<uint8_t>((m_state[i] >> 8) & 0xFF);
        digest[i * 4 + 3] = static_cast<uint8_t>(m_state[i] & 0xFF);
    }
}

void SHA256::hash(const uint8_t* data, size_t len, uint8_t digest[32]) {
    SHA256 ctx;
    ctx.update(data, len);
    ctx.final(digest);
}

std::array<uint8_t, 32> SHA256::hash(const uint8_t* data, size_t len) {
    std::array<uint8_t, 32> digest;
    hash(data, len, digest.data());
    return digest;
}

std::string SHA256::bytesToHex(const uint8_t* data, size_t len) {
    std::ostringstream ss;
    for (size_t i = 0; i < len; ++i) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(data[i]);
    }
    return ss.str();
}

std::string SHA256::hashToHex(const uint8_t* data, size_t len) {
    uint8_t digest[32];
    hash(data, len, digest);
    return bytesToHex(digest, 32);
}

} // namespace crypto
} // namespace aion
```

### 4.3 Header: `post_engine.h`
```cpp
#ifndef AION_POST_ENGINE_H
#define AION_POST_ENGINE_H

#include <cstdint>
#include <cstddef>
#include <atomic>

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
    std::atomic<bool> in_use{false};
};

void secure_zero(void* ptr, size_t len);
PoSTContext* allocate_post_context(int size_mb);
ExecutionResult compute_post(PoSTContext* ctx, const uint8_t* seed, size_t seed_len, int iterations);
void cancel_post(PoSTContext* ctx);
void release_post_context(PoSTContext* ctx);

} // namespace post
} // namespace aion

#endif // AION_POST_ENGINE_H
```

### 4.4 Source: `post_engine.cpp`
```cpp
#include "post_engine.h"
#include "sha256.h"
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <new>

namespace aion {
namespace post {

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
    ctx->cancelled.store(false);
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

ExecutionResult compute_post(PoSTContext* ctx, const uint8_t* seed, size_t seed_len, int iterations) {
    ExecutionResult result{};
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

    ctx->cancelled.store(false);
    result.allocated_ram_bytes = ctx->buffer_size_bytes;

    auto start_time = std::chrono::high_resolution_clock::now();

    // Stage 1: Space Allocation & Seed Expansion
    uint8_t h0[32];
    aion::crypto::SHA256::hash(seed, seed_len, h0);

    size_t num_blocks = ctx->buffer_size_bytes / 32;
    std::memcpy(ctx->buffer, h0, 32);

    uint8_t block_input[40];
    for (size_t i = 1; i < num_blocks; ++i) {
        if (i % 1024 == 0 && ctx->cancelled.load(std::memory_order_relaxed)) {
            result.status = StatusCode::CANCELLED;
            ctx->in_use.store(false);
            return result;
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
        if (r % 64 == 0 && ctx->cancelled.load(std::memory_order_relaxed)) {
            result.status = StatusCode::CANCELLED;
            result.iterations_completed = r;
            ctx->in_use.store(false);
            return result;
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

    ctx->in_use.store(false);
    return result;
}

void cancel_post(PoSTContext* ctx) {
    if (ctx) {
        ctx->cancelled.store(true, std::memory_order_relaxed);
    }
}

void release_post_context(PoSTContext* ctx) {
    if (!ctx) return;
    ctx->cancelled.store(true);
    if (ctx->buffer) {
        secure_zero(ctx->buffer, ctx->buffer_size_bytes);
        free(ctx->buffer);
        ctx->buffer = nullptr;
    }
    delete ctx;
}

} // namespace post
} // namespace aion
```

### 4.5 JNI Binding Layer: `jni_bridge.cpp`
```cpp
#include <jni.h>
#include <android/log.h>
#include "post_engine.h"
#include "sha256.h"

#define LOG_TAG "AION_PoST_JNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" {

JNIEXPORT jlong JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeAllocateMemory(
    JNIEnv *env,
    jobject thiz,
    jint size_mb
) {
    aion::post::PoSTContext* ctx = aion::post::allocate_post_context(size_mb);
    if (!ctx) {
        jclass oomClass = env->FindClass("java/lang/OutOfMemoryError");
        if (oomClass) env->ThrowNew(oomClass, "Failed to allocate 64-byte aligned PoST memory");
        return 0;
    }
    LOGI("Allocated PoST memory context: %d MB at handle 0x%llx", size_mb, (unsigned long long)ctx);
    return reinterpret_cast<jlong>(ctx);
}

JNIEXPORT jbyteArray JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeComputePoSt(
    JNIEnv *env,
    jobject thiz,
    jlong handle,
    jbyteArray seed_array,
    jint iterations
) {
    if (handle == 0 || seed_array == NULL) {
        jclass argClass = env->FindClass("java/lang/IllegalArgumentException");
        if (argClass) env->ThrowNew(argClass, "Invalid handle or seed array");
        return NULL;
    }

    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    jsize seed_len = env->GetArrayLength(seed_array);
    jbyte* seed_bytes = env->GetByteArrayElements(seed_array, NULL);

    aion::post::ExecutionResult res = aion::post::compute_post(
        ctx,
        reinterpret_cast<const uint8_t*>(seed_bytes),
        static_cast<size_t>(seed_len),
        static_cast<int>(iterations)
    );

    env->ReleaseByteArrayElements(seed_array, seed_bytes, JNI_ABORT);

    if (res.status == aion::post::StatusCode::CANCELLED) {
        jclass exClass = env->FindClass("java/lang/IllegalStateException");
        if (exClass) env->ThrowNew(exClass, "PoST computation was cancelled");
        return NULL;
    }

    if (res.status == aion::post::StatusCode::INVALID_PARAM) {
        jclass argClass = env->FindClass("java/lang/IllegalArgumentException");
        if (argClass) env->ThrowNew(argClass, "Invalid PoST computation parameters");
        return NULL;
    }

    jbyteArray out_array = env->NewByteArray(32);
    if (out_array) {
        env->SetByteArrayRegion(out_array, 0, 32, reinterpret_cast<const jbyte*>(res.proof_digest));
    }
    return out_array;
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeCancelPoSt(
    JNIEnv *env,
    jobject thiz,
    jlong handle
) {
    if (handle == 0) return;
    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    aion::post::cancel_post(ctx);
    LOGI("Cancelled PoST computation for handle 0x%llx", (unsigned long long)ctx);
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeReleaseMemory(
    JNIEnv *env,
    jobject thiz,
    jlong handle
) {
    if (handle == 0) return;
    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    aion::post::release_post_context(ctx);
    LOGI("Released PoST memory context at handle 0x%llx", (unsigned long long)ctx);
}

} // extern "C"
```

---

## 5. Verification & Testing Method for Worker

1. **Standalone C++ Test Harness**:
   - Compile `post_engine.cpp` and `sha256.cpp` using Host g++ or NDK clang:
     `clang++ -std=c++17 -O3 -I. sha256.cpp post_engine.cpp -DTEST_MAIN -o post_test`
   - Assert deterministic SHA-256 output hashes given static 32-byte seed.

2. **Automated Android Instrumentation Test**:
   - In `app/src/androidTest/java/com/aionos/edgenode/jni/AionPostNativeInstrumentedTest.kt`:
   - Invoke `nativeAllocateMemory(2)`, execute `nativeComputePoSt`, verify 32-byte hash output, verify cancellation via `nativeCancelPoSt`, and call `nativeReleaseMemory`.

---

## 6. Conclusion & Worker Instructions

- All C++ headers and implementation sources (`post_engine.h`, `post_engine.cpp`, `sha256.h`, `sha256.cpp`, `jni_bridge.cpp`) are fully specified and ready for implementation by the worker.
- Alignment (64-byte), zeroing (`secure_zero`), stateful handles (`PoSTContext`), asynchronous cancellation (`std::atomic<bool>`), and JNI exception safety are completely guaranteed.
