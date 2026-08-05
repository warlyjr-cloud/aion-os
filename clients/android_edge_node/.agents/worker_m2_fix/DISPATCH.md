## 2026-08-05T16:45:45Z
You are Worker M2_fix (worker_m2_fix) for Milestone 2 Iteration 2 of the AION OS Android Edge Node project.

Project Root: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node
Working Directory: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\worker_m2_fix
Original Request Path: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\ORIGINAL_REQUEST.md
Project File: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\PROJECT.md
Challenger Handoff: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\challenger_m2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusive File Ownership:
You own editing of:
- `app/src/main/java/com/aionos/edgenode/service/PoStDaemonService.kt`
- `app/src/main/java/com/aionos/edgenode/ui/MainActivity.kt`

Tasks & Remediation Objectives (Fix Challenger M2 Findings):
1. **Fix Non-Atomic `startPoSt()` Guard in `PoStDaemonService.kt`**:
   - Add `private val isStarting = AtomicBoolean(false)`.
   - In `startPoSt(...)`, use `if (!isStarting.compareAndSet(false, true)) return`. In `finally` block or when state becomes terminal/idle, reset `isStarting.set(false)`.
2. **Fix `cancelPoSt()` Allocation Window Race in `PoStDaemonService.kt`**:
   - Maintain `private val isCancelled = AtomicBoolean(false)`.
   - In `cancelPoSt()`, set `isCancelled.set(true)`. If `currentHandle != 0L`, invoke `PoStNativeBridge.cancelPoSt(handle)` and `PoStNativeBridge.releaseMemory(handle)`.
   - In `startPoSt()` background job, check `if (isCancelled.get())` immediately after `allocateMemory` returns. If true, call `releaseMemory` immediately, set state to `CANCELLED`, and return without proceeding to `computePoSt`.
3. **Fix UI Subscriber Rebind Leak in `MainActivity.kt`**:
   - Maintain `private var observationJob: Job? = null` in `MainActivity`.
   - Before launching a new `lifecycleScope.launch` collecting `daemonService.stateFlow`, call `observationJob?.cancel()`. Assign the new job to `observationJob`.

Verify changes, document in `changes.md`, write `handoff.md`, and send a message to orchestrator when finished.
