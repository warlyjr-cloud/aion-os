## 2026-08-05T13:22:40-03:00

You are Worker 1 (worker_m1) for Milestone 1 of the AION OS Android Edge Node project.

Project Root: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node
Working Directory: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\worker_m1
Original Request Path: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\ORIGINAL_REQUEST.md
Project File: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\PROJECT.md

Explorer Analysis Inputs:
- C++ PoST Engine Spec: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_m1_1\analysis.md
- JNI Binding Layer Spec: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_m1_2\analysis.md
- NDK & CMake Build Spec: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_m1_3\analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Objective:
Implement Milestone 1 (Bare-Metal C++ PoST Engine, CMake build setup, JNI Bridge Kotlin API).

Exclusive File Ownership:
You own creation and editing of the following files in the project root:
- `settings.gradle.kts`
- `build.gradle.kts` (root)
- `gradle.properties`
- `app/build.gradle.kts`
- `app/CMakeLists.txt`
- `app/src/main/AndroidManifest.xml`
- `app/src/main/cpp/sha256.h`
- `app/src/main/cpp/sha256.cpp`
- `app/src/main/cpp/post_engine.h`
- `app/src/main/cpp/post_engine.cpp`
- `app/src/main/cpp/jni_bridge.cpp`
- `app/src/main/java/com/aionos/edgenode/jni/PoSTResult.kt`
- `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt`

Tasks:
1. Initialize your briefing/progress files in `.agents/worker_m1/`.
2. Implement `sha256.h` and `sha256.cpp` (standalone FIPS 180-4 compliant SHA-256 implementation).
3. Implement `post_engine.h` and `post_engine.cpp` featuring `posix_memalign` aligned RAM allocation, zeroing, seed expansion, memory-hard pseudo-random access walk with XOR cell mutations, atomic cancellation checks, and proof compression.
4. Implement `jni_bridge.cpp` declaring JNI functions for package `com.aionos.edgenode.jni` and class `PoStNativeBridge` mapping native handle pointers, seed arrays, iterations, releasing memory safely, and exception translation.
5. Implement `PoSTResult.kt` and `PoStNativeBridge.kt` in `app/src/main/java/com/aionos/edgenode/jni/`.
6. Implement `CMakeLists.txt`, `app/build.gradle.kts`, `build.gradle.kts`, `settings.gradle.kts`, `gradle.properties`, and `AndroidManifest.xml`.
7. Verify build using native compiler/cmake or gradle build commands if available.
8. Document all changes in `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\worker_m1\changes.md` and deliver handoff report in `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\worker_m1\handoff.md`.
9. Send a message to orchestrator when complete.
