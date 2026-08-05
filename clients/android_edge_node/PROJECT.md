# Project: AION OS Android Edge Node PoST

## Architecture
- **Hybrid Architecture**: Jetpack Compose UI + Foreground Service Daemon (`PoStDaemonService`).
- **Bare-metal C++ PoST Engine**: `libaion_post.so` exposed via JNI (`PoStNativeBridge`).
- **Build System**: Gradle (Kotlin DSL) + NDK r25+ + CMake 3.22.1+.
- **Testing Strategy**: JUnit 4/5 Instrumentation Unit Tests in `app/src/androidTest/` validating JNI C++ hash returns natively.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | C++ Bare-Metal PoST Engine | 3-stage memory-hard cryptographic proof math loop with aligned physical RAM allocation & SHA-256 | M1 | survey_1 (R1) |
| 2 | JNI Native Bridge & Kotlin API | `PoStNativeBridge` Kotlin class with native methods (`nativeAllocateMemory`, `nativeComputePoSt`, `nativeReleaseMemory`, `nativeCancelPoSt`) and callback listener | M1 | survey_1 & survey_2 (R1, R2) |
| 3 | Project Build Toolchain & Android Setup | Gradle wrapper, `build.gradle.kts`, `CMakeLists.txt`, `AndroidManifest.xml`, NDK integration | M1 | survey_3 (R3) |
| 4 | Android App Architecture & Service Daemon | `PoStDaemonService` Foreground Service with Notification, `PARTIAL_WAKE_LOCK`, `StateFlow` state machine, and Jetpack Compose UI | M2 | survey_2 (R2) |
| 5 | Automated Native JNI Unit Test Suite | JUnit/Espresso tests in `app/src/androidTest/` calling native JNI functions and attesting deterministic SHA-256 hash returns | M3 | survey_3 (Acceptance Criteria) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: C++ Bare-Metal PoST Engine & JNI Bridge | C++ PoST algorithm, memory allocation, CMake build script, JNI binding layer (`PoStNativeBridge.kt`) | none | DONE |
| 2 | M2: Android Edge Node App & Daemon Service | Foreground Service (`PoStDaemonService`), notifications, WakeLock, Compose UI, state machine | M1 | DONE |
| 3 | M3: Automated JNI Unit Test Suite & Verification | JUnit / Espresso native JNI instrumentation test suite attesting cryptographic hash returns | M1, M2 | DONE |

## Interface Contracts
### C++ ↔ JNI ↔ Kotlin Interface
- Native C++ shared library: `libaion_post.so`
- Java package: `com.aionos.edgenode.jni`
- Class: `PoStNativeBridge`
- Native Method Signatures:
  - `private external native long nativeAllocateMemory(int sizeMb)`
  - `private external native byte[] nativeComputePoSt(long handle, byte[] seed, int iterations)`
  - `private external native void nativeReleaseMemory(long handle)`
  - `private external native void nativeCancelPoSt(long handle)`
- Data Class `PoSTResult`:
  - `proofDigest: ByteArray` (32-byte SHA-256 digest)
  - `proofHex: String` (64-char hex string)
  - `executionTimeMs: Long`
  - `allocatedRamBytes: Long`
  - `iterationsCompleted: Int`
  - `statusCode: Int` (0 = SUCCESS, 1 = OOM, 2 = CANCELLED, 3 = INVALID_PARAM)

## Code Layout
```
app/
├── CMakeLists.txt
├── build.gradle.kts
└── src/
    ├── main/
    │   ├── AndroidManifest.xml
    │   ├── cpp/
    │   │   ├── post_engine.h
    │   │   ├── post_engine.cpp
    │   │   ├── sha256.h
    │   │   ├── sha256.cpp
    │   │   └── jni_bridge.cpp
    │   └── java/com/aionos/edgenode/
    │       ├── jni/
    │       │   ├── PoStNativeBridge.kt
    │       │   └── PoSTResult.kt
    │       ├── service/
    │       │   └── PoStDaemonService.kt
    │       ├── ui/
    │       │   └── MainActivity.kt
    │       └── model/
    │           └── PoStState.kt
    └── androidTest/
        └── java/com/aionos/edgenode/
            └── AionPostNativeInstrumentedTest.kt
```
