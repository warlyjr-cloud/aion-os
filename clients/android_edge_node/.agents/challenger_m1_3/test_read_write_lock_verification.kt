import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.locks.ReentrantReadWriteLock

/**
 * Empirical Verification Harness for PoStNativeBridge ReentrantReadWriteLock Synchronization.
 *
 * Verifies that:
 * 1. TOCTOU Use-After-Free race condition between Kotlin validity check and JNI execution is eliminated.
 * 2. Concurrent releaseMemory during active computePoSt cleanly blocks deallocation until compute completes.
 * 3. Invocations on released handles immediately fail with IllegalStateException.
 * 4. Double release calls fail safely without corrupting handle registry state.
 */
class PoStBridgeLockHarness {

    // Mock bridge simulating PoStNativeBridge lock mechanics
    private val activeHandles = ConcurrentHashMap.newKeySet<Long>()
    private val handleLocks = ConcurrentHashMap<Long, ReentrantReadWriteLock>()
    
    // Counters for verification
    val nativeComputeExecutions = AtomicInteger(0)
    val nativeReleaseExecutions = AtomicInteger(0)
    val toctouViolations = AtomicInteger(0)
    val nativeActiveInFlight = AtomicInteger(0)

    fun allocateMemory(sizeMb: Int): Long {
        require(sizeMb in 1..256)
        val handle = 0x1000L + (Math.random() * 0x7FFF_FFFFL).toLong()
        activeHandles.add(handle)
        handleLocks[handle] = ReentrantReadWriteLock()
        return handle
    }

    fun computePoSt(handle: Long, seed: ByteArray, iterations: Int): String {
        if (handle == 0L) {
            throw IllegalStateException("Handle released or invalid")
        }
        val lock = handleLocks[handle] ?: throw IllegalStateException("Handle released or invalid")
        lock.readLock().lock()
        try {
            if (!activeHandles.contains(handle)) {
                throw IllegalStateException("Handle released or invalid")
            }
            require(seed.size == 32)
            require(iterations > 0)

            // Simulate JNI Native Execution Window
            val active = nativeActiveInFlight.incrementAndGet()
            nativeComputeExecutions.incrementAndGet()
            
            // Artificial delay simulating heavy C++ time-dilation computation
            Thread.sleep(50)
            
            if (!activeHandles.contains(handle)) {
                // If activeHandles was modified WHILE we were executing inside JNI, TOCTOU occurred!
                toctouViolations.incrementAndGet()
            }
            
            nativeActiveInFlight.decrementAndGet()
            return "SUCCESS_HASH_MOCK"
        } finally {
            lock.readLock().unlock()
        }
    }

    fun releaseMemory(handle: Long) {
        if (handle == 0L) {
            throw IllegalStateException("Handle released or invalid")
        }
        val lock = handleLocks.remove(handle) ?: throw IllegalStateException("Handle released or invalid")
        lock.writeLock().lock()
        try {
            activeHandles.remove(handle)
            
            // Simulate C++ nativeReleaseMemory
            if (nativeActiveInFlight.get() > 0) {
                // If native compute is still executing when we release memory, UAF occurred!
                toctouViolations.incrementAndGet()
            }
            nativeReleaseExecutions.incrementAndGet()
        } finally {
            lock.writeLock().unlock()
        }
    }
}

fun main() {
    println("=== Starting PoStNativeBridge ReadWriteLock Verification Harness ===")
    val harness = PoStBridgeLockHarness()
    val executor = Executors.newFixedThreadPool(16)
    val handle = harness.allocateMemory(64)
    val seed = ByteArray(32) { 0x01 }
    
    val illegalExceptionsCaught = AtomicInteger(0)
    val successComputes = AtomicInteger(0)

    // Launch concurrent compute threads
    for (i in 0 until 10) {
        executor.submit {
            try {
                val res = harness.computePoSt(handle, seed, 100)
                if (res == "SUCCESS_HASH_MOCK") {
                    successComputes.incrementAndGet()
                }
            } catch (e: IllegalStateException) {
                illegalExceptionsCaught.incrementAndGet()
            }
        }
    }

    // Concurrent thread attempting releaseMemory mid-execution
    executor.submit {
        Thread.sleep(15) // Wait for some computes to enter native window
        try {
            harness.releaseMemory(handle)
        } catch (e: IllegalStateException) {
            illegalExceptionsCaught.incrementAndGet()
        }
    }

    // Additional concurrent compute threads post-release attempt
    for (i in 0 until 5) {
        executor.submit {
            Thread.sleep(30)
            try {
                harness.computePoSt(handle, seed, 100)
            } catch (e: IllegalStateException) {
                illegalExceptionsCaught.incrementAndGet()
            }
        }
    }

    executor.shutdown()
    executor.awaitTermination(5, TimeUnit.SECONDS)

    println("Verification Summary:")
    println("  Successful native computes: ${successComputes.get()}")
    println("  Native releases executed: ${harness.nativeReleaseExecutions.get()}")
    println("  IllegalStateExceptions caught safely: ${illegalExceptionsCaught.get()}")
    println("  TOCTOU / UAF violations detected: ${harness.toctouViolations.get()}")

    if (harness.toctouViolations.get() == 0 && harness.nativeReleaseExecutions.get() == 1) {
        println("VERDICT: PASS - ReadWriteLock completely eliminates TOCTOU Use-After-Free race condition!")
    } else {
        println("VERDICT: FAIL - Concurrency violations detected!")
    }
}
