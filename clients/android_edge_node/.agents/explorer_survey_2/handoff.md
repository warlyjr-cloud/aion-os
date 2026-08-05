# Handoff Report: Android Edge Node App Design & Architecture Survey (Requirement R2)

**Author**: Explorer 2 (survey_2)  
**Recipient**: Orchestrator (parent)  
**Date**: 2026-08-05  

---

## 1. Observation

1. **Original Request**:
   - File Path: `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\ORIGINAL_REQUEST.md`
   - Line 15-16: `### R2. Design e Arquitetura do App` / `A equipe tem autonomia total para decidir a arquitetura visual e estrutural do aplicativo (Interface ou Headless Daemon).`
   - Line 12-13: `### R1. Cálculo de PoST Robusto em C++ (Bare-Metal/NDK)` / `A equipe deve implementar uma função nativa em C++ que aloque memória física no dispositivo e execute um loop matemático criptográfico para validar o esforço real do hardware, expondo o resultado via JNI para o Android.`

2. **Android Platform Execution Constraints**:
   - Standard Android background activities are paused (`onStop`) and killed by the OS when placed in background.
   - Non-foreground background services on Android 8.0+ (API 26+) are restricted and throw `BackgroundServiceStartNotAllowedException` if launched from background.
   - Android Doze Mode throttles CPU cycles and delays non-foreground tasks (`WorkManager` / `JobScheduler`).
   - Android Low Memory Killer (LMK) targets non-foreground apps first to reclaim memory.

3. **Generated Design Artifacts**:
   - Technical Analysis File: `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_survey_2\analysis.md`

---

## 2. Logic Chain

1. **Premise 1**: PoST (Proof of Space-Time) computation requires continuous physical memory allocation (hundreds of MBs to GBs) and constant CPU hash graph execution.
2. **Premise 2**: If built solely as a UI Activity (Pure UI), navigating away or turning off the screen causes Android OS to destroy the Activity and abort native memory/PoST threads (Observation 2).
3. **Premise 3**: If built solely as a background WorkManager/JobScheduler task (Pure Headless Daemon), Android Doze mode and background execution limits throttle CPU execution or delay execution by 15+ minutes, rendering continuous real-time hardware proof invalid (Observation 2).
4. **Deduction**: The application must utilize a **Hybrid Architecture** combining:
   - A **Foreground Service (`PoStDaemonService`)** with an active notification and `PARTIAL_WAKE_LOCK` to shield the C++ worker thread from Doze mode, LMK, and execution timeouts.
   - An interactive **Jetpack Compose UI** that binds dynamically to the service via `LocalBinder` / `StateFlow` for metrics display, configuration, and control.

---

## 3. Caveats

- **Device RAM Limitations**: The native C++ memory allocation size must be checked against available physical memory (`ActivityManager.MemoryInfo`) prior to allocation to prevent Out-Of-Memory (OOM) native aborts on low-RAM test devices/emulators.
- **Android 14 Foreground Service Requirements**: Android 14 (API 34) requires explicit `foregroundServiceType` declarations in `AndroidManifest.xml` (e.g. `specialUse` or `dataSync`).
- **No Direct Source Code Written**: As an Explorer agent, no application source files (`.kt`, `.cpp`, `.xml`) were created in the root project directory; all architectural specs are documented in `analysis.md`.

---

## 4. Conclusion

A **Hybrid Architecture (Jetpack Compose UI + Foreground Service Daemon)** is determined to be the optimal design for the AION OS Android Edge Node app (Requirement R2).

Key structural specifications established:
1. **Package**: `com.aionos.edgenode` with Clean Architecture layering (`data`, `service`, `ui`, `util`).
2. **JNI Bridge**: `PoStNativeBridge` class with Kotlin native methods (`nativeAllocateMemory`, `nativeComputePoSt`, `nativeReleaseMemory`, `nativeCancelPoSt`) and asynchronous `PoStNativeListener` progress callbacks.
3. **State Model**: Reactive `PoStState` containing 7 distinct statuses (`IDLE`, `ALLOCATING_MEMORY`, `PROVING`, `PAUSED`, `CANCELLED`, `COMPLETED`, `FAILED`), hash rate (H/s), allocated RAM (MB), and progress percentage.
4. **Execution & Lifecycle**: `PoStDaemonService` maintaining `PARTIAL_WAKE_LOCK`, IO coroutine dispatching, ongoing notification, and decoupled UI binding via `StateFlow`.

---

## 5. Verification Method

1. **Inspect Analysis File**:
   - Verify `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_survey_2\analysis.md` contains the complete architectural evaluation, package diagram, JNI wrapper code, state model, and manifest permissions.
2. **Verify Layout & Guidelines Compliance**:
   - Confirm all metadata and analysis outputs are located strictly within `.agents/explorer_survey_2/` and no temporary/code files were placed in the project root.
3. **Downstream Implementation Verification**:
   - When implementers construct `PoStDaemonService.kt` and `PoStNativeBridge.kt`, test background persistence by running `./gradlew test` and running an Android instrumentation/emulator test where the app is backgrounded while verifying PoST progress continues uninterrupted.
