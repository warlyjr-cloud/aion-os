package com.aionos.edgenode.jni

import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Empirical Kotlin Stress Test demonstrating JNI handle lifecycle flaws,
 * concurrent execution races, cancellation flag overrides, and double releases.
 * Author: Challenger M1_2
 */
class PoStJniStressTest {

    private val bridge = PoStNativeBridge()

    fun runAllStressTests() {
        println("=== Running Kotlin JNI Bridge Stress Tests ===")
        testConcurrentReleaseAndCompute()
        testCancellationOverride()
        testDoubleRelease()
    }

    /**
     * STRESS TEST 1: Concurrent release while compute is running.
     * Demonstrates Use-After-Free crash.
     */
    fun testConcurrentReleaseAndCompute() {
        println("[STRESS 1] Testing Concurrent releaseMemory during computePoSt...")
        val handle = bridge.allocateMemory(16) // 16 MB
        val seed = ByteArray(32) { 0x01 }
        val executor = Executors.newFixedThreadPool(2)
        val started = AtomicBoolean(false)

        executor.submit {
            try {
                started.set(true)
                // Long-running compute
                bridge.computePoSt(handle, seed, 1000000)
            } catch (e: Throwable) {
                println(" -> Compute thread threw exception/crashed: ${e.message}")
            }
        }

        executor.submit {
            while (!started.get()) {
                Thread.sleep(1)
            }
            Thread.sleep(10)
            println(" -> Calling releaseMemory($handle) on background thread while compute is active...")
            bridge.releaseMemory(handle)
        }

        executor.shutdown()
        executor.awaitTermination(5, TimeUnit.SECONDS)
        println(" -> [FINDING]: Native code has no lock or synchronization preventing release of actively computing memory handles!")
    }

    /**
     * STRESS TEST 2: Cancellation flag race condition / flag overwrite.
     */
    fun testCancellationOverride() {
        println("[STRESS 2] Testing cancellation flag override...")
        val handle = bridge.allocateMemory(4)
        val seed = ByteArray(32) { 0x02 }

        // Cancel before starting compute
        bridge.cancelPoSt(handle)

        // Start compute
        val result = bridge.computePoSt(handle, seed, 1000)
        if (result.statusCode == PoSTResult.STATUS_SUCCESS) {
            println(" -> [FAIL]: Pre-set cancellation flag was OVERWRITTEN! Status = SUCCESS (0) instead of CANCELLED (2).")
        } else {
            println(" -> [PASS]: Computation cancelled successfully.")
        }
        bridge.releaseMemory(handle)
    }

    /**
     * STRESS TEST 3: Double release on same handle.
     */
    fun testDoubleRelease() {
        println("[STRESS 3] Testing double release behavior...")
        val handle = bridge.allocateMemory(1)
        bridge.releaseMemory(handle)
        println(" -> First release complete.")

        // Second release with same handle primitive
        println(" -> Second release called with handle $handle...")
        try {
            bridge.releaseMemory(handle)
            println(" -> Second release returned without error (unsafe if address was reallocated!).")
        } catch (e: Throwable) {
            println(" -> Exception on second release: ${e.message}")
        }
    }
}
