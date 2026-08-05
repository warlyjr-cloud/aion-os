# Technical Analysis & Specification: Milestone 1 JNI Binding Layer

**Author**: Explorer M1_2 (`explorer_m1_2`)  
**Project**: AION OS Android Edge Node  
**Milestone**: Milestone 1 — Bare-Metal C++ PoST Engine & JNI Bridge  
**Focus**: JNI Binding Layer (`jni_bridge.cpp`, `PoStNativeBridge.kt`, `PoSTResult.kt`)  
**Date**: 2026-08-05  

---

## 1. Executive Summary

Milestone 1 establishes the core computational foundation of the AION OS Android Edge Node, bridging high-performance bare-metal C++ cryptographic calculations (`libaion_post.so`) with the Android JVM via Java Native Interface (JNI).

This report provides the complete, production-grade technical design, interface specification, lifecycle handle model, JNI memory conversion rules, exception boundary handling, and verbatim source code blueprints for the three key JNI components:
1. `app/src/main/cpp/jni_bridge.cpp` — Native C++ JNI bridge exported functions.
2. `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt` — Kotlin native binding wrapper class.
3. `app/src/main/java/com/aionos/edgenode/jni/PoSTResult.kt` — Immutable result data class.

---

## 2. Interface Contract Alignment

According to `PROJECT.md`, the JNI layer must satisfy the following exact package structure and method contracts:

- **Java Package**: `com.aionos.edgenode.jni`
- **Native Shared Library**: `libaion_post.so` (loaded via `System.loadLibrary("aion_post")`)
- **Kotlin Class**: `PoStNativeBridge`
- **Target Native Methods**:
  - `private external native long nativeAllocateMemory(int sizeMb)`
  - `private external native byte[] nativeComputePoSt(long handle, byte[] seed, int iterations)` — *or returning `PoSTResult` object directly from JNI*
  - `private external native void nativeReleaseMemory(long handle)`
  - `private external native void nativeCancelPoSt(long handle)`

---

## 3. Exact JNI C++ Function Signatures (`extern "C"`)

JNI relies on strict function naming conventions to resolve native symbols exported by dynamic libraries. For Java package `com.aionos.edgenode.jni` and class `PoStNativeBridge`:

```cpp
#include <jni.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Class:     com_aionos_edgenode_jni_PoStNativeBridge
 * Method:    nativeAllocateMemory
 * Signature: (I)J
 */
JNIEXPORT jlong JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeAllocateMemory(
    JNIEnv *env,
    jobject thiz,
    jint j_size_mb
);

/*
 * Class:     com_aionos_edgenode_jni_PoStNativeBridge
 * Method:    nativeComputePoSt
 * Signature: (J[BI)Lcom/aionos/edgenode/jni/PoSTResult;
 */
JNIEXPORT jobject JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeComputePoSt(
    JNIEnv *env,
    jobject thiz,
    jlong j_handle,
    jbyteArray j_seed,
    jint j_iterations
);

/*
 * Class:     com_aionos_edgenode_jni_PoStNativeBridge
 * Method:    nativeReleaseMemory
 * Signature: (J)V
 */
JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeReleaseMemory(
    JNIEnv *env,
    jobject thiz,
    jlong j_handle
);

/*
 * Class:     com_aionos_edgenode_jni_PoStNativeBridge
 * Method:    nativeCancelPoSt
 * Signature: (J)V
 */
JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeCancelPoSt(
    JNIEnv *env,
    jobject thiz,
    jlong j_handle
);

#ifdef __cplusplus
}
#endif
```

---

## 4. Native Handle Lifecycle & Memory Safety Design

### 4.1 Native `PoSTContext` Handle Wrapper
To allow non-blocking allocations, long-running computation loops, and asynchronous cancellation signals from Kotlin without global state, native allocations are wrapped in a dynamic C++ heap structure called `PoSTContext`:

```cpp
struct PoSTContext {
    uint8_t* memory_buffer = nullptr;
    size_t buffer_size_bytes = 0;
    std::atomic<bool> is_cancelled{false};
    std::atomic<bool> is_computing{false};
    std::mutex context_mutex;
};
```

### 4.2 Pointer-to-`jlong` Conversion Rules
1. **Allocation (`nativeAllocateMemory`)**:
   - `PoSTContext* ctx = new (std::nothrow) PoSTContext();`
   - Physical memory allocated via 64-byte cache-aligned `posix_memalign` (or `aligned_alloc`).
   - The memory address pointer `reinterpret_cast<jlong>(ctx)` is returned as a 64-bit `jlong` handle to Kotlin.
2. **Method Invocations (`nativeComputePoSt`, `nativeCancelPoSt`)**:
   - The `jlong handle` parameter received from Kotlin is validated (`handle != 0L`) and cast back: `PoSTContext* ctx = reinterpret_cast<PoSTContext*>(handle);`.
3. **Deallocation (`nativeReleaseMemory`)**:
   - Memory buffer is sanitized using volatile zeroing (`volatile uint8_t* p = ctx->memory_buffer; ...`).
   - Aligned buffer is freed via `free(ctx->memory_buffer)`.
   - Context is deleted (`delete ctx`) and set to `nullptr` to prevent use-after-free or double-free vulnerabilities.

---

## 5. JNI Byte Array & String Data Conversions

### 5.1 Input Array Conversion (`seed: ByteArray`)
- **Pinning vs. Copying**: Calling `env->GetByteArrayElements(j_seed, NULL)` provides a pointer to native bytes.
- **Mode Flag Optimization**: When releasing the input seed array, specify `JNI_ABORT` mode:
  `env->ReleaseByteArrayElements(j_seed, seed_bytes, JNI_ABORT);`
  This informs the JVM that the C++ code did NOT modify the array, skipping expensive buffer sync back to JVM memory.

### 5.2 Output Array Conversion (`proofDigest: ByteArray`)
- Allocates a new 32-byte JVM `jbyteArray`: `jbyteArray j_digest = env->NewByteArray(32);`
- Copies the binary digest from C++ stack memory into JVM byte array:
  `env->SetByteArrayRegion(j_digest, 0, 32, reinterpret_cast<const jbyte*>(raw_digest));`

### 5.3 Hexadecimal String Conversion (`proofHex: String`)
- Converts 32-byte binary SHA-256 digest into 64-character lowercase hexadecimal string natively:
  `char hex_str[65]; charToHex(raw_digest, 32, hex_str);`
- Wraps in JVM `jstring`: `jstring j_hex = env->NewStringUTF(hex_str);`

---

## 6. Exception Handling & Error Code Mapping Strategy

JNI functions must prevent unhandled native C++ exceptions from crashing the Android process (`SIGABRT`/`SIGSEGV`). 

### 6.1 Native Exception Catching & JVM Propagation
All native code inside JNI functions is wrapped in `try { ... } catch (...)` blocks.

| Error Condition | C++ Action | JNI / Kotlin Result |
|---|---|---|
| Invalid Handle (`handle == 0L`) | Log error, throw `IllegalArgumentException` | JVM throws `IllegalArgumentException("Invalid native handle")` |
| Null Seed (`seed == null`) | Log error, throw `IllegalArgumentException` | JVM throws `IllegalArgumentException("Seed array cannot be null")` |
| Invalid Size (`sizeMb <= 0` or `> 256`) | Log error, return `0L` or throw `IllegalArgumentException` | JVM throws `IllegalArgumentException` |
| Native OOM (`posix_memalign` fails) | Log error, throw `OutOfMemoryError` or return `PoSTResult(statusCode=1)` | JVM throws `OutOfMemoryError` / returns STATUS_OOM |
| User Cancellation | Interrupted loop via `is_cancelled` flag | Returns `PoSTResult(statusCode=2)` |

### 6.2 Status Code Enumeration (`PoSTResult`)
```
0 = STATUS_SUCCESS         (Computation completed successfully)
1 = STATUS_OOM             (Failed physical RAM allocation)
2 = STATUS_CANCELLED       (Operation gracefully aborted by user/service)
3 = STATUS_INVALID_PARAM   (Invalid handle, null seed, or illegal iteration count)
```

---

## 7. Verbatim Source Code Blueprints for Implementers

The following three complete source files are specified for direct implementation under `app/src/main/`:

### 7.1 `app/src/main/cpp/jni_bridge.cpp`

```cpp
#include <jni.h>
#include <android/log.h>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <atomic>
#include <mutex>
#include <new>

#include "post_engine.h"

#define LOG_TAG "AION_PoST_JNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

// Native context structure managed via jlong handle
struct PoSTContext {
    uint8_t* memory_buffer = nullptr;
    size_t buffer_size_bytes = 0;
    std::atomic<bool> is_cancelled{false};
    std::atomic<bool> is_computing{false};
    std::mutex context_mutex;
};

// Helper: Convert 32-byte digest to 64-character lowercase hex string
static void digest_to_hex(const uint8_t* digest, char* hex_out) {
    static const char hex_digits[] = "0123456789abcdef";
    for (size_t i = 0; i < 32; ++i) {
        hex_out[i * 2]     = hex_digits[(digest[i] >> 4) & 0x0F];
        hex_out[i * 2 + 1] = hex_digits[digest[i] & 0x0F];
    }
    hex_out[64] = '\0';
}

// Helper: Throw Java Exception
static void throw_java_exception(JNIEnv* env, const char* class_name, const char* message) {
    jclass ex_class = env->FindClass(class_name);
    if (ex_class != nullptr) {
        env->ThrowNew(ex_class, message);
    }
}

extern "C" {

JNIEXPORT jlong JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeAllocateMemory(
    JNIEnv *env,
    jobject thiz,
    jint j_size_mb
) {
    if (j_size_mb <= 0 || j_size_mb > 256) {
        throw_java_exception(env, "java/lang/IllegalArgumentException",
            "Requested memory size must be between 1 MB and 256 MB.");
        return 0L;
    }

    size_t bytes_to_allocate = static_cast<size_t>(j_size_mb) * 1024 * 1024;
    
    PoSTContext* ctx = new (std::nothrow) PoSTContext();
    if (ctx == nullptr) {
        throw_java_exception(env, "java/lang/OutOfMemoryError", "Failed to allocate native PoSTContext.");
        return 0L;
    }

    void* raw_ptr = nullptr;
    // Align to 64-byte boundary for NEON/AVX vectorization
    int res = posix_memalign(&raw_ptr, 64, bytes_to_allocate);
    if (res != 0 || raw_ptr == nullptr) {
        delete ctx;
        throw_java_exception(env, "java/lang/OutOfMemoryError", "posix_memalign failed to allocate physical RAM.");
        return 0L;
    }

    ctx->memory_buffer = static_cast<uint8_t*>(raw_ptr);
    ctx->buffer_size_bytes = bytes_to_allocate;
    ctx->is_cancelled.store(false);
    ctx->is_computing.store(false);

    LOGI("Native memory allocated successfully: %d MB (%zu bytes) at address %p",
         j_size_mb, bytes_to_allocate, ctx->memory_buffer);

    return reinterpret_cast<jlong>(ctx);
}

JNIEXPORT jobject JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeComputePoSt(
    JNIEnv *env,
    jobject thiz,
    jlong j_handle,
    jbyteArray j_seed,
    jint j_iterations
) {
    if (j_handle == 0L) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Native handle cannot be zero.");
        return nullptr;
    }

    if (j_seed == nullptr) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Seed byte array cannot be null.");
        return nullptr;
    }

    jsize seed_len = env->GetArrayLength(j_seed);
    if (seed_len != 32) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Seed byte array must be exactly 32 bytes.");
        return nullptr;
    }

    if (j_iterations <= 0) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Iteration count must be greater than zero.");
        return nullptr;
    }

    PoSTContext* ctx = reinterpret_cast<PoSTContext*>(j_handle);
    if (ctx->memory_buffer == nullptr || ctx->buffer_size_bytes == 0) {
        throw_java_exception(env, "java/lang/IllegalStateException", "Native memory buffer is uninitialized or freed.");
        return nullptr;
    }

    {
        std::lock_guard<std::mutex> lock(ctx->context_mutex);
        if (ctx->is_computing.load()) {
            throw_java_exception(env, "java/lang/IllegalStateException", "Computation already running on this handle.");
            return nullptr;
        }
        ctx->is_computing.store(true);
        ctx->is_cancelled.store(false);
    }

    jbyte* seed_bytes = env->GetByteArrayElements(j_seed, nullptr);
    if (seed_bytes == nullptr) {
        ctx->is_computing.store(false);
        throw_java_exception(env, "java/lang/OutOfMemoryError", "Failed to access JVM seed array elements.");
        return nullptr;
    }

    uint8_t proof_digest[32] = {0};
    uint64_t elapsed_ms = 0;
    int status_code = 0; // 0 = SUCCESS, 1 = OOM, 2 = CANCELLED, 3 = INVALID_PARAM
    int iterations_completed = 0;

    auto start_time = std::chrono::high_resolution_clock::now();

    try {
        // Execute C++ PoST Engine calculation pass
        status_code = execute_post_engine(
            reinterpret_cast<const uint8_t*>(seed_bytes),
            seed_len,
            ctx->memory_buffer,
            ctx->buffer_size_bytes,
            static_cast<uint32_t>(j_iterations),
            &ctx->is_cancelled,
            proof_digest,
            &iterations_completed
        );
    } catch (...) {
        LOGE("Unhandled Exception inside C++ execute_post_engine");
        status_code = 3;
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();

    // Release JNI array lock (JNI_ABORT preserves JVM array memory without copying)
    env->ReleaseByteArrayElements(j_seed, seed_bytes, JNI_ABORT);

    ctx->is_computing.store(false);

    // Prepare Return Data Class com.aionos.edgenode.jni.PoSTResult
    jclass result_class = env->FindClass("com/aionos/edgenode/jni/PoSTResult");
    if (result_class == nullptr) {
        LOGE("Failed to find class com/aionos/edgenode/jni/PoSTResult");
        return nullptr;
    }

    jmethodID constructor = env->GetMethodID(
        result_class,
        "<init>",
        "([BLjava/lang/String;JJII)V"
    );

    if (constructor == nullptr) {
        LOGE("Failed to find constructor for PoSTResult");
        return nullptr;
    }

    jbyteArray j_digest_array = env->NewByteArray(32);
    env->SetByteArrayRegion(j_digest_array, 0, 32, reinterpret_cast<const jbyte*>(proof_digest));

    char hex_str[65];
    digest_to_hex(proof_digest, hex_str);
    jstring j_hex_string = env->NewStringUTF(hex_str);

    jobject result_obj = env->NewObject(
        result_class,
        constructor,
        j_digest_array,
        j_hex_string,
        static_cast<jlong>(elapsed_ms),
        static_cast<jlong>(ctx->buffer_size_bytes),
        static_cast<jint>(iterations_completed),
        static_cast<jint>(status_code)
    );

    return result_obj;
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeReleaseMemory(
    JNIEnv *env,
    jobject thiz,
    jlong j_handle
) {
    if (j_handle == 0L) {
        return;
    }

    PoSTContext* ctx = reinterpret_cast<PoSTContext*>(j_handle);
    std::lock_guard<std::mutex> lock(ctx->context_mutex);

    if (ctx->memory_buffer != nullptr) {
        // Secure zeroing before free
        volatile uint8_t* p = ctx->memory_buffer;
        for (size_t i = 0; i < ctx->buffer_size_bytes; ++i) {
            p[i] = 0;
        }
        free(ctx->memory_buffer);
        ctx->memory_buffer = nullptr;
        ctx->buffer_size_bytes = 0;
    }

    LOGI("Native memory released safely for handle %p", ctx);
    delete ctx;
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeCancelPoSt(
    JNIEnv *env,
    jobject thiz,
    jlong j_handle
) {
    if (j_handle == 0L) {
        return;
    }

    PoSTContext* ctx = reinterpret_cast<PoSTContext*>(j_handle);
    ctx->is_cancelled.store(true);
    LOGI("Cancellation flag set for native handle %p", ctx);
}

} // extern "C"
```

---

### 7.2 `app/src/main/java/com/aionos/edgenode/jni/PoSTResult.kt`

```kotlin
package com.aionos.edgenode.jni

/**
 * Immutable data result returned from C++ Proof-of-Space-Time engine via JNI.
 *
 * @property proofDigest 32-byte binary SHA-256 digest of the final PoST commitment.
 * @property proofHex 64-character lowercase hexadecimal string representation of proofDigest.
 * @property executionTimeMs Total high-resolution execution duration in milliseconds.
 * @property allocatedRamBytes Physical bytes allocated in C++ native memory.
 * @property iterationsCompleted Total memory-hard hashing rounds completed before return.
 * @property statusCode Execution status code (0 = SUCCESS, 1 = OOM, 2 = CANCELLED, 3 = INVALID_PARAM).
 */
data class PoSTResult(
    val proofDigest: ByteArray,
    val proofHex: String,
    val executionTimeMs: Long,
    val allocatedRamBytes: Long,
    val iterationsCompleted: Int,
    val statusCode: Int
) {
    companion object {
        const val STATUS_SUCCESS = 0
        const val STATUS_OOM = 1
        const val STATUS_CANCELLED = 2
        const val STATUS_INVALID_PARAM = 3
    }

    /**
     * Returns true if computation finished successfully without error or cancellation.
     */
    val isSuccess: Boolean get() = statusCode == STATUS_SUCCESS

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as PoSTResult

        if (!proofDigest.contentEquals(other.proofDigest)) return false
        if (proofHex != other.proofHex) return false
        if (executionTimeMs != other.executionTimeMs) return false
        if (allocatedRamBytes != other.allocatedRamBytes) return false
        if (iterationsCompleted != other.iterationsCompleted) return false
        if (statusCode != other.statusCode) return false

        return true
    }

    override fun hashCode(): Int {
        var result = proofDigest.contentHashCode()
        result = 31 * result + proofHex.hashCode()
        result = 31 * result + executionTimeMs.hashCode()
        result = 31 * result + allocatedRamBytes.hashCode()
        result = 31 * result + iterationsCompleted
        result = 31 * result + statusCode
        return result
    }
}
```

---

### 7.3 `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt`

```kotlin
package com.aionos.edgenode.jni

/**
 * JNI Native Bridge exposing C++ PoST Bare-Metal Engine (`libaion_post.so`) to Android JVM.
 */
class PoStNativeBridge {

    companion object {
        init {
            System.loadLibrary("aion_post")
        }
    }

    /**
     * Native C++ method signatures matching C++ JNI exports in jni_bridge.cpp.
     */
    private external fun nativeAllocateMemory(sizeMb: Int): Long

    private external fun nativeComputePoSt(
        handle: Long,
        seed: ByteArray,
        iterations: Int
    ): PoSTResult?

    private external fun nativeReleaseMemory(handle: Long)

    private external fun nativeCancelPoSt(handle: Long)

    /**
     * Allocates native physical RAM (in Megabytes) for Space-Time commitment.
     * @param sizeMb Size in Megabytes (1 to 256 MB).
     * @return Handle pointer (`Long`) referencing the native C++ PoSTContext.
     */
    fun allocateMemory(sizeMb: Int): Long {
        require(sizeMb in 1..256) { "Memory size must be between 1 MB and 256 MB." }
        return nativeAllocateMemory(sizeMb)
    }

    /**
     * Computes Proof-of-Space-Time over allocated memory buffer.
     * @param handle 64-bit handle returned by [allocateMemory].
     * @param seed 32-byte challenge seed byte array.
     * @param iterations Target time-dilation iteration rounds.
     * @return [PoSTResult] containing final proof digest and execution statistics.
     */
    fun computePoSt(handle: Long, seed: ByteArray, iterations: Int): PoSTResult {
        require(handle != 0L) { "Native handle cannot be zero." }
        require(seed.size == 32) { "Seed byte array must be exactly 32 bytes." }
        require(iterations > 0) { "Iteration count must be greater than zero." }

        return nativeComputePoSt(handle, seed, iterations)
            ?: throw IllegalStateException("Native computation failed to return a valid PoSTResult object.")
    }

    /**
     * Releases physical RAM allocated to native handle safely.
     * @param handle 64-bit handle pointer returned by [allocateMemory].
     */
    fun releaseMemory(handle: Long) {
        if (handle != 0L) {
            nativeReleaseMemory(handle)
        }
    }

    /**
     * Signals native computation loop on the specified handle to cancel gracefully.
     * @param handle 64-bit handle pointer returned by [allocateMemory].
     */
    fun cancelPoSt(handle: Long) {
        if (handle != 0L) {
            nativeCancelPoSt(handle)
        }
    }
}
```

---

## 8. Verification Strategy & Invalidation Conditions

### 8.1 Verification Test Cases
1. **Signature Integrity Verification**: Ensure `javah` or `javac -h` generates exact signatures corresponding to `Java_com_aionos_edgenode_jni_PoStNativeBridge_...`.
2. **Handle Integrity**: Test passing valid handles, zero handles (`0L`), and freed handles. Ensure proper exception throwing (`IllegalArgumentException` / `IllegalStateException`).
3. **Cancellation Test**: Launch `computePoSt` in a background thread and call `cancelPoSt` after 50ms. Verify result returns `statusCode == STATUS_CANCELLED (2)`.
4. **Data Equals / HashCode Test**: Verify Kotlin `PoSTResult` equality logic works correctly for byte arrays.

### 8.2 Invalidation Conditions
- Changing package name from `com.aionos.edgenode.jni` would invalidate symbol Resolution.
- Changing `libaion_post.so` to another dynamic library name without updating `System.loadLibrary("aion_post")`.
- Passing non-pinned native array references or omitting `JNI_ABORT`.
