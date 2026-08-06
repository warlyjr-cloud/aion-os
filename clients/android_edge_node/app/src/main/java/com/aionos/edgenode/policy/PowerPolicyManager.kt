package com.aionos.edgenode.policy

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.BatteryManager

/**
 * Monitors device resource state to enforce execution policies.
 * Ensures the node is a "good citizen" by checking battery and network.
 */
class PowerPolicyManager(private val context: Context) {

    /**
     * Data class representing the current resource constraints.
     */
    data class ResourceState(
        val isCharging: Boolean,
        val isBatteryLow: Boolean,
        val isOnWifi: Boolean
    )

    /**
     * Checks if the node is allowed to perform heavy computations.
     * Policy: Must be charging OR battery > 20%, AND must be on Wi-Fi.
     */
    fun isExecutionAllowed(): Boolean {
        val state = getResourceState()
        return (state.isCharging || !state.isBatteryLow) && state.isOnWifi
    }

    fun getResourceState(): ResourceState {
        val batteryStatus: Intent? = IntentFilter(Intent.ACTION_BATTERY_CHANGED).let { filter ->
            context.registerReceiver(null, filter)
        }

        val status = batteryStatus?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                         status == BatteryManager.BATTERY_STATUS_FULL

        val level = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: 100
        val batteryPct = level * 100 / scale.toFloat()
        val isBatteryLow = batteryPct < 20

        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork
        val capabilities = connectivityManager.getNetworkCapabilities(network)
        val isOnWifi = capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true

        return ResourceState(isCharging, isBatteryLow, isOnWifi)
    }
}
