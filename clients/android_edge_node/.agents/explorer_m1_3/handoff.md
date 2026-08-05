# Handoff Report: Milestone 1 NDK & Gradle Build Configuration Specs

**Author:** Explorer M1_3 (`explorer_m1_3`)  
**Target Recipient:** Orchestrator (`orchestrator`)  
**Working Directory:** `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_m1_3`  
**Date:** 2026-08-05  

---

## 1. Observation

1. **Project Contract (`PROJECT.md`)**:
   - Architecture specifies: "Gradle (Kotlin DSL) + NDK r25+ + CMake 3.22.1+" (`PROJECT.md`, line 6).
   - Target package contract: `com.aionos.edgenode` (`PROJECT.md`, lines 28, 48-69).
   - Code layout defines build files at root and under `app/`: `CMakeLists.txt`, `build.gradle.kts`, `AndroidManifest.xml` (`PROJECT.md`, lines 45-70).
2. **Survey 3 Baseline (`.agents/explorer_survey_3/analysis.md`)**:
   - Survey established NDK r25+ / CMake 3.22.1 compatibility, Kotlin DSL gradle setup, and JNI instrumentation test strategy (`analysis.md`, lines 87-214).
3. **Original Request (`ORIGINAL_REQUEST.md`)**:
   - Focuses on native C++ (JNI/NDK) Proof of Space-Time (PoST) engine on Android (`ORIGINAL_REQUEST.md`, lines 5, 12-14).
4. **Dispatch Instructions (`DISPATCH.md`)**:
   - Scope: Milestone 1 — Bare-Metal C++ PoST Engine & JNI Bridge.
   - Focus: Formulate exact build configuration specs for NDK compilation of `libaion_post.so` with `arm64-v8a` and `x86_64` ABI targets.

---

## 2. Logic Chain

1. **Step 1 (Interface & Namespace Alignment)**:
   - Observation 1 defines Java package `com.aionos.edgenode` and Kotlin class `PoStNativeBridge`.
   - Therefore, `app/build.gradle.kts` must set `namespace = "com.aionos.edgenode"` and `applicationId = "com.aionos.edgenode"`. `AndroidManifest.xml` must declare components within this package namespace.
2. **Step 2 (Target ABI & NDK Configuration)**:
   - Dispatch instructions require target ABIs `arm64-v8a` (for physical 64-bit ARM Android hardware) and `x86_64` (for 64-bit Android emulators).
   - Therefore, `app/build.gradle.kts` must specify `abiFilters("arm64-v8a", "x86_64")` within the `externalNativeBuild.cmake` block.
   - NDK compilation requires STL support for C++17 memory allocation (`posix_memalign`, `std::aligned_alloc`, `<chrono>`, `<vector>`), so `arguments("-DANDROID_STL=c++_shared", "-DANDROID_PLATFORM=android-26")` and `cppFlags("-std=c++17 -O3 -Wall -Wextra -frtti -fexceptions")` are configured.
3. **Step 3 (CMake Library Definition)**:
   - C++ PoST engine source files (`post_engine.cpp`, `sha256.cpp`, `jni_bridge.cpp`) are compiled into dynamic shared library `libaion_post.so`.
   - `CMakeLists.txt` sets `cmake_minimum_required(VERSION 3.22.1)`, defines target `aion_post` as `SHARED`, and links against NDK logging library (`log-lib`).
4. **Step 4 (Gradle Build Toolchain Structure)**:
   - Root project configuration (`settings.gradle.kts`, root `build.gradle.kts`, `gradle.properties`) defines repositories, AGP 8.2.2 plugin, Kotlin 1.9.22 plugin, and JVM memory flags (`-Xmx2048m`).
   - App module (`app/build.gradle.kts`) specifies SDK levels (`compileSdk = 34`, `minSdk = 26`, `targetSdk = 34`), dependencies, and CMake path linkage.
5. **Step 5 (Manifest Permissions & Service Declaration)**:
   - Android manifest (`AndroidManifest.xml`) declares `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE`, `WAKE_LOCK`, and `POST_NOTIFICATIONS` permissions to support the PoSt daemon service, and registers `MainActivity` as launcher and `PoStDaemonService` as special use foreground service.

---

## 3. Caveats

- **Device Physical Execution**: The `x86_64` ABI filter enables fast emulation during testing, while `arm64-v8a` is required for production physical devices. 32-bit ABIs (`armeabi-v7a`, `x86`) are deliberately excluded to ensure 64-bit memory addressing for PoST RAM allocation.
- **NDK Path Discovery**: The build environment requires `ANDROID_HOME` or `ANDROID_NDK_HOME` to be configured, or NDK installed via Android SDK Manager at `ndk/25.2.9519653` (or any installed 25.x+ version).

---

## 4. Conclusion

All build configuration specifications for Milestone 1 are fully formulated, verified against `PROJECT.md`, and documented in `analysis.md`:
1. `settings.gradle.kts`
2. Root `build.gradle.kts`
3. `gradle.properties`
4. `app/build.gradle.kts` (with `arm64-v8a` and `x86_64` ABI filters)
5. `app/CMakeLists.txt` (compiling `libaion_post.so`)
6. `app/src/main/AndroidManifest.xml` (with daemon service & wake lock permissions)

These specs are ready for immediate implementation by the implementer worker (`implementer_m1`).

---

## 5. Verification Method

1. **File Verification**:
   - Inspect `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_m1_3\analysis.md` for complete code blueprints of all 6 build files.
2. **Build Execution Check (Post-Implementation)**:
   - Run `./gradlew assembleDebug` in project root.
   - Verify build success and inspect output APK for `lib/arm64-v8a/libaion_post.so` and `lib/x86_64/libaion_post.so`.
3. **Invalidation Conditions**:
   - Gradle fail with NDK missing error -> Ensure `ndk` component is installed in SDK.
   - JNI linking failure -> Check namespace `com.aionos.edgenode` matches C++ JNI function signatures.
