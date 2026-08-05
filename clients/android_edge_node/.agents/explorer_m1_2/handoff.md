# Handoff Report: Milestone 1 JNI Binding Layer Blueprint

**Agent**: Explorer M1_2 (`explorer_m1_2`)  
**Target Milestone**: Milestone 1 — Bare-Metal C++ PoST Engine & JNI Bridge  
**Date**: 2026-08-05  

---

## 1. Observation

- **Project Root**: `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node`
- **Interface Contract (`PROJECT.md`)**:
  - Package: `com.aionos.edgenode.jni` (lines 28, 58)
  - Native Library: `libaion_post.so` (line 27)
  - Class Name: `PoStNativeBridge` (line 29)
  - Method Signatures:
    - `private external native long nativeAllocateMemory(int sizeMb)` (line 31)
    - `private external native byte[] nativeComputePoSt(long handle, byte[] seed, int iterations)` (line 32)
    - `private external native void nativeReleaseMemory(long handle)` (line 33)
    - `private external native void nativeCancelPoSt(long handle)` (line 34)
  - Data Class `PoSTResult` (lines 35-41):
    - `proofDigest: ByteArray` (32 bytes)
    - `proofHex: String` (64 chars)
    - `executionTimeMs: Long`
    - `allocatedRamBytes: Long`
    - `iterationsCompleted: Int`
    - `statusCode: Int` (0 = SUCCESS, 1 = OOM, 2 = CANCELLED, 3 = INVALID_PARAM)
- **Directory Layout (`PROJECT.md`)**:
  - C++ source path: `app/src/main/cpp/jni_bridge.cpp` (line 55)
  - Kotlin source paths: `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt` (line 59), `app/src/main/java/com/aionos/edgenode/jni/PoSTResult.kt` (line 60)

---

## 2. Logic Chain

1. **Package & Naming Mapping**:
   From Observation 1 (`PROJECT.md`), the Kotlin class is `com.aionos.edgenode.jni.PoStNativeBridge`. Therefore, standard JNI symbol resolution dictates C++ exported function names must follow:
   - `Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeAllocateMemory`
   - `Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeComputePoSt`
   - `Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeReleaseMemory`
   - `Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeCancelPoSt`

2. **Handle-Based Native State Lifecycle**:
   From Observation 1, `nativeAllocateMemory` returns a 64-bit `long` handle. To prevent process-wide global variables and support concurrent/multi-instance PoST sessions safely, the C++ implementation instantiates a `PoSTContext` struct on the native heap and converts its memory address pointer to `jlong` via `reinterpret_cast<jlong>(ctx)`.

3. **Array Memory Management & Pinning Efficiency**:
   When receiving `jbyteArray j_seed`, calling `GetByteArrayElements` pins or copies the JVM byte array. Calling `ReleaseByteArrayElements` with mode `JNI_ABORT` when exiting ensures the JVM does not execute unnecessary sync writes back to Java heap, reducing execution latency.

4. **Structured Error Handling**:
   Passing raw errors directly through native JNI can trigger unhandled C++ exceptions or segmentation faults. Wrapping calculations in `try-catch` blocks and mapping statuses to `PoSTResult.statusCode` (0 = SUCCESS, 1 = OOM, 2 = CANCELLED, 3 = INVALID_PARAM) ensures thread safety, graceful JVM recovery, and predictable Kotlin handling.

5. **Kotlin Interface Design**:
   Exposing private native methods wrapped by public Kotlin functions (`allocateMemory`, `computePoSt`, `releaseMemory`, `cancelPoSt`) with `require()` precondition assertions ensures invalid arguments (e.g. 0 handle, wrong seed length) are caught early on the JVM side before native transition.

---

## 3. Caveats

- **Thread Affinity of JNIEnv**: `JNIEnv*` pointers cannot be shared across OS threads. In `jni_bridge.cpp`, any callbacks or long-running execution must use the `JNIEnv` passed directly to the calling thread.
- **NDK 64-bit Memory Handles**: On 32-bit platforms (`armeabi-v7a`), casting 32-bit pointers to 64-bit `jlong` handles zero-extends safely; however, 64-bit ARM (`arm64-v8a`) is the target architecture.
- **Direct Implementer Reliance**: The verbatim code snippets in `analysis.md` assume standard C++17 compilation with Android NDK r25+ and CMake 3.22.1+.

---

## 4. Conclusion

The technical design and JNI interface specification for Milestone 1 are complete. The proposed design satisfies all contract requirements in `PROJECT.md`, provides safe lifecycle handle management (`PoSTContext`), ensures memory zeroing upon release, translates errors cleanly, and includes production-ready verbatim code for `jni_bridge.cpp`, `PoStNativeBridge.kt`, and `PoSTResult.kt`.

---

## 5. Verification Method

To verify the JNI implementation once built by the implementer:

1. **JNI Header Verification**:
   Execute `javac -h` on `PoStNativeBridge.kt` and verify that the generated C header function signatures match `Java_com_aionos_edgenode_jni_PoStNativeBridge_...`.

2. **Native Library Load Verification**:
   Run an Android Instrumentation unit test (`AionPostNativeInstrumentedTest.kt`) on an emulator/device and confirm `System.loadLibrary("aion_post")` succeeds without `UnsatisfiedLinkError`.

3. **JNI Round-Trip Verification**:
   - `allocateMemory(2)` returns non-zero `handle`.
   - `computePoSt(handle, seed, 100)` returns `PoSTResult` with `isSuccess == true`, `proofDigest.size == 32`, and `proofHex.length == 64`.
   - `releaseMemory(handle)` frees physical RAM without leaking or crashing.

4. **Invalidation Conditions**:
   - Altering package package name `com.aionos.edgenode.jni`.
   - Modifying `PoSTResult` constructor signature without updating JNI `GetMethodID` descriptor `([BLjava/lang/String;JJII)V`.
