// Test Harness: Demonstrating Kotlin PoStNativeBridge TOCTOU Race Condition
// File: .agents/challenger_m1_2_fix/test_kotlin_race.kt

package com.aionos.edgenode.jni

import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

/**
 * Conceptual simulation of current PoStNativeBridge implementation to demonstrate TOCTOU race condition.
 */
class PoStNativeBridgeSim {
    companion object {
        val activeHandles = ConcurrentHashMap.newKeySet<Long>()
    }

    private val validMemory = ConcurrentHashMap<Long, Boolean>()

    fun allocateMemory(sizeMb: Int): Long {
        val handle = System.identityHashCode(Any()).toLong() or 0x100000000L
        validMemory[handle] = true
        activeHandles.add(handle)
        return handle
    }

    fun computePoSt(handle: Long, seed: ByteArray, iterations: Int): String {
        // Step 1: Check activeHandles
        if (handle == 0L || !activeHandles.contains(handle)) {
            throw IllegalStateException("Handle released or invalid")
        }

        // SIMULATE CONTEXT SWITCH / GC PAUSE / JNI TRANSITION HERE
        Thread.sleep(1)

        // Step 2: Simulated JNI nativeComputePoSt call accessing C++ memory
        val isStillValid = validMemory[handle] ?: false
        if (!isStillValid) {
            // IN REAL C++, THIS IS A SIGSEGV / USE-AFTER-FREE CRASH!
            throw RuntimeException("CRASH: Use-After-Free in JNI nativeComputePoSt! Memory was deleted for handle $handle!")
        }
        return "SUCCESS"
    }

    fun releaseMemory(handle: Long) {
        if (handle == 0L || !activeHandles.remove(handle)) {
            throw IllegalStateException("Handle released or invalid")
        }
        // Native C++ release_post_context deletes memory
        validMemory.remove(handle)
    }
}

fun main() {
    println("[STRESS TEST] Simulating PoStNativeBridge concurrent computePoSt vs releaseMemory...")
    val bridge = PoStNativeBridgeSim()
    var uafCount = 0

    for (i in 1..100) {
        val handle = bridge.allocateMemory(16)
        val seed = ByteArray(32)

        var exceptionThrown: Exception? = null

        val t1 = thread {
            try {
                bridge.computePoSt(handle, seed, 100)
            } catch (e: Exception) {
                exceptionThrown = e
            }
        }

        val t2 = thread {
            Thread.sleep(0, 500000) // 0.5 ms
            try {
                bridge.releaseMemory(handle)
            } catch (e: Exception) {
                // Already released or invalid
            }
        }

        t1.join()
        t2.join()

        if (exceptionThrown?.message?.contains("Use-After-Free") == true) {
            uafCount++
            println("Iteration $i: REPRODUCED USE-AFTER-FREE! -> ${exceptionThrown?.message}")
        }
    }

    println("[RESULT] Total Use-After-Free race conditions caught: $uafCount")
}
