# Changes Log — Worker M1_fix2

## Modified Files

### `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt`

#### Purpose
Eliminate TOCTOU (Time-of-Check to Time-of-Use) Use-After-Free race condition when `computePoSt` or `cancelPoSt` is called concurrently with `releaseMemory` across multiple threads.

#### Summary of Edits
1. **Import added**:
   `import java.util.concurrent.locks.ReentrantReadWriteLock`

2. **`companion object` update**:
   Added `private val handleLocks = ConcurrentHashMap<Long, ReentrantReadWriteLock>()` to map each allocated handle to its own `ReentrantReadWriteLock`.

3. **`allocateMemory(sizeMb)` update**:
   When `nativeAllocateMemory(sizeMb)` returns a non-zero handle `handle`, instantiate and store a new `ReentrantReadWriteLock()` into `handleLocks[handle]`.

4. **`computePoSt(handle, seed, iterations)` update**:
   - Check if `handle == 0L`.
   - Retrieve `lock = handleLocks[handle] ?: throw IllegalStateException("Handle released or invalid")`.
   - Acquire `lock.readLock().lock()`.
   - Inside `try { ... } finally { lock.readLock().unlock() }`:
     - Verify `if (!activeHandles.contains(handle)) throw IllegalStateException(...)`.
     - Validate arguments (`seed.size == 32`, `iterations > 0`).
     - Invoke `nativeComputePoSt(handle, seed, iterations)`.

5. **`cancelPoSt(handle)` update**:
   - Check if `handle == 0L`.
   - Retrieve `lock = handleLocks[handle] ?: throw IllegalStateException("Handle released or invalid")`.
   - Acquire `lock.readLock().lock()`.
   - Inside `try { ... } finally { lock.readLock().unlock() }`:
     - Verify `if (!activeHandles.contains(handle)) throw IllegalStateException(...)`.
     - Invoke `nativeCancelPoSt(handle)`.

6. **`releaseMemory(handle)` update**:
   - Check if `handle == 0L`.
   - Atomic remove: `lock = handleLocks.remove(handle) ?: throw IllegalStateException("Handle released or invalid")`.
   - Acquire `lock.writeLock().lock()`.
   - Inside `try { ... } finally { lock.writeLock().unlock() }`:
     - `activeHandles.remove(handle)`.
     - Invoke `nativeReleaseMemory(handle)`.

#### Rationale & Guarantees
- **Atomic Handle Lookup**: `handleLocks.remove(handle)` ensures that only a single thread can ever enter the `releaseMemory` critical section for a specific handle. Subsequent or duplicate calls (double-free) immediately fail with `IllegalStateException`.
- **Exclusive Deallocation**: `writeLock` blocks in `releaseMemory` until all active `computePoSt` or `cancelPoSt` operations holding a `readLock` for that handle have finished.
- **Immediate Rejection**: Any invocation of `computePoSt` or `cancelPoSt` initiated after `releaseMemory` starts (and removes the lock from `handleLocks`) will immediately throw `IllegalStateException` without executing any JNI calls.
- **TOCTOU Elimination**: The Kotlin validation check (`activeHandles.contains(handle)`) and the JNI native invocation (`nativeComputePoSt`/`nativeCancelPoSt`) now execute atomically under the protection of `readLock`, preventing native memory deallocation during native execution.
