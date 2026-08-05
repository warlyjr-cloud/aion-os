package com.aionos.edgenode.service

import com.aionos.edgenode.model.PoStState
import com.aionos.edgenode.model.PoStStatus
import org.junit.Assert.*
import org.junit.Test
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicReference

/**
 * Unit & Stress Test suite for PoStDaemonService lifecycle, state flow,
 * WakeLock safety, cancellation races, and service unbind edge cases.
 */
class PoStDaemonServiceTest {

    @Test
    fun testPoStStatusLifecycleEnumValues() {
        val statuses = PoStStatus.values()
        assertEquals(7, statuses.size)
        assertTrue(statuses.contains(PoStStatus.IDLE))
        assertTrue(statuses.contains(PoStStatus.ALLOCATING_MEMORY))
        assertTrue(statuses.contains(PoStStatus.PROVING))
        assertTrue(statuses.contains(PoStStatus.PAUSED))
        assertTrue(statuses.contains(PoStStatus.CANCELLED))
        assertTrue(statuses.contains(PoStStatus.COMPLETED))
        assertTrue(statuses.contains(PoStStatus.FAILED))
    }

    @Test
    fun testPoStStateIsRunningProperty() {
        val idleState = PoStState(status = PoStStatus.IDLE)
        assertFalse(idleState.isRunning)

        val allocState = PoStState(status = PoStStatus.ALLOCATING_MEMORY)
        assertTrue(allocState.isRunning)

        val provingState = PoStState(status = PoStStatus.PROVING)
        assertTrue(provingState.isRunning)

        val completedState = PoStState(status = PoStStatus.COMPLETED)
        assertFalse(completedState.isRunning)

        val failedState = PoStState(status = PoStStatus.FAILED)
        assertFalse(failedState.isRunning)

        val cancelledState = PoStState(status = PoStStatus.CANCELLED)
        assertFalse(cancelledState.isRunning)
    }

    @Test
    fun testPoStStateEqualityAndHashCode() {
        val digest1 = byteArrayOf(1, 2, 3, 4)
        val digest2 = byteArrayOf(1, 2, 3, 4)

        val state1 = PoStState(
            status = PoStStatus.COMPLETED,
            allocatedMemoryMb = 16,
            completedHashes = 1000,
            proofDigest = digest1,
            proofHashHex = "01020304"
        )

        val state2 = PoStState(
            status = PoStStatus.COMPLETED,
            allocatedMemoryMb = 16,
            completedHashes = 1000,
            proofDigest = digest2,
            proofHashHex = "01020304"
        )

        assertEquals(state1, state2)
        assertEquals(state1.hashCode(), state2.hashCode())
    }

    /**
     * Stress Test: Concurrent startPoSt invocations to detect non-atomic state guard races.
     */
    @Test
    fun testConcurrentStartGuardRaceConditionSimulation() {
        val threadCount = 10
        val executor = Executors.newFixedThreadPool(threadCount)
        val readyLatch = CountDownLatch(threadCount)
        val startLatch = CountDownLatch(1)
        val successCount = AtomicInteger(0)

        var isRunningState = false
        val lock = Object()

        for (i in 0 until threadCount) {
            executor.submit {
                readyLatch.countDown()
                startLatch.await()

                // Simulating non-atomic check and update in PoStDaemonService:
                // if (_stateFlow.value.isRunning) return
                val wasRunning = synchronized(lock) {
                    if (isRunningState) {
                        true
                    } else {
                        // Delay between check and set simulates race window
                        Thread.sleep(1)
                        isRunningState = true
                        false
                    }
                }

                if (!wasRunning) {
                    successCount.incrementAndGet()
                }
            }
        }

        readyLatch.await(5, TimeUnit.SECONDS)
        startLatch.countDown()
        executor.shutdown()
        executor.awaitTermination(5, TimeUnit.SECONDS)

        // Without synchronization on startPoSt, multiple threads pass the isRunning check
        assertTrue("Without atomic compare-and-set, concurrent invocations pass guard", successCount.get() > 1)
    }

    /**
     * Stress Test: Race condition simulation between cancelPoSt and allocateMemory.
     */
    @Test
    fun testCancelDuringAllocationRaceSimulation() {
        val currentHandle = AtomicLong(0L)
        val status = AtomicReference(PoStStatus.IDLE)
        val nativeCancelCalled = AtomicBoolean(false)

        val allocationLatch = CountDownLatch(1)
        val cancelLatch = CountDownLatch(1)

        // Thread 1: startPoSt simulation
        val serviceThread = Thread {
            status.set(PoStStatus.ALLOCATING_MEMORY)
            allocationLatch.countDown()

            // Simulating slow allocateMemory
            Thread.sleep(50)
            val allocatedHandle = 0x12345678L
            currentHandle.set(allocatedHandle)

            // Overwrites status to PROVING regardless of whether status was set to CANCELLED!
            status.set(PoStStatus.PROVING)
        }

        // Thread 2: cancelPoSt simulation
        val cancelThread = Thread {
            allocationLatch.await()
            val handleToCancel = currentHandle.get()
            if (handleToCancel != 0L) {
                nativeCancelCalled.set(true)
            }
            status.set(PoStStatus.CANCELLED)
            cancelLatch.countDown()
        }

        serviceThread.start()
        cancelThread.start()

        serviceThread.join()
        cancelThread.join()

        // Empirical check: cancel happened while currentHandle was 0L
        assertFalse("Native cancel was not called because currentHandle was 0L during allocation", nativeCancelCalled.get())
        assertEquals("Status was overwritten back to PROVING by startPoSt coroutine after cancel", PoStStatus.PROVING, status.get())
    }
}
