# Technical Analysis: Requirement R1 — C++ Native PoST Engine & JNI Architecture

**Project**: AION OS Android Edge Node  
**Target Requirement**: R1 — Robust C++ PoST calculation allocating physical memory, executing a cryptographic math loop, and exposing results via JNI to Android Java/Kotlin.  
**Author**: Explorer 1 (`survey_1`)  
**Date**: 2026-08-05  

---

## Executive Summary

This document provides a comprehensive technical design and architectural specification for Requirement R1 of the AION OS Android Edge Node. The core objective of R1 is to establish a bare-metal C++ Proof-of-Space-Time (PoST) engine compiled via the Android NDK and exposed through Java Native Interface (JNI). 

The PoST engine serves as a physical proof-of-work/space mechanism for mobile edge devices, requiring the device to commit physical RAM (configurable between 1 MB and 64 MB) and perform sequential, memory-hard cryptographic hash iterations. This deters spoofing and measures real hardware dedication on heterogeneous Android hardware (arm64-v8a, armeabi-v7a, x86_64).

---

## 1. System & Environment Overview

### 1.1 Filesystem & Root State
- **Project Root**: `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node`
- **Current State**: Project initialization stage. `.agents` metadata workspace configured. Source tree layout for Android app with C++ NDK integration needs to be established.

### 1.2 Target Android/NDK Toolchain Architecture
- **Build System**: Gradle with Android Gradle Plugin (AGP) version 8.+ using `externalNativeBuild` with CMake.
- **NDK Version**: NDK r25c / r26b or newer (CMake 3.22.1+).
- **Target Architectures**:
  1. `arm64-v8a` (Primary target for modern 64-bit Android smartphones & edge tablets)
  2. `x86_64` (Primary target for Android Emulators & development testing)
  3. `armeabi-v7a` (Optional legacy 32-bit support)

---

## 2. Cryptographic PoST Engine Mathematical Specification

### 2.1 Theoretical Foundation: Proof-of-Space-Time (PoST)
Unlike pure CPU-bound Proof-of-Work (like double-SHA256 in Bitcoin), a PoST algorithm requires both physical memory capacity ($M$ bytes) and sequential temporal effort ($T$ rounds). This prevents low-memory ASICs or lightweight virtual machines from faking effort, as memory accesses cannot be parallelized efficiently without allocating actual physical memory buffers.

### 2.2 Three-Stage PoST Math Loop Design

#### Stage 1: Seed Expansion & Memory Allocation (Space Phase)
1. **Input Parameters**:
   - `challenge` (32 bytes): Network-provided randomness seed.
   - `node_id` (32 bytes): Unique public identifier of the Android Edge Node.
   - `nonce` (uint64_t): Iteration counter for candidate searching.
   - `memory_size_bytes` (size_t): Target buffer size $M$ (e.g., $16\,\text{MB} = 16 \times 1024 \times 1024$ bytes).
2. **Buffer Initialization**:
   - Allocate contiguous aligned memory buffer $B$ of size $M$.
   - Compute initial seed hash $H_0 = \text{SHA256}(\text{challenge} \parallel \text{node\_id} \parallel \text{nonce})$.
   - Fill buffer $B$ sequentially:
     $$B[i \dots i+31] = \text{SHA256}(H_{prev} \parallel \text{i})$$
     for $i = 0, 32, 64, \dots, M-32$.

#### Stage 2: Time-Dilation Pseudo-Random Memory Walk (Time Phase)
To enforce physical retention of buffer $B$ in RAM and prevent cache-only calculation:
1. Initialize working hash state $W = H_0$.
2. Perform $R$ rounds of memory-hard mixing (where $R = \text{iterations}$, e.g. $1,000$ to $50,000$ rounds):
   $$\text{index} = (\text{uint64\_t}(W[0\dots7])) \pmod{(M / 32)} \times 32$$
   $$W = \text{SHA256}(W \parallel B[\text{index} \dots \text{index}+31] \parallel r)$$
   $$B[\text{index} \dots \text{index}+31] = B[\text{index} \dots \text{index}+31] \oplus W$$

*Key Property*: The read index for round $r+1$ depends unpredictably on the result of round $r$, forcing sequential RAM access latency.

#### Stage 3: Proof Digest Compression (Finalization Phase)
1. Aggregate the final working state $W$ with a final hash scan across sampled checkpoints in buffer $B$:
   $$\text{FinalHash} = \text{SHA256}(W \parallel B[0\dots31] \parallel B[M/2 \dots M/2+31] \parallel B[M-32 \dots M-1])$$
2. Return 32-byte binary digest (or 64-character hexadecimal representation) along with performance statistics.

---

## 3. C++ Native Architecture & Memory Safety Design

### 3.1 C++ Source Layout Recommendation
```
aion_edge_node/
└── app/
    └── src/
        └── main/
            └── cpp/
                ├── CMakeLists.txt
                ├── include/
                │   ├── post_engine.h
                │   ├── sha256.h
                │   └── jni_bridge.h
                └── src/
                    ├── post_engine.cpp
                    ├── sha256.cpp
                    └── jni_bridge.cpp
```

### 3.2 Memory Allocation Strategy & Safety Protocols
1. **Contiguous Aligned Memory**:
   - Use `posix_memalign` or aligned dynamic vectors (`std::vector<uint8_t>` with custom 64-byte alignment or `aligned_alloc`) to support ARM NEON vectorization and prevent unaligned memory access faults on mobile CPUs.
2. **Buffer Bounds & Sanity Constraints**:
   - Minimum memory limit: 1 MB ($1,048,576$ bytes).
   - Maximum memory limit: 64 MB ($67,108,864$ bytes) by default (configurable up to 256 MB on high-ram devices).
   - Validation before allocation: Check requested memory size against hardcoded safety limits.
3. **Out-of-Memory (OOM) & Crash Prevention**:
   - Exception isolation: Enclose allocations inside `try { ... } catch (const std::bad_alloc& e)` blocks.
   - If allocation fails, catch the error gracefully, free any partial allocations, and throw a descriptive Java exception (`java/lang/OutOfMemoryError` or custom code) back through JNI instead of crashing the process (`SIGABRT`/`SIGSEGV`).
4. **Secure Memory Sanitization**:
   - Upon task completion or exception, clear memory using volatile zeroing (`volatile uint8_t* p = buffer; while(len--) *p++ = 0;`) or `memset_s` before deallocation to prevent leaking cryptographic state in heap memory.

---

## 4. JNI Native Interface Design

### 4.1 Native Function Signature
We specify both static JNI function naming conventions and dynamic JNI registration patterns.

#### C++ Header (`post_engine.h` / `jni_bridge.h`)
```cpp
#ifndef AION_POST_ENGINE_H
#define AION_POST_ENGINE_H

#include <jni.h>
#include <cstdint>
#include <cstddef>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Struct representing the execution result of a PoST calculation.
 */
typedef struct {
    uint8_t proof_hash[32];     // 256-bit cryptographic digest
    uint64_t elapsed_time_ms;   // High-resolution execution time
    size_t allocated_bytes;     // Exact physical bytes allocated
    uint32_t iterations_done;   // Total round iterations executed
    int32_t status_code;        // 0 = Success, -1 = OOM, -2 = Invalid Arg
} PoSTResultNative;

/**
 * Computes Proof-of-Space-Time over a given seed and memory size.
 */
PoSTResultNative execute_post_calculation(
    const uint8_t* challenge, size_t challenge_len,
    const uint8_t* node_id, size_t node_id_len,
    uint64_t nonce,
    size_t memory_size_bytes,
    uint32_t iterations
);

/* Static JNI Export definition */
JNIEXPORT jobject JNICALL
Java_com_aion_edgenode_post_PoSTEngine_calculatePoST(
    JNIEnv *env,
    jobject thiz,
    jbyteArray j_challenge,
    jbyteArray j_node_id,
    jlong j_nonce,
    jint j_memory_size_mb,
    jint j_iterations
);

#ifdef __cplusplus
}
#endif

#endif // AION_POST_ENGINE_H
```

### 4.2 Kotlin Interface Wrapper (`PoSTEngine.kt`)
```kotlin
package com.aion.edgenode.post

data class PoSTResult(
    val proofHashHex: String,
    val rawProofHash: ByteArray,
    val elapsedTimeMs: Long,
    val allocatedBytes: Long,
    val iterationsDone: Int,
    val statusCode: Int
) {
    val isSuccess: Boolean get() = statusCode == 0
}

class PoSTEngine {
    companion object {
        init {
            System.loadLibrary("aion_post_engine")
        }
    }

    /**
     * Executes native Proof-of-Space-Time calculation.
     * @param challenge 32-byte challenge seed
     * @param nodeId 32-byte edge node public ID
     * @param nonce Candidate nonce counter
     * @param memorySizeMb Buffer size in MB (e.g. 1..64)
     * @param iterations Number of time-dilation rounds (e.g. 1000..10000)
     */
    external fun calculatePoST(
        challenge: ByteArray,
        nodeId: ByteArray,
        nonce: Long,
        memorySizeMb: Int,
        iterations: Int
    ): PoSTResult
}
```

### 4.3 JNI Implementation & Data Conversion (`jni_bridge.cpp`)
```cpp
#include "jni_bridge.h"
#include "post_engine.h"
#include <android/log.h>
#include <cstring>
#include <chrono>

#define LOG_TAG "AION_PoST_Native"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static void charToHex(const uint8_t* in, size_t len, char* out) {
    static const char hexChars[] = "0123456789abcdef";
    for (size_t i = 0; i < len; ++i) {
        out[i * 2]     = hexChars[(in[i] >> 4) & 0x0F];
        out[i * 2 + 1] = hexChars[in[i] & 0x0F];
    }
    out[len * 2] = '\0';
}

JNIEXPORT jobject JNICALL
Java_com_aion_edgenode_post_PoSTEngine_calculatePoST(
    JNIEnv *env,
    jobject thiz,
    jbyteArray j_challenge,
    jbyteArray j_node_id,
    jlong j_nonce,
    jint j_memory_size_mb,
    jint j_iterations
) {
    if (j_challenge == NULL || j_node_id == NULL) {
        jclass exClass = env->FindClass("java/lang/IllegalArgumentException");
        env->ThrowNew(exClass, "Challenge and Node ID arrays must not be null.");
        return NULL;
    }

    jsize challenge_len = env->GetArrayLength(j_challenge);
    jsize node_id_len = env->GetArrayLength(j_node_id);

    jbyte* challenge_bytes = env->GetByteArrayElements(j_challenge, NULL);
    jbyte* node_id_bytes = env->GetByteArrayElements(j_node_id, NULL);

    size_t target_memory_bytes = static_cast<size_t>(j_memory_size_mb) * 1024 * 1024;

    LOGI("Starting PoST calculation: Mem=%d MB, Iterations=%d", j_memory_size_mb, j_iterations);

    PoSTResultNative native_res = execute_post_calculation(
        reinterpret_cast<const uint8_t*>(challenge_bytes), static_cast<size_t>(challenge_len),
        reinterpret_cast<const uint8_t*>(node_id_bytes), static_cast<size_t>(node_id_len),
        static_cast<uint64_t>(j_nonce),
        target_memory_bytes,
        static_cast<uint32_t>(j_iterations)
    );

    // Release JNI array locks
    env->ReleaseByteArrayElements(j_challenge, challenge_bytes, JNI_ABORT);
    env->ReleaseByteArrayElements(j_node_id, node_id_bytes, JNI_ABORT);

    if (native_res.status_code == -1) {
        jclass oomClass = env->FindClass("java/lang/OutOfMemoryError");
        env->ThrowNew(oomClass, "Failed to allocate physical memory for PoST computation.");
        return NULL;
    }

    // Construct Kotlin PoSTResult Object
    jclass resultClass = env->FindClass("com/aion/edgenode/post/PoSTResult");
    jmethodID constructor = env->GetMethodID(
        resultClass, 
        "<init>", 
        "(Ljava/lang/String;[BJJII)V"
    );

    char hexStr[65];
    charToHex(native_res.proof_hash, 32, hexStr);
    jstring j_hex_string = env->NewStringUTF(hexStr);

    jbyteArray j_hash_array = env->NewByteArray(32);
    env->SetByteArrayRegion(j_hash_array, 0, 32, reinterpret_cast<const jbyte*>(native_res.proof_hash));

    jobject resultObj = env->NewObject(
        resultClass,
        constructor,
        j_hex_string,
        j_hash_array,
        static_cast<jlong>(native_res.elapsed_time_ms),
        static_cast<jlong>(native_res.allocated_bytes),
        static_cast<jint>(native_res.iterations_done),
        static_cast<jint>(native_res.status_code)
    );

    return resultObj;
}
```

---

## 5. CMake Build Configuration (`CMakeLists.txt`)

Below is the complete, self-contained `CMakeLists.txt` specification for Android NDK building:

```cmake
cmake_minimum_required(VERSION 3.22.1)

project("aion_post_engine" C CXX)

# Set C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization Flags for ARM64 / x86_64 Edge Performance
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -ffast-math -flto -fvisibility=hidden")

# Enable Android Log library
find_library(LOG_LIB log)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Define native library source files
add_library(
    aion_post_engine
    SHARED
    src/sha256.cpp
    src/post_engine.cpp
    src/jni_bridge.cpp
)

# Link standard libraries
target_link_libraries(
    aion_post_engine
    ${LOG_LIB}
)
```

### 5.1 Android Gradle Integration (`app/build.gradle.kts`)
```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.aion.edgenode"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.aion.edgenode"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        externalNativeBuild {
            cmake {
                cppFlags("-std=c++17")
                arguments("-DANDROID_STL=c++_shared")
                abiFilters("arm64-v8a", "x86_64")
            }
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
}
```

---

## 6. Cryptographic Determinism & Unit Testing Strategy

### 6.1 Determinism Test Vectors
To satisfy Acceptance Criterion R1 (Proof of Correctness via automated unit tests), the PoST C++ implementation must produce strictly deterministic output hashes given identical input vectors.

**Test Vector 1 (Minimal 1 MB Buffer, 100 Iterations)**:
- `Challenge`: `0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20`
- `NodeID`: `0xa1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf00`
- `Nonce`: `42`
- `MemorySizeMb`: `1`
- `Iterations`: `100`

### 6.2 JUnit Automated Unit Test Blueprint (`PoSTEngineTest.kt`)
```kotlin
package com.aion.edgenode

import com.aion.edgenode.post.PoSTEngine
import org.junit.Assert.*
import org.junit.Test

class PoSTEngineTest {

    @Test
    fun testPoSTCalculationSuccess() {
        val engine = PoSTEngine()
        val challenge = ByteArray(32) { it.toByte() }
        val nodeId = ByteArray(32) { (it + 16).toByte() }
        val nonce = 100L
        val memoryMb = 2 // 2 MB
        val iterations = 500

        val result = engine.calculatePoST(challenge, nodeId, nonce, memoryMb, iterations)

        assertNotNull(result)
        assertEquals(0, result.statusCode)
        assertTrue(result.isSuccess)
        assertEquals(64, result.proofHashHex.length)
        assertEquals(32, result.rawProofHash.size)
        assertEquals(2 * 1024 * 1024L, result.allocatedBytes)
        assertEquals(500, result.iterationsDone)
        assertTrue(result.elapsedTimeMs > 0)
    }

    @Test
    fun testPoSTDeterminism() {
        val engine = PoSTEngine()
        val challenge = ByteArray(32) { 0x42.toByte() }
        val nodeId = ByteArray(32) { 0x99.toByte() }
        val nonce = 1L
        val memoryMb = 1
        val iterations = 100

        val res1 = engine.calculatePoST(challenge, nodeId, nonce, memoryMb, iterations)
        val res2 = engine.calculatePoST(challenge, nodeId, nonce, memoryMb, iterations)

        assertEquals(res1.proofHashHex, res2.proofHashHex)
        assertArrayEquals(res1.rawProofHash, res2.rawProofHash)
    }
}
```

---

## 7. Comparative Assessment & Trade-Offs

| Architecture Dimension | Selected Strategy | Alternative Considered | Rationale for Choice |
| :--- | :--- | :--- | :--- |
| **Memory Allocation** | Dynamic aligned C++ Heap (`posix_memalign` / `std::vector`) | JNI `DirectByteBuffer` from Java | Higher allocation speeds in bare-metal C++, eliminates JVM heap fragmentation during large (64MB) allocations. |
| **Crypto Hash Library** | Standalone lightweight C++ SHA-256 implementation | Full OpenSSL / BoringSSL link | Reduces APK footprint by ~3MB, simplifies NDK build setup without external binary dependencies. |
| **JNI Result Delivery** | Custom Structured Data Class (`PoSTResult`) | Hex String or primitive `byte[]` | Encapsulates metadata (execution time, allocated bytes, status codes) cleanly for Android UI / Daemon services. |
| **Algorithm Class** | 3-Stage Memory-Hard Time-Dilation Walk | Pure CPU SHA-256 Iteration | Enforces hardware space allocation (RAM commitment) required by PoST consensus specification. |

---

## 8. Summary of Findings & Next Steps for Implementer

1. **Bare-metal C++ NDK implementation** is fully specified and architected for 1MB-64MB configurable memory commitment.
2. **JNI Layer** provides safe memory passing, boundary checks, and graceful OOM handling via Kotlin `PoSTResult`.
3. **Automated Unit Verification** blueprint is established with deterministic assertions on hash length, raw byte consistency, and execution statistics.
4. **Implementer Roadmap**:
   - Step 1: Create standard Android project folder structure.
   - Step 2: Implement C++ native components under `app/src/main/cpp/`.
   - Step 3: Configure `CMakeLists.txt` and `build.gradle.kts`.
   - Step 4: Implement Kotlin `PoSTEngine` wrapper and JUnit unit tests.
