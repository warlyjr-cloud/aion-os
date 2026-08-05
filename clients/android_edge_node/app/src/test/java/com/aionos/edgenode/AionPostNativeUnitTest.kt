package com.aionos.edgenode

import com.aionos.edgenode.jni.PoSTResult
import com.aionos.edgenode.jni.PoStNativeBridge
import org.junit.Assert.*
import org.junit.Test

/**
 * JVM Unit Test Suite for PoST Native JNI Bridge and PoSTResult state machine.
 * Verifies parameter validation, data model contracts, status code representations,
 * and error handling on the JVM side.
 */
class AionPostNativeUnitTest {

    @Test
    fun testPoSTResultStatusCodeConstants() {
        assertEquals(0, PoSTResult.STATUS_SUCCESS)
        assertEquals(1, PoSTResult.STATUS_OOM)
        assertEquals(2, PoSTResult.STATUS_CANCELLED)
        assertEquals(3, PoSTResult.STATUS_INVALID_PARAM)
    }

    @Test
    fun testPoSTResultIsSuccessProperty() {
        val successResult = PoSTResult(
            proofDigest = ByteArray(32) { 1 },
            proofHex = "01".repeat(32),
            executionTimeMs = 120L,
            allocatedRamBytes = 16L * 1024L * 1024L,
            iterationsCompleted = 1000,
            statusCode = PoSTResult.STATUS_SUCCESS
        )
        assertTrue(successResult.isSuccess)

        val oomResult = successResult.copy(statusCode = PoSTResult.STATUS_OOM)
        assertFalse(oomResult.isSuccess)

        val cancelledResult = successResult.copy(statusCode = PoSTResult.STATUS_CANCELLED)
        assertFalse(cancelledResult.isSuccess)

        val invalidParamResult = successResult.copy(statusCode = PoSTResult.STATUS_INVALID_PARAM)
        assertFalse(invalidParamResult.isSuccess)
    }

    @Test
    fun testPoSTResultEqualityAndHashCode() {
        val digest1 = byteArrayOf(10, 20, 30, 40)
        val digest2 = byteArrayOf(10, 20, 30, 40)
        val digest3 = byteArrayOf(10, 20, 30, 99)

        val result1 = PoSTResult(
            proofDigest = digest1,
            proofHex = "0a141e28",
            executionTimeMs = 50L,
            allocatedRamBytes = 1024L,
            iterationsCompleted = 10,
            statusCode = PoSTResult.STATUS_SUCCESS
        )

        val result2 = PoSTResult(
            proofDigest = digest2,
            proofHex = "0a141e28",
            executionTimeMs = 50L,
            allocatedRamBytes = 1024L,
            iterationsCompleted = 10,
            statusCode = PoSTResult.STATUS_SUCCESS
        )

        val result3 = PoSTResult(
            proofDigest = digest3,
            proofHex = "0a141e63",
            executionTimeMs = 50L,
            allocatedRamBytes = 1024L,
            iterationsCompleted = 10,
            statusCode = PoSTResult.STATUS_SUCCESS
        )

        assertEquals(result1, result2)
        assertEquals(result1.hashCode(), result2.hashCode())

        assertNotEquals(result1, result3)
    }

    @Test
    fun testAllocateMemoryParameterBoundsValidation() {
        val bridge = try {
            PoStNativeBridge()
        } catch (e: UnsatisfiedLinkError) {
            // Expected on pure host JVM if native lib is not loaded
            return
        }

        // Test memory size 0 MB throws IllegalArgumentException
        try {
            bridge.allocateMemory(0)
            fail("allocateMemory(0) must throw IllegalArgumentException")
        } catch (e: IllegalArgumentException) {
            assertEquals("Memory size must be between 1 MB and 256 MB.", e.message)
        }

        // Test negative memory size throws IllegalArgumentException
        try {
            bridge.allocateMemory(-5)
            fail("allocateMemory(-5) must throw IllegalArgumentException")
        } catch (e: IllegalArgumentException) {
            assertEquals("Memory size must be between 1 MB and 256 MB.", e.message)
        }

        // Test memory size > 256 MB throws IllegalArgumentException
        try {
            bridge.allocateMemory(257)
            fail("allocateMemory(257) must throw IllegalArgumentException")
        } catch (e: IllegalArgumentException) {
            assertEquals("Memory size must be between 1 MB and 256 MB.", e.message)
        }
    }

    @Test
    fun testZeroHandleValidation() {
        val bridge = try {
            PoStNativeBridge()
        } catch (e: UnsatisfiedLinkError) {
            return
        }

        val zeroHandle = 0L
        val validSeed = ByteArray(32)

        // computePoSt with handle 0L must throw IllegalStateException
        try {
            bridge.computePoSt(zeroHandle, validSeed, 100)
            fail("computePoSt with zero handle must throw IllegalStateException")
        } catch (e: IllegalStateException) {
            assertEquals("Handle released or invalid", e.message)
        }

        // releaseMemory with handle 0L must throw IllegalStateException
        try {
            bridge.releaseMemory(zeroHandle)
            fail("releaseMemory with zero handle must throw IllegalStateException")
        } catch (e: IllegalStateException) {
            assertEquals("Handle released or invalid", e.message)
        }

        // cancelPoSt with handle 0L must throw IllegalStateException
        try {
            bridge.cancelPoSt(zeroHandle)
            fail("cancelPoSt with zero handle must throw IllegalStateException")
        } catch (e: IllegalStateException) {
            assertEquals("Handle released or invalid", e.message)
        }
    }
}
