#include <jni.h>
#include <android/log.h>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include "post_engine.h"
#include "sha256.h"
#include <fstream>
#include <string>

#define LOG_TAG "AION_PoST_JNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

static jclass g_post_result_class = nullptr;
static jmethodID g_post_result_constructor = nullptr;
static std::mutex g_jni_cache_mutex;

static bool init_post_result_cache(JNIEnv* env) {
    std::lock_guard<std::mutex> lock(g_jni_cache_mutex);
    if (g_post_result_class != nullptr && g_post_result_constructor != nullptr) {
        return true;
    }
    jclass local_class = env->FindClass("com/aionos/edgenode/jni/PoSTResult");
    if (local_class == nullptr) {
        LOGE("Failed to find class com/aionos/edgenode/jni/PoSTResult");
        return false;
    }
    g_post_result_class = reinterpret_cast<jclass>(env->NewGlobalRef(local_class));
    env->DeleteLocalRef(local_class);
    if (g_post_result_class == nullptr) {
        LOGE("Failed to create global ref for PoSTResult class");
        return false;
    }
    g_post_result_constructor = env->GetMethodID(
        g_post_result_class,
        "<init>",
        "([BLjava/lang/String;JJII)V"
    );
    if (g_post_result_constructor == nullptr) {
        LOGE("Failed to find constructor for PoSTResult");
        return false;
    }
    return true;
}

static void digest_to_hex(const uint8_t* digest, char* hex_out) {
    static const char hex_digits[] = "0123456789abcdef";
    for (size_t i = 0; i < 32; ++i) {
        hex_out[i * 2]     = hex_digits[(digest[i] >> 4) & 0x0F];
        hex_out[i * 2 + 1] = hex_digits[digest[i] & 0x0F];
    }
    hex_out[64] = '\0';
}

static void throw_java_exception(JNIEnv* env, const char* class_name, const char* message) {
    jclass ex_class = env->FindClass(class_name);
    if (ex_class != nullptr) {
        env->ThrowNew(ex_class, message);
    }
}

extern "C" {

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }
    if (!init_post_result_cache(env)) {
        LOGE("Failed to initialize JNI class cache in JNI_OnLoad");
    }
    return JNI_VERSION_1_6;
}

JNIEXPORT void JNICALL JNI_OnUnload(JavaVM* vm, void* reserved) {
    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) == JNI_OK) {
        std::lock_guard<std::mutex> lock(g_jni_cache_mutex);
        if (g_post_result_class != nullptr) {
            env->DeleteGlobalRef(g_post_result_class);
            g_post_result_class = nullptr;
            g_post_result_constructor = nullptr;
        }
    }
}

JNIEXPORT jlong JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeAllocateMemory(
    JNIEnv *env,
    jobject thiz,
    jint size_mb
) {
    if (size_mb <= 0 || size_mb > 256) {
        throw_java_exception(env, "java/lang/IllegalArgumentException",
            "Requested memory size must be between 1 MB and 256 MB.");
        return 0L;
    }

    aion::post::PoSTContext* ctx = aion::post::allocate_post_context(size_mb);
    if (!ctx) {
        throw_java_exception(env, "java/lang/OutOfMemoryError",
            "Failed to allocate 64-byte aligned PoST memory.");
        return 0L;
    }

    LOGI("Allocated PoST memory context: %d MB at handle %p", size_mb, ctx);
    return reinterpret_cast<jlong>(ctx);
}

JNIEXPORT jobject JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeComputePoSt(
    JNIEnv *env,
    jobject thiz,
    jlong handle,
    jbyteArray seed_array,
    jint iterations
) {
    if (handle == 0L) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Native handle cannot be zero.");
        return nullptr;
    }

    if (seed_array == nullptr) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Seed byte array cannot be null.");
        return nullptr;
    }

    jsize seed_len = env->GetArrayLength(seed_array);
    if (seed_len != 32) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Seed byte array must be exactly 32 bytes.");
        return nullptr;
    }

    if (iterations <= 0) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Iteration count must be greater than zero.");
        return nullptr;
    }

    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    if (ctx == nullptr || ctx->buffer == nullptr || ctx->buffer_size_bytes == 0) {
        throw_java_exception(env, "java/lang/IllegalStateException", "Native memory buffer is uninitialized or freed.");
        return nullptr;
    }

    uint8_t seed_bytes[32];
    env->GetByteArrayRegion(seed_array, 0, 32, reinterpret_cast<jbyte*>(seed_bytes));
    if (env->ExceptionCheck()) {
        return nullptr;
    }

    aion::post::ExecutionResult res = aion::post::compute_post(
        ctx,
        seed_bytes,
        32,
        nullptr, // No real shard data provided
        0,
        static_cast<int>(iterations)
    );

    if (g_post_result_class == nullptr || g_post_result_constructor == nullptr) {
        if (!init_post_result_cache(env)) {
            return nullptr;
        }
    }

    jbyteArray j_digest_array = env->NewByteArray(32);
    if (j_digest_array != nullptr) {
        env->SetByteArrayRegion(j_digest_array, 0, 32, reinterpret_cast<const jbyte*>(res.proof_digest));
    }

    char hex_str[65];
    digest_to_hex(res.proof_digest, hex_str);
    jstring j_hex_string = env->NewStringUTF(hex_str);

    jobject result_obj = env->NewObject(
        g_post_result_class,
        g_post_result_constructor,
        j_digest_array,
        j_hex_string,
        static_cast<jlong>(res.execution_time_ms),
        static_cast<jlong>(res.allocated_ram_bytes),
        static_cast<jint>(res.iterations_completed),
        static_cast<jint>(static_cast<int32_t>(res.status))
    );

    return result_obj;
}

JNIEXPORT jobject JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeComputePoStWithData(
    JNIEnv *env,
    jobject thiz,
    jlong handle,
    jbyteArray seed_array,
    jbyteArray shard_array,
    jint iterations
) {
    if (handle == 0L) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Native handle cannot be zero.");
        return nullptr;
    }

    if (seed_array == nullptr) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Seed byte array cannot be null.");
        return nullptr;
    }

    jsize seed_len = env->GetArrayLength(seed_array);
    if (seed_len != 32) {
        throw_java_exception(env, "java/lang/IllegalArgumentException", "Seed byte array must be exactly 32 bytes.");
        return nullptr;
    }

    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    if (ctx == nullptr || ctx->buffer == nullptr || ctx->buffer_size_bytes == 0) {
        throw_java_exception(env, "java/lang/IllegalStateException", "Native memory buffer is uninitialized or freed.");
        return nullptr;
    }

    uint8_t seed_bytes[32];
    env->GetByteArrayRegion(seed_array, 0, 32, reinterpret_cast<jbyte*>(seed_bytes));

    uint8_t* shard_ptr = nullptr;
    jsize shard_len = 0;
    if (shard_array != nullptr) {
        shard_len = env->GetArrayLength(shard_array);
        shard_ptr = reinterpret_cast<uint8_t*>(env->GetByteArrayElements(shard_array, nullptr));
    }

    aion::post::ExecutionResult res = aion::post::compute_post(
        ctx,
        seed_bytes,
        32,
        shard_ptr,
        static_cast<size_t>(shard_len),
        static_cast<int>(iterations)
    );

    if (shard_array != nullptr && shard_ptr != nullptr) {
        env->ReleaseByteArrayElements(shard_array, reinterpret_cast<jbyte*>(shard_ptr), JNI_ABORT);
    }

    if (g_post_result_class == nullptr || g_post_result_constructor == nullptr) {
        if (!init_post_result_cache(env)) {
            return nullptr;
        }
    }

    jbyteArray j_digest_array = env->NewByteArray(32);
    if (j_digest_array != nullptr) {
        env->SetByteArrayRegion(j_digest_array, 0, 32, reinterpret_cast<const jbyte*>(res.proof_digest));
    }

    char hex_str[65];
    digest_to_hex(res.proof_digest, hex_str);
    jstring j_hex_string = env->NewStringUTF(hex_str);

    jobject result_obj = env->NewObject(
        g_post_result_class,
        g_post_result_constructor,
        j_digest_array,
        j_hex_string,
        static_cast<jlong>(res.execution_time_ms),
        static_cast<jlong>(res.allocated_ram_bytes),
        static_cast<jint>(res.iterations_completed),
        static_cast<jint>(static_cast<int32_t>(res.status))
    );

    return result_obj;
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeCancelPoSt(
    JNIEnv *env,
    jobject thiz,
    jlong handle
) {
    if (handle == 0L) return;
    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    aion::post::cancel_post(ctx);
    LOGI("Cancelled PoST computation for handle %p", ctx);
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativePausePoSt(
    JNIEnv *env,
    jobject thiz,
    jlong handle
) {
    if (handle == 0L) return;
    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    aion::post::pause_post(ctx);
    LOGI("Paused PoST computation for handle %p", ctx);
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeResumePoSt(
    JNIEnv *env,
    jobject thiz,
    jlong handle
) {
    if (handle == 0L) return;
    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    aion::post::resume_post(ctx);
    LOGI("Resumed PoST computation for handle %p", ctx);
}

JNIEXPORT jint JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeGetProgress(
    JNIEnv *env,
    jobject thiz,
    jlong handle
) {
    if (handle == 0L) return 0;
    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    return static_cast<jint>(ctx->progress.load(std::memory_order_relaxed));
}

JNIEXPORT jlong JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeGetPhysicalMemoryUsage(
    JNIEnv *env,
    jobject thiz
) {
    std::ifstream status("/proc/self/status");
    std::string line;
    while (std::getline(status, line)) {
        if (line.substr(0, 6) == "VmRSS:") {
            // Find the first digit
            size_t start = line.find_first_of("0123456789");
            if (start != std::string::npos) {
                size_t end = line.find_first_not_of("0123456789", start);
                std::string val_str = line.substr(start, end - start);
                return static_cast<jlong>(std::stoul(val_str) * 1024);
            }
        }
    }
    return 0L;
}

JNIEXPORT void JNICALL
Java_com_aionos_edgenode_jni_PoStNativeBridge_nativeReleaseMemory(
    JNIEnv *env,
    jobject thiz,
    jlong handle
) {
    if (handle == 0L) return;
    aion::post::PoSTContext* ctx = reinterpret_cast<aion::post::PoSTContext*>(handle);
    aion::post::release_post_context(ctx);
    LOGI("Released PoST memory context at handle %p", ctx);
}

} // extern "C"
