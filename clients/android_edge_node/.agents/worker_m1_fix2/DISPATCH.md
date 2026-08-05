## 2026-08-05T13:37:26Z

You are Worker M1_fix2 (worker_m1_fix2) for Milestone 1 Iteration 3 of the AION OS Android Edge Node project.

Project Root: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node
Working Directory: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\worker_m1_fix2
Original Request Path: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\ORIGINAL_REQUEST.md
Project File: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\PROJECT.md
Challenger Handoff: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\challenger_m1_2_fix\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusive File Ownership:
You own editing of:
- `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt`

Task & Remediation Objective (Fix TOCTOU Race Condition):
Implement `ReentrantReadWriteLock` handle locking in `PoStNativeBridge.kt` to completely eliminate the TOCTOU window between Kotlin validity check and native JNI call:
1. In `companion object`, maintain `private val handleLocks = ConcurrentHashMap<Long, ReentrantReadWriteLock>()`.
2. In `allocateMemory(sizeMb)`:
   When native memory is allocated and `handle` is returned, create a `ReentrantReadWriteLock()` in `handleLocks[handle]`.
3. In `computePoSt(handle, seed, iterations)` and `cancelPoSt(handle)`:
   - Retrieve `lock = handleLocks[handle] ?: throw IllegalStateException("Handle released or invalid")`.
   - Acquire `lock.readLock().lock()`.
   - Inside `try { ... } finally { lock.readLock().unlock() }`:
     Verify `if (!activeHandles.contains(handle)) throw IllegalStateException(...)`.
     Execute native JNI call (`nativeComputePoSt` / `nativeCancelPoSt`).
4. In `releaseMemory(handle)`:
   - Retrieve and remove `lock = handleLocks.remove(handle) ?: throw IllegalStateException("Handle released or invalid")`.
   - Acquire `lock.writeLock().lock()`.
   - Inside `try { ... } finally { lock.writeLock().unlock() }`:
     `activeHandles.remove(handle)`
     Execute `nativeReleaseMemory(handle)`.

Verify changes, document in `changes.md`, write `handoff.md`, and send a message to orchestrator when finished.
