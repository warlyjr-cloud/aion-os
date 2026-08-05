package com.aionos.edgenode.model

/**
 * 7-State status lifecycle representation of the PoST Hardware Engine.
 */
enum class PoStStatus {
    IDLE,
    ALLOCATING_MEMORY,
    PROVING,
    PAUSED,
    CANCELLED,
    COMPLETED,
    FAILED
}

/**
 * Immutable state snapshot holding node metrics, memory allocation status,
 * hash rate, elapsed time, and generated proof details.
 */
data class PoStState(
    val status: PoStStatus = PoStStatus.IDLE,
    val allocatedMemoryMb: Int = 0,
    val allocatedRamBytes: Long = 0L,
    val availableSystemMemoryMb: Int = 0,
    val currentHashRate: Double = 0.0,
    val completedHashes: Long = 0L,
    val targetHashes: Long = 0L,
    val progressPercent: Float = 0f,
    val elapsedTimeMs: Long = 0L,
    val proofDigest: ByteArray? = null,
    val proofHashHex: String? = null,
    val errorMessage: String? = null
) {
    /**
     * Returns true if computation is actively executing or allocating memory.
     */
    val isRunning: Boolean
        get() = status == PoStStatus.ALLOCATING_MEMORY || status == PoStStatus.PROVING

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as PoStState

        if (status != other.status) return false
        if (allocatedMemoryMb != other.allocatedMemoryMb) return false
        if (allocatedRamBytes != other.allocatedRamBytes) return false
        if (availableSystemMemoryMb != other.availableSystemMemoryMb) return false
        if (currentHashRate != other.currentHashRate) return false
        if (completedHashes != other.completedHashes) return false
        if (targetHashes != other.targetHashes) return false
        if (progressPercent != other.progressPercent) return false
        if (elapsedTimeMs != other.elapsedTimeMs) return false
        if (proofDigest != null) {
            if (other.proofDigest == null) return false
            if (!proofDigest.contentEquals(other.proofDigest)) return false
        } else if (other.proofDigest != null) return false
        if (proofHashHex != other.proofHashHex) return false
        if (errorMessage != other.errorMessage) return false

        return true
    }

    override fun hashCode(): Int {
        var result = status.hashCode()
        result = 31 * result + allocatedMemoryMb
        result = 31 * result + allocatedRamBytes.hashCode()
        result = 31 * result + availableSystemMemoryMb
        result = 31 * result + currentHashRate.hashCode()
        result = 31 * result + completedHashes.hashCode()
        result = 31 * result + targetHashes.hashCode()
        result = 31 * result + progressPercent.hashCode()
        result = 31 * result + elapsedTimeMs.hashCode()
        result = 31 * result + (proofDigest?.contentHashCode() ?: 0)
        result = 31 * result + (proofHashHex?.hashCode() ?: 0)
        result = 31 * result + (errorMessage?.hashCode() ?: 0)
        return result
    }
}
