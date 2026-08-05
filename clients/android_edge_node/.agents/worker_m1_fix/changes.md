# Changes Report — Worker M1_fix (Milestone 1 Iteration 2)

## Overview
Remediated all 4 critical/high/medium/low defects identified by Challenger M1_2 in the AION OS C++ Bare-Metal PoST Engine, JNI Bridge, and Kotlin `PoStNativeBridge`.

---

## Summary of Modified Files

| File Path | Changes Made |
|---|---|
| `app/src/main/cpp/post_engine.h` | Added `#include <mutex>` and `#include <condition_variable>`. Added `std::mutex lock;` and `std::condition_variable cv;` synchronization primitives to `PoSTContext` struct. |
| `app/src/main/cpp/post_engine.cpp` | Implemented `InUseGuard` RAII struct to guarantee atomic clearing of `in_use` and condition variable notification upon `compute_post` exit. Synchronized `release_post_context` to signal `cancelled = true` and wait via `cv.wait()` for active computation to complete before freeing memory and deleting `ctx`. Removed `ctx->cancelled.store(false)` overwrite to preserve early cancellation signals. |
| `app/src/main/cpp/jni_bridge.cpp` | Added `JNI_OnLoad` and `JNI_OnUnload` lifecycle handlers to cache `g_post_result_class` and `g_post_result_constructor` globally under `g_jni_cache_mutex`. Replaced `GetByteArrayElements`/`ReleaseByteArrayElements` with stack-allocated `GetByteArrayRegion` into `uint8_t seed_bytes[32]` to eliminate JNI heap memory pinning. |
| `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt` | Added `activeHandles` set (`ConcurrentHashMap.newKeySet<Long>()`) in companion object to track all active native memory handles. Updated `allocateMemory`, `computePoSt`, `releaseMemory`, and `cancelPoSt` to validate handle existence and throw `IllegalStateException("Handle released or invalid")` if zero or already released. |
| `app/src/main/java/com/aionos/edgenode/jni/PoSTResult.kt` | Verified immutable data class compatibility (no modifications required). |

---

## Detailed Technical Changes & Remediation Objectives

### 1. Fix Use-After-Free (UAF) Race Condition (`post_engine.h`, `post_engine.cpp`)
- **Problem**: `release_post_context` immediately freed `ctx->buffer` and called `delete ctx` without checking `ctx->in_use`. If called while `compute_post` was executing on a background thread, the worker thread suffered a Use-After-Free (SIGSEGV/SIGABRT) crash or heap corruption when writing/reading `ctx->buffer`.
- **Solution**:
  1. Extended `PoSTContext` with `std::mutex lock` and `std::condition_variable cv`.
  2. Implemented RAII helper `InUseGuard` inside `compute_post`. Upon any exit from `compute_post` (normal completion, error, or cancellation), `~InUseGuard` acquires `ctx->lock`, sets `ctx->in_use = false`, and calls `ctx->cv.notify_all()`.
  3. In `release_post_context`:
     - Sets `ctx->cancelled.store(true, std::memory_order_release)` to signal the worker thread to exit.
     - Locks `ctx->lock` and waits via `ctx->cv.wait(lock, [ctx] { return !ctx->in_use.load(std::memory_order_acquire); })`.
     - Ensures worker thread has completely exited `compute_post` before executing `secure_zero`, `free(ctx->buffer)`, and `delete ctx`.

### 2. Fix Cancellation Flag Overwrite (`post_engine.cpp`)
- **Problem**: `compute_post` unconditionally executed `ctx->cancelled.store(false)` after acquiring `in_use`. Calling `cancel_post(ctx)` before `compute_post` entered wiped out the cancellation signal and caused zombie computations.
- **Solution**:
  - Removed `ctx->cancelled.store(false)` from `compute_post`.
  - Added an explicit check right after acquiring `in_use`: `if (ctx->cancelled.load(std::memory_order_acquire)) { result.status = StatusCode::CANCELLED; return result; }`.
  - Fresh contexts start with `cancelled = false` from `allocate_post_context`. Pre-computation cancellation signals are now strictly preserved.

### 3. Fix Double-Free & Handle Safety in Kotlin (`PoStNativeBridge.kt`)
- **Problem**: Kotlin layer treated native handles as raw unmanaged `Long` primitives. Calling `releaseMemory(handle)` multiple times passed the same freed pointer to C++ `release_post_context`, causing double-free heap corruption.
- **Solution**:
  - Implemented an application-wide thread-safe active handle tracking set `activeHandles` (`ConcurrentHashMap.newKeySet<Long>()`) in `PoStNativeBridge.companion`.
  - On `allocateMemory`: Registers non-zero handle into `activeHandles`.
  - On `releaseMemory`: Atomically removes handle via `activeHandles.remove(handle)`. If handle is `0L` or not in `activeHandles` (already released), throws `IllegalStateException("Handle released or invalid")`.
  - On `computePoSt` & `cancelPoSt`: Checks `activeHandles.contains(handle)`. If `0L` or not present, throws `IllegalStateException("Handle released or invalid")`.

### 4. Optimize JNI Memory & Reflection Overhead (`jni_bridge.cpp`)
- **Problem**: `GetByteArrayElements` pinned JVM heap memory or allocated temporary buffers for 32-byte seed arrays. Every `nativeComputePoSt` call performed reflection (`FindClass` & `GetMethodID`) for `PoSTResult`.
- **Solution**:
  - Replaced `GetByteArrayElements` with stack copy: `env->GetByteArrayRegion(seed_array, 0, 32, reinterpret_cast<jbyte*>(seed_bytes))`.
  - Implemented JNI class caching in `JNI_OnLoad` / `JNI_OnUnload` to cache `g_post_result_class` (Global Ref) and `g_post_result_constructor` (`jmethodID`) under mutex protection `g_jni_cache_mutex`.
