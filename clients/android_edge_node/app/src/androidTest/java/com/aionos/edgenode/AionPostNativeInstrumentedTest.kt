package com.aionos.edgenode

import androidx.test.ext.junit.runners.AndroidJUnit4
import com.aionos.edgenode.jni.PoSTResult
import com.aionos.edgenode.jni.PoStNativeBridge
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference

/**
 * Android Instrumented Test Suite for AION OS Native PoST Engine via JNI.
 * Executes native C++ PoST Bare-Metal Engine functions on device/emulator.
 */
@RunWith(AndroidJUnit4::class)
class AionPostNativeInstrumentedTest {

    private lateinit var bridge: PoStNativeBridge

    @Before
    fun setUp() {
        bridge = PoStNativeBridge()
    }

    /**
     * Test 1: Native JNI Library Load & Handle Allocation
     * Verifies that libaion_post.so loads properly and allocateMemory(16)
     * returns a valid non-zero pointer handle.
     */
    @Test
    fun testNativeJniLibraryLoadAndHandleAllocation() {
        val sizeMb = 16
        val handle = bridge.allocateMemory(sizeMb)

        assertNotEquals("Native handle must be non-zero after memory allocation", 0L, handle)
        assertTrue("Native handle must be positive pointer value", handle > 0L)

        // Clean up
        bridge.releaseMemory(handle)
    }

    /**
     * Test 2: Native PoST Execution
     * Computes PoST over 16MB memory and attests status 0, non-null 32-byte digest,
     * 64-char hex, execution time, and allocated RAM == 16MB.
     */
    @Test
    fun testNativePoStExecution() {
        val sizeMb = 16
        val handle = bridge.allocateMemory(sizeMb)
        assertNotEquals(0L, handle)

        try {
            val seed = ByteArray(32) { (it + 1).toByte() }
            val iterations = 10

            val result = bridge.computePoSt(handle, seed, iterations)

            assertNotNull("PoSTResult must not be null", result)
            assertEquals("Status code must be STATUS_SUCCESS (0)", PoSTResult.STATUS_SUCCESS, result.statusCode)
            assertTrue("isSuccess property must be true", result.isSuccess)

            assertNotNull("Proof digest must not be null", result.proofDigest)
            assertEquals("Proof digest must be exactly 32 bytes", 32, result.proofDigest.size)

            assertNotNull("Proof hex string must not be null", result.proofHex)
            assertEquals("Proof hex string must be 64 characters long", 64, result.proofHex.length)
            assertTrue(
                "Proof hex string must match 64-char lowercase hexadecimal regex",
                result.proofHex.matches(Regex("^[0-9a-f]{64}$"))
            )

            val expectedHex = byteArrayToHex(result.proofDigest)
            assertEquals(
                "Proof hex string must match hex representation of proof digest",
                expectedHex,
                result.proofHex
            )

            assertTrue("Execution time must be >= 0ms", result.executionTimeMs >= 0L)
            assertEquals(
                "Allocated RAM in bytes must equal 16 MB (16,777,216 bytes)",
                16L * 1024L * 1024L,
                result.allocatedRamBytes
            )
            assertEquals("Iterations completed must equal requested count", iterations, result.iterationsCompleted)
        } finally {
            bridge.releaseMemory(handle)
        }
    }

    /**
     * Test 3: Deterministic Hash Verification
     * Same seed + iterations produces identical proof hash digest;
     * different seed produces distinct proof hash digest.
     */
    @Test
    fun testDeterministicHashVerification() {
        val handle = bridge.allocateMemory(16)
        assertNotEquals(0L, handle)

        try {
            val seedA = ByteArray(32) { 0x42.toByte() }
            val seedB = ByteArray(32) { (it + 1).toByte() }
            val iterations = 15

            // Compute with Seed A - Pass 1
            val resultA1 = bridge.computePoSt(handle, seedA, iterations)
            assertEquals(PoSTResult.STATUS_SUCCESS, resultA1.statusCode)

            // Compute with Seed A - Pass 2
            val resultA2 = bridge.computePoSt(handle, seedA, iterations)
            assertEquals(PoSTResult.STATUS_SUCCESS, resultA2.statusCode)

            // Determinism check: Same seed must produce identical digest and hex
            assertArrayEquals(
                "Identical seed and iterations must yield identical 32-byte proof digest",
                resultA1.proofDigest,
                resultA2.proofDigest
            )
            assertEquals(
                "Identical seed and iterations must yield identical 64-char proof hex",
                resultA1.proofHex,
                resultA2.proofHex
            )

            // Compute with Seed B
            val resultB = bridge.computePoSt(handle, seedB, iterations)
            assertEquals(PoSTResult.STATUS_SUCCESS, resultB.statusCode)

            // Distinctness check: Different seed must produce distinct digest
            assertFalse(
                "Different seeds must yield distinct proof digests",
                resultA1.proofDigest.contentEquals(resultB.proofDigest)
            )
            assertNotEquals(
                "Different seeds must yield distinct proof hex strings",
                resultA1.proofHex,
                resultB.proofHex
            )
        } finally {
            bridge.releaseMemory(handle)
        }
    }

    /**
     * Test 4: Hardware Effort Attestation
     * Asserts execution time >= 0ms, correct iteration count, allocated memory size,
     * and non-trivial memory walk mutations.
     */
    @Test
    fun testHardwareEffortAttestation() {
        val handle = bridge.allocateMemory(16)
        assertNotEquals(0L, handle)

        try {
            val seed = ByteArray(32) { (it * 7).toByte() }
            val iterations = 100

            val result = bridge.computePoSt(handle, seed, iterations)

            assertEquals(PoSTResult.STATUS_SUCCESS, result.statusCode)
            assertEquals(100, result.iterationsCompleted)
            assertEquals(16L * 1024L * 1024L, result.allocatedRamBytes)
            assertTrue("Hardware effort execution duration must be >= 0ms", result.executionTimeMs >= 0L)

            // Verify non-trivial digest (not all 0x00 bytes)
            val allZeros = ByteArray(32) { 0 }
            assertFalse(
                "Proof digest after hardware memory walk must not be all zeros",
                result.proofDigest.contentEquals(allZeros)
            )
        } finally {
            bridge.releaseMemory(handle)
        }
    }

    /**
     * Test 5: Atomic Cancellation & Thread Safety
     * Asynchronously triggers cancelPoSt on active handle during computation
     * and verifies returned status code is STATUS_CANCELLED (2).
     */
    @Test
    fun testAtomicCancellationAndThreadSafety() {
        val handle = bridge.allocateMemory(16)
        assertNotEquals(0L, handle)

        try {
            val seed = ByteArray(32) { 0xAA.toByte() }
            val iterations = 500000 // High iteration count to allow cancellation timing window

            val resultRef = AtomicReference<PoSTResult>()
            val latch = CountDownLatch(1)

            val workerThread = Thread {
                try {
                    val result = bridge.computePoSt(handle, seed, iterations)
                    resultRef.set(result)
                } catch (e: Exception) {
                    // Handle unexpected exceptions
                } finally {
                    latch.countDown()
                }
            }

            workerThread.start()

            // Brief sleep to allow worker thread to enter native compute loop
            Thread.sleep(10)

            // Trigger atomic cancellation
            bridge.cancelPoSt(handle)

            val completed = latch.await(5, TimeUnit.SECONDS)
            assertTrue("PoSt computation thread should terminate after cancellation signal", completed)

            val result = resultRef.get()
            assertNotNull("Computation result should be returned after cancellation", result)
            assertEquals(
                "Status code must be STATUS_CANCELLED (2)",
                PoSTResult.STATUS_CANCELLED,
                result.statusCode
            )
            assertFalse("isSuccess must be false when cancelled", result.isSuccess)
        } finally {
            bridge.releaseMemory(handle)
        }
    }

    /**
     * Test 6: Memory Release Cleanup
     * Verifies releaseMemory releases native context and subsequent operations
     * on the released handle throw IllegalStateException.
     */
    @Test
    fun testMemoryReleaseCleanup() {
        val handle = bridge.allocateMemory(16)
        assertNotEquals(0L, handle)

        // Release memory
        bridge.releaseMemory(handle)

        val seed = ByteArray(32) { 0x11.toByte() }

        // Subsequent compute call must throw IllegalStateException
        try {
            bridge.computePoSt(handle, seed, 10)
            fail("computePoSt on released handle must throw IllegalStateException")
        } catch (e: IllegalStateException) {
            assertTrue(e.message?.contains("released or invalid") == true)
        }

        // Subsequent cancel call must throw IllegalStateException
        try {
            bridge.cancelPoSt(handle)
            fail("cancelPoSt on released handle must throw IllegalStateException")
        } catch (e: IllegalStateException) {
            assertTrue(e.message?.contains("released or invalid") == true)
        }

        // Subsequent release call must throw IllegalStateException
        try {
            bridge.releaseMemory(handle)
            fail("releaseMemory on released handle must throw IllegalStateException")
        } catch (e: IllegalStateException) {
            assertTrue(e.message?.contains("released or invalid") == true)
        }
    }

    /**
     * Edge Case Test: Invalid Input Parameters
     */
    @Test
    fun testInvalidInputParameterValidations() {
        // Memory allocation size out of bounds (1..256 MB)
        try {
            bridge.allocateMemory(0)
            fail("allocateMemory(0) must throw IllegalArgumentException")
        } catch (e: IllegalArgumentException) {
            // expected
        }

        try {
            bridge.allocateMemory(300)
            fail("allocateMemory(300) must throw IllegalArgumentException")
        } catch (e: IllegalArgumentException) {
            // expected
        }

        val handle = bridge.allocateMemory(16)
        try {
            // Invalid seed length (must be 32 bytes)
            try {
                bridge.computePoSt(handle, ByteArray(16), 10)
                fail("computePoSt with 16-byte seed must throw IllegalArgumentException")
            } catch (e: IllegalArgumentException) {
                // expected
            }

            // Invalid iteration count (must be > 0)
            try {
                bridge.computePoSt(handle, ByteArray(32), 0)
                fail("computePoSt with 0 iterations must throw IllegalArgumentException")
            } catch (e: IllegalArgumentException) {
                // expected
            }
        } finally {
            bridge.releaseMemory(handle)
        }
    }

    private fun byteArrayToHex(bytes: ByteArray): String {
        val hexDigits = "0123456789abcdef"
        val result = StringBuilder(bytes.size * 2)
        for (b in bytes) {
            val i = b.toInt() and 0xFF
            result.append(hexDigits[i ushr 4])
            result.append(hexDigits[i and 0x0F])
        }
        return result.toString()
    }
}
