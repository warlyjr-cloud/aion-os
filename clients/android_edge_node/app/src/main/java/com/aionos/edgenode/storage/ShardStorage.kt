package com.aionos.edgenode.storage

import android.content.Context
import java.io.File

/**
 * Manages the persistence of data shards on the device.
 */
class ShardStorage(private val context: Context) {

    private val shardDir = File(context.filesDir, "shards").apply {
        if (!exists()) mkdirs()
    }

    /**
     * Saves a shard to internal storage.
     */
    fun saveShard(id: String, data: ByteArray) {
        File(shardDir, id).writeBytes(data)
    }

    /**
     * Reads a shard from storage.
     */
    fun readShard(id: String): ByteArray? {
        val file = File(shardDir, id)
        return if (file.exists()) file.readBytes() else null
    }

    /**
     * Lists all shard IDs currently stored.
     */
    fun listShards(): List<String> {
        return shardDir.list()?.toList() ?: emptyList()
    }

    /**
     * Returns the total storage used by shards in bytes.
     */
    fun getTotalUsageBytes(): Long {
        return shardDir.listFiles()?.sumOf { it.length() } ?: 0L
    }

    /**
     * Deletes a shard.
     */
    fun deleteShard(id: String): Boolean {
        return File(shardDir, id).delete()
    }
}
