package com.aionos.edgenode.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import com.aionos.edgenode.R
import com.aionos.edgenode.jni.PoStNativeBridge
import com.aionos.edgenode.jni.PoSTResult
import com.aionos.edgenode.model.PoStState
import com.aionos.edgenode.model.PoStStatus
import com.aionos.edgenode.ui.MainActivity
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Android Foreground Service hosting native C++ PoST computation via Kotlin Coroutines.
 * Holds PARTIAL_WAKE_LOCK to preserve execution across screen timeouts and Doze mode.
 */
class PoStDaemonService : Service() {

    companion object {
        const val CHANNEL_ID = "aion_post_daemon"
        const val NOTIFICATION_ID = 1001
        private const val WAKE_LOCK_TAG = "AionEdgeNode::PoStDaemonWakeLock"
    }

    inner class LocalBinder : Binder() {
        fun getService(): PoStDaemonService = this@PoStDaemonService
    }

    private val binder = LocalBinder()
    private val nativeBridge = PoStNativeBridge()

    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)

    private val _stateFlow = MutableStateFlow(PoStState())
    val stateFlow: StateFlow<PoStState> = _stateFlow.asStateFlow()

    private var wakeLock: PowerManager.WakeLock? = null

    @Volatile
    private var currentHandle: Long = 0L

    private val isStarting = AtomicBoolean(false)
    private val isCancelled = AtomicBoolean(false)

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        acquireWakeLock()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = buildNotification(_stateFlow.value)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder {
        return binder
    }

    /**
     * Starts background PoST hardware computation using Kotlin Coroutines on Dispatchers.IO.
     */
    fun startPoSt(
        ramMb: Int = 16,
        iterations: Int = 1000,
        seed: ByteArray = ByteArray(32) { 0x42.toByte() }
    ) {
        if (_stateFlow.value.isRunning) return
        if (!isStarting.compareAndSet(false, true)) return

        isCancelled.set(false)

        acquireWakeLock()

        _stateFlow.value = PoStState(
            status = PoStStatus.ALLOCATING_MEMORY,
            allocatedMemoryMb = ramMb,
            targetHashes = iterations.toLong(),
            errorMessage = null
        )
        updateNotification()

        serviceScope.launch {
            try {
                val handle = nativeBridge.allocateMemory(ramMb)
                if (handle == 0L) {
                    _stateFlow.value = _stateFlow.value.copy(
                        status = PoStStatus.FAILED,
                        errorMessage = "Native RAM allocation failed (OOM)."
                    )
                    updateNotification()
                    return@launch
                }

                if (isCancelled.get()) {
                    try {
                        nativeBridge.releaseMemory(handle)
                    } catch (_: Exception) {}
                    _stateFlow.value = _stateFlow.value.copy(
                        status = PoStStatus.CANCELLED,
                        errorMessage = "Cancellation requested."
                    )
                    updateNotification()
                    return@launch
                }

                currentHandle = handle
                val allocatedBytes = ramMb.toLong() * 1024 * 1024

                _stateFlow.value = _stateFlow.value.copy(
                    status = PoStStatus.PROVING,
                    allocatedRamBytes = allocatedBytes,
                    errorMessage = null
                )
                updateNotification()

                val startTime = System.currentTimeMillis()
                val result = nativeBridge.computePoSt(handle, seed, iterations)
                val endTime = System.currentTimeMillis()

                val elapsedTime = (endTime - startTime).coerceAtLeast(1)
                val hashRate = (result.iterationsCompleted.toDouble() / (elapsedTime.toDouble() / 1000.0))

                when {
                    isCancelled.get() || result.statusCode == PoSTResult.STATUS_CANCELLED -> {
                        _stateFlow.value = _stateFlow.value.copy(
                            status = PoStStatus.CANCELLED,
                            completedHashes = result.iterationsCompleted.toLong(),
                            elapsedTimeMs = result.executionTimeMs,
                            errorMessage = "Computation cancelled by user."
                        )
                    }
                    result.statusCode == PoSTResult.STATUS_SUCCESS -> {
                        _stateFlow.value = _stateFlow.value.copy(
                            status = PoStStatus.COMPLETED,
                            completedHashes = result.iterationsCompleted.toLong(),
                            progressPercent = 100f,
                            elapsedTimeMs = result.executionTimeMs,
                            currentHashRate = hashRate,
                            proofDigest = result.proofDigest,
                            proofHashHex = result.proofHex,
                            errorMessage = null
                        )
                    }
                    else -> {
                        _stateFlow.value = _stateFlow.value.copy(
                            status = PoStStatus.FAILED,
                            completedHashes = result.iterationsCompleted.toLong(),
                            elapsedTimeMs = result.executionTimeMs,
                            errorMessage = "Native computation failed (code ${result.statusCode})."
                        )
                    }
                }
            } catch (e: Exception) {
                _stateFlow.value = _stateFlow.value.copy(
                    status = PoStStatus.FAILED,
                    errorMessage = e.message ?: "Unknown native error."
                )
            } finally {
                val handleToRelease = currentHandle
                if (handleToRelease != 0L) {
                    try {
                        nativeBridge.releaseMemory(handleToRelease)
                    } catch (_: Exception) {}
                    currentHandle = 0L
                }
                isStarting.set(false)
                releaseWakeLock()
                updateNotification()
            }
        }
    }

    /**
     * Cancels an ongoing PoST computation.
     */
    fun cancelPoSt() {
        isCancelled.set(true)
        val handle = currentHandle
        if (handle != 0L) {
            try {
                nativeBridge.cancelPoSt(handle)
                nativeBridge.releaseMemory(handle)
            } catch (_: Exception) {}
            currentHandle = 0L
        }
        _stateFlow.value = _stateFlow.value.copy(
            status = PoStStatus.CANCELLED,
            errorMessage = "Cancellation requested."
        )
        updateNotification()
    }

    fun getCurrentState(): PoStState = _stateFlow.value

    private fun acquireWakeLock() {
        if (wakeLock == null) {
            val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
            wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, WAKE_LOCK_TAG).apply {
                setReferenceCounted(false)
            }
        }
        wakeLock?.let {
            if (!it.isHeld) {
                it.acquire(30 * 60 * 1000L /* 30 minutes timeout */)
            }
        }
    }

    private fun releaseWakeLock() {
        try {
            wakeLock?.let {
                if (it.isHeld) {
                    it.release()
                }
            }
        } catch (_: Exception) {}
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(R.string.notification_channel_desc)
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun updateNotification() {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(NOTIFICATION_ID, buildNotification(_stateFlow.value))
    }

    private fun buildNotification(state: PoStState): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntentFlags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        } else {
            PendingIntent.FLAG_UPDATE_CURRENT
        }
        val pendingIntent = PendingIntent.getActivity(this, 0, intent, pendingIntentFlags)

        val contentText = when (state.status) {
            PoStStatus.IDLE -> getString(R.string.notification_text_idle)
            PoStStatus.ALLOCATING_MEMORY -> getString(R.string.notification_text_allocating)
            PoStStatus.PROVING -> "Computing PoST: ${state.allocatedMemoryMb} MB, ${state.targetHashes} hashes"
            PoStStatus.COMPLETED -> getString(R.string.notification_text_completed)
            PoStStatus.FAILED -> getString(R.string.notification_text_failed)
            PoStStatus.CANCELLED -> getString(R.string.notification_text_cancelled)
            PoStStatus.PAUSED -> "PoST Computation Paused"
        }

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.notification_title))
            .setContentText(contentText)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setOngoing(state.isRunning)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceJob.cancel()
        val handleToRelease = currentHandle
        if (handleToRelease != 0L) {
            try {
                nativeBridge.releaseMemory(handleToRelease)
            } catch (_: Exception) {}
            currentHandle = 0L
        }
        releaseWakeLock()
    }
}
