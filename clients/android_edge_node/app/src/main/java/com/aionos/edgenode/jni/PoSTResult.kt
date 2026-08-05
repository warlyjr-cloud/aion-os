package com.aionos.edgenode.jni

/**
 * Immutable data result returned from C++ Proof-of-Space-Time engine via JNI.
 *
 * @property proofDigest 32-byte binary SHA-256 digest of the final PoST commitment.
 * @property proofHex 64-character lowercase hexadecimal string representation of proofDigest.
 * @property executionTimeMs Total high-resolution execution duration in milliseconds.
 * @property allocatedRamBytes Physical bytes allocated in C++ native memory.
 * @property iterationsCompleted Total memory-hard hashing rounds completed before return.
 * @property statusCode Execution status code (0 = SUCCESS, 1 = OOM, 2 = CANCELLED, 3 = INVALID_PARAM).
 */
data class PoSTResult(
    val proofDigest: ByteArray,
    val proofHex: String,
    val executionTimeMs: Long,
    val allocatedRamBytes: Long,
    val iterationsCompleted: Int,
    val statusCode: Int
) {
    companion object {
        const val STATUS_SUCCESS = 0
        const val STATUS_OOM = 1
        const val STATUS_CANCELLED = 2
        const val STATUS_INVALID_PARAM = 3
    }

    /**
     * Returns true if computation finished successfully without error or cancellation.
     */
    val isSuccess: Boolean get() = statusCode == STATUS_SUCCESS

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as PoSTResult

        if (!proofDigest.contentEquals(other.proofDigest)) return false
        if (proofHex != other.proofHex) return false
        if (executionTimeMs != other.executionTimeMs) return false
        if (allocatedRamBytes != other.allocatedRamBytes) return false
        if (iterationsCompleted != other.iterationsCompleted) return false
        if (statusCode != other.statusCode) return false

        return true
    }

    override fun hashCode(): Int {
        var result = proofDigest.contentHashCode()
        result = 31 * result + proofHex.hashCode()
        result = 31 * result + executionTimeMs.hashCode()
        result = 31 * result + allocatedRamBytes.hashCode()
        result = 31 * result + iterationsCompleted
        result = 31 * result + statusCode
        return result
    }
}
