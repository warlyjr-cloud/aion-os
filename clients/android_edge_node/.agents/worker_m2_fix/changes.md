# Summary of Code Changes - Worker M2_fix

## Remediated Vulnerabilities & Bug Fixes

### 1. `PoStDaemonService.kt`
- **Atomic Execution Guard (`startPoSt`)**:
  - Introduced `private val isStarting = AtomicBoolean(false)` to guard entry into `startPoSt()`.
  - Used `if (!isStarting.compareAndSet(false, true)) return` atomically preventing concurrent callers from entering `ALLOCATING_MEMORY` or initiating duplicate background allocations.
  - Reset `isStarting.set(false)` inside the `finally` block of the service background job to ensure proper release on completion, failure, or cancellation.
- **Allocation Window Cancellation Race (`cancelPoSt` & `startPoSt`)**:
  - Introduced `private val isCancelled = AtomicBoolean(false)`.
  - In `cancelPoSt()`, set `isCancelled.set(true)`. If `currentHandle != 0L`, invoked `PoStNativeBridge.cancelPoSt(handle)` and `PoStNativeBridge.releaseMemory(handle)`.
  - In `startPoSt()`, checked `if (isCancelled.get())` immediately after `nativeBridge.allocateMemory(ramMb)` returns. If true, immediately calls `releaseMemory(handle)`, sets status to `PoStStatus.CANCELLED`, updates notifications, and aborts execution before calling `computePoSt()`.
- **WakeLock Release Exception Guard (`releaseWakeLock`)**:
  - Wrapped `wakeLock?.release()` inside a `try { ... } catch (_: Exception) {}` block to prevent potential runtime exceptions from PowerManager on custom ROMs during release.

### 2. `MainActivity.kt`
- **UI Subscriber Rebind Leak (`observeDaemonState` & `onStop`)**:
  - Maintained `private var observationJob: Job? = null` in `MainActivity`.
  - Called `observationJob?.cancel()` before spawning a new coroutine collecting `daemonService.stateFlow` in `observeDaemonState()`, storing the new coroutine in `observationJob`.
  - Cancelled `observationJob` and cleared reference in `onStop()` when Activity unbinds from service.

## Modified Files List
1. `app/src/main/java/com/aionos/edgenode/service/PoStDaemonService.kt`
2. `app/src/main/java/com/aionos/edgenode/ui/MainActivity.kt`
