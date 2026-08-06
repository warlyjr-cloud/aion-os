package com.aionos.edgenode.identity

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.interfaces.ECPublicKey

/**
 * Manages the node's cryptographic identity (AION ID) using Android Keystore.
 * Uses ECDSA (P-256) for compatibility across Android 8.0+.
 */
class WalletManager {

    companion object {
        private const val KEY_ALIAS = "aion_node_identity"
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
    }

    private val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply {
        load(null)
    }

    /**
     * Returns the AION ID (Base64 encoded Public Key).
     * Generates a new identity if none exists.
     */
    fun getAionId(): String {
        val publicKey = getOrCreateKeyPair().public as ECPublicKey
        return Base64.encodeToString(publicKey.encoded, Base64.NO_WRAP)
    }

    /**
     * Returns a shortened version of the AION ID for display.
     */
    fun getShortId(): String {
        val fullId = getAionId()
        return if (fullId.length > 12) {
            "${fullId.take(6)}...${fullId.takeLast(6)}"
        } else {
            fullId
        }
    }

    private fun getOrCreateKeyPair(): java.security.KeyPair {
        if (!keyStore.containsAlias(KEY_ALIAS)) {
            generateNewIdentity()
        }

        val entry = keyStore.getEntry(KEY_ALIAS, null) as KeyStore.PrivateKeyEntry
        return java.security.KeyPair(entry.certificate.publicKey, entry.privateKey)
    }

    private fun generateNewIdentity() {
        val kpg = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC,
            ANDROID_KEYSTORE
        )

        val parameterSpec = KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        ).run {
            setDigests(KeyProperties.DIGEST_SHA256)
            build()
        }

        kpg.initialize(parameterSpec)
        kpg.generateKeyPair()
    }

    /**
     * Simulation of balance for the node's contribution.
     */
    fun getSimulatedBalance(): Double {
        // In a real app, this would fetch from a blockchain or oracle.
        return 12.45 // AION Tokens
    }
}
