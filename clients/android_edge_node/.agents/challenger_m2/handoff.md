# Handoff & Adversarial Challenge Report — Milestone 2

**Agent**: Challenger M2 (`challenger_m2`)  
**Milestone**: M2 (Android Edge Node App & Daemon Service)  
**Date**: 2026-08-05  
**Explicit Verdict**: `REJECT`

---

## Challenge Summary

- **Overall Risk Assessment**: **HIGH**
- **Tested Dimensions**:
  1. Service Lifecycle Management (`PoStDaemonService`)
  2. `PARTIAL_WAKE_LOCK` Acquisition & Release Safety
  3. Notification Channel Setup & Foreground Service Compliance (Android 8 – 14+)
  4. Service Unbind Edge Cases & Activity Lifecycle (`MainActivity`)
  5. StateFlow Concurrent Updates & Cancellation Races

---

## 1. Observations

### 1.1 Non-Atomic Guard in `startPoSt()` (`PoStDaemonService.kt:92-104`)
```kotlin
fun startPoSt(ramMb: Int = 16, iterations: Int = 1000, seed: ByteArray = ...) {
    if (_stateFlow.value.isRunning) return // Line 92: Non-atomic check

    acquireWakeLock()

    _stateFlow.value = PoStState(
        status = PoStStatus.ALLOCATING_MEMORY,
        ...
    )
    ...
    serviceScope.launch {
        val handle = nativeBridge.allocateMemory(ramMb) // Line 106
        ...
        currentHandle = handle // Line 115: Overwrites handle
```
- **Observation**: Checking `_stateFlow.value.isRunning` and updating `_stateFlow.value` to `ALLOCATING_MEMORY` is non-atomic. Concurrent calls to `startPoSt()` pass line 92 simultaneously.
- **Impact**: Multiple coroutines allocate native C++ PoST memory contexts (`allocate_post_context`). `currentHandle` is overwritten with the newest handle, leaking previously allocated C++ physical RAM handles which are never released by `finally`.

### 1.2 Race Condition in `cancelPoSt()` during Memory Allocation (`PoStDaemonService.kt:104-123`, `184-196`)
```kotlin
fun cancelPoSt() {
    val handle = currentHandle // Line 185: Evaluates to 0L during allocation
    if (handle != 0L) {
        try {
            nativeBridge.cancelPoSt(handle)
        } catch (_: Exception) {}
    }
    _stateFlow.value = _stateFlow.value.copy(
        status = PoStStatus.CANCELLED,
        errorMessage = "Cancellation requested."
    )
    updateNotification()
}
```
- **Observation**: While `nativeBridge.allocateMemory(ramMb)` is executing in `serviceScope.launch`, `currentHandle` remains `0L`. If `cancelPoSt()` is called during this window, `handle` is `0L`, so `nativeBridge.cancelPoSt` is never invoked in C++.
- **Impact**: `cancelPoSt()` sets `_stateFlow.value` to `CANCELLED`. However, when `allocateMemory` finishes, `serviceScope.launch` continues to line 118 (`_stateFlow.value = _stateFlow.value.copy(status = PoStStatus.PROVING)`), overwriting `CANCELLED` back to `PROVING` and executing `computePoSt` to completion despite the user's cancellation.

### 1.3 Activity Service Unbind Rebind Collector Accumulation (`MainActivity.kt:57-69`, `92-100`)
```kotlin
private val serviceConnection = object : ServiceConnection {
    override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
        val localBinder = binder as? PoStDaemonService.LocalBinder
        daemonService = localBinder?.getService()
        isBound = true
        observeDaemonState() // Line 62: Called on every connection/rebind
    }
    ...
}

private fun observeDaemonState() {
    lifecycleScope.launch { // Line 93: Spawns new coroutine on each rebind
        repeatOnLifecycle(Lifecycle.State.STARTED) {
            daemonService?.stateFlow?.collect { state -> updateUi(state) }
        }
    }
}
```
- **Observation**: `onServiceConnected` calls `observeDaemonState()` without cancelling prior state observation jobs. `unbindService` in `onStop()` does not cancel `lifecycleScope` collection jobs.
- **Impact**: Each Activity Stop/Start cycle (or rebind event) spawns an additional coroutine collector. Over multiple lifecycle events, duplicate collectors run in parallel on the UI thread updating views redundant times per StateFlow emission.

### 1.4 `PARTIAL_WAKE_LOCK` Safety Assessment (`PoStDaemonService.kt:200-220`, `272-283`)
```kotlin
private fun releaseWakeLock() {
    wakeLock?.let {
        if (it.isHeld) {
            it.release()
        }
    }
}
```
- **Observation**: `wakeLock` is initialized with `setReferenceCounted(false)`. `acquireWakeLock()` is called in `onCreate()` and `startPoSt()`. `releaseWakeLock()` is called in `onDestroy()` and in the `finally` block of `startPoSt()`.
- **Finding**: WakeLock acquisition and release logic is functional and released upon service stop/destroy. However, `it.release()` is not wrapped in `try-catch` to guard against potential `PowerManager` runtime exceptions on custom device ROMs.

### 1.5 Notification Channel & FGS Manifest Compliance (`AndroidManifest.xml:5-8, 29-37`, `PoStDaemonService.kt:68-78, 222-234`)
- **Observation**:
  - `CHANNEL_ID = "aion_post_daemon"` registered with `IMPORTANCE_LOW`.
  - Notification Builder uses `PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE`.
  - Service declares `android:foregroundServiceType="specialUse"` with `<property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" ... />`.
- **Finding**: Notification setup fully satisfies Android 8.0 – Android 14+ FGS requirements.

---

## 2. Logic Chain

1. **Premise**: Hardware computation daemons must safely manage memory, state transitions, UI bindings, and background wake locks.
2. **Step 1 (Concurrency Guard)**: `PoStDaemonService.startPoSt()` relies on `if (_stateFlow.value.isRunning) return`. Because `_stateFlow.value` check and state write are non-atomic, parallel callers invoke `allocateMemory` concurrently. Since `currentHandle` holds a single `Long`, earlier handles are overwritten and leaked in native memory.
3. **Step 2 (Cancellation Window)**: `startPoSt()` allocates memory before setting `currentHandle`. Calling `cancelPoSt()` during allocation fails to notify C++ engine and has its `CANCELLED` state overwritten back to `PROVING` when allocation completes.
4. **Step 3 (UI Rebind Collector Leak)**: `MainActivity` calls `observeDaemonState()` inside `onServiceConnected` without tracking or cancelling active collector jobs, leaking coroutines across Activity stop/rebind cycles.
5. **Step 4 (WakeLock Safety)**: WakeLock is safely released in `finally` and `onDestroy()`, but lacks exception wrapping around `WakeLock.release()`.
6. **Conclusion**: M2 core components are in place, but high-risk race conditions in service state control and memory context management require remediation before M2 approval.

---

## 3. Caveats

- Unit test harness was written in `app/src/test/java/com/aionos/edgenode/service/PoStDaemonServiceTest.kt` to empirically model state flow and cancellation race scenarios.
- Physical device battery drain over multi-hour execution under Android Doze mode requires physical hardware testing in M3.

---

## 4. Final Conclusion & Explicit Verdict

**Verdict**: `REJECT`

**Reasoning**:
While the Foreground Service structure, C++ bridge integration, Notification channel setup, and WakeLock mechanics are solidly designed, the implementation contains two critical concurrency vulnerabilities in `PoStDaemonService` (native handle leak via non-atomic `startPoSt` guard, and silently ignored cancellation during memory allocation) along with a UI coroutine collector leak on service rebind in `MainActivity`.

### Required Remediation Action Plan for Implementer:
1. **Atomic Guard in `startPoSt()`**:
   - Use an explicit synchronization block or atomic flag (`AtomicBoolean` / `@Synchronized`) to guard `startPoSt()` execution so concurrent calls cannot enter `ALLOCATING_MEMORY` or overwrite `currentHandle`.
2. **Fix `cancelPoSt()` Allocation Race**:
   - Track an `isCancelRequested` flag or check `_stateFlow.value.status == PoStStatus.CANCELLED` immediately after `allocateMemory()` returns. If cancelled during allocation, immediately release the handle and abort without starting `computePoSt`.
3. **Fix `MainActivity` State Flow Subscriber Leak**:
   - Store the `Job` returned by `observeDaemonState()` and cancel it before subscribing again, or collect `stateFlow` once within `lifecycleScope` bound to `repeatOnLifecycle(STARTED)`.
4. **Wrap `WakeLock.release()`**:
   - Wrap `wakeLock?.release()` inside `try { ... } catch (_: Exception) {}` in `releaseWakeLock()`.

---

## 5. Verification Method

To independently verify the bugs and subsequent fixes:
1. Inspect `PoStDaemonServiceTest.kt` in `app/src/test/java/com/aionos/edgenode/service/PoStDaemonServiceTest.kt`.
2. Run unit test suite: `./gradlew test`.
3. Inspect `PoStDaemonService.kt` lines 87-180 and `MainActivity.kt` lines 57-100.
