package com.aionos.edgenode.jni

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.locks.ReentrantReadWriteLock

/**
 * JNI Native Bridge exposing C++ PoST Bare-Metal Engine (`libaion_post.so`) to Android JVM.
 */
class PoStNativeBridge {

    companion object {
        init {
            System.loadLibrary("aion_post")
        }
        private val activeHandles = ConcurrentHashMap.newKeySet<Long>()
        private val handleLocks = ConcurrentHashMap<Long, ReentrantReadWriteLock>()
    }

    /**
     * Native C++ method signatures matching C++ JNI exports in jni_bridge.cpp.
     */
    private external fun nativeAllocateMemory(sizeMb: Int): Long

    private external fun nativeComputePoSt(
        handle: Long,
        seed: ByteArray,
        iterations: Int
    ): PoSTResult?

    private external fun nativeReleaseMemory(handle: Long)

    private external fun nativeCancelPoSt(handle: Long)

    private external fun nativePausePoSt(handle: Long)

    private external fun nativeResumePoSt(handle: Long)

    private external fun nativeGetProgress(handle: Long): Int

    /**
     * Allocates native physical RAM (in Megabytes) for Space-Time commitment.
     * @param sizeMb Size in Megabytes (1 to 256 MB).
     * @return Handle pointer (`Long`) referencing the native C++ PoSTContext.
     */
    fun allocateMemory(sizeMb: Int): Long {
        require(sizeMb in 1..256) { "Memory size must be between 1 MB and 256 MB." }
        val handle = nativeAllocateMemory(sizeMb)
        if (handle != 0L) {
            activeHandles.add(handle)
            handleLocks[handle] = ReentrantReadWriteLock()
        }
        return handle
    }

    /**
     * Computes Proof-of-Space-Time over allocated memory buffer.
     * @param handle 64-bit handle returned by [allocateMemory].
     * @param seed 32-byte challenge seed byte array.
     * @param iterations Target time-dilation iteration rounds.
     * @return [PoSTResult] containing final proof digest and execution statistics.
     */
    fun computePoSt(handle: Long, seed: ByteArray, iterations: Int): PoSTResult {
        if (handle == 0L) {
            throw IllegalStateException("Handle released or invalid")
        }
        val lock = handleLocks[handle] ?: throw IllegalStateException("Handle released or invalid")
        lock.readLock().lock()
        try {
            if (!activeHandles.contains(handle)) {
                throw IllegalStateException("Handle released or invalid")
            }
            require(seed.size == 32) { "Seed byte array must be exactly 32 bytes." }
            require(iterations > 0) { "Iteration count must be greater than zero." }

            return nativeComputePoSt(handle, seed, iterations)
                ?: throw IllegalStateException("Native computation failed to return a valid PoSTResult object.")
        } finally {
            lock.readLock().unlock()
        }
    }

    /**
     * Releases physical RAM allocated to native handle safely.
     * @param handle 64-bit handle pointer returned by [allocateMemory].
     */
    fun releaseMemory(handle: Long) {
        if (handle == 0L) {
            throw IllegalStateException("Handle released or invalid")
        }
        val lock = handleLocks.remove(handle) ?: throw IllegalStateException("Handle released or invalid")
        lock.writeLock().lock()
        try {
            activeHandles.remove(handle)
            nativeReleaseMemory(handle)
        } finally {
            lock.writeLock().unlock()
        }
    }

    /**
     * Signals native computation loop on the specified handle to cancel gracefully.
     * @param handle 64-bit handle pointer returned by [allocateMemory].
     */
    fun cancelPoSt(handle: Long) {
        if (handle == 0L) {
            throw IllegalStateException("Handle released or invalid")
        }
        val lock = handleLocks[handle] ?: throw IllegalStateException("Handle released or invalid")
        lock.readLock().lock()
        try {
            if (!activeHandles.contains(handle)) {
                throw IllegalStateException("Handle released or invalid")
            }
            nativeCancelPoSt(handle)
        } finally {
            lock.readLock().unlock()
        }
    }

    /**
     * Pauses ongoing PoST computation.
     */
    fun pausePoSt(handle: Long) {
        if (handle == 0L) return
        val lock = handleLocks[handle] ?: return
        lock.readLock().lock()
        try {
            if (!activeHandles.contains(handle)) return
            nativePausePoSt(handle)
        } finally {
            lock.readLock().unlock()
        }
    }

    /**
     * Resumes paused PoST computation.
     */
    fun resumePoSt(handle: Long) {
        if (handle == 0L) return
        val lock = handleLocks[handle] ?: return
        lock.readLock().lock()
        try {
            if (!activeHandles.contains(handle)) return
            nativeResumePoSt(handle)
        } finally {
            lock.readLock().unlock()
        }
    }

    /**
     * Polls current iteration progress from native context.
     */
    fun getProgress(handle: Long): Int {
        if (handle == 0L) return 0
        val lock = handleLocks[handle] ?: return 0
        lock.readLock().lock()
        try {
            if (!activeHandles.contains(handle)) return 0
            return nativeGetProgress(handle)
        } finally {
            lock.readLock().unlock()
        }
    }
}

