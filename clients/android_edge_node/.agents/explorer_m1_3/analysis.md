# Technical Analysis & Build Configuration Specification: Milestone 1 NDK & Gradle Toolchain

**Author:** Explorer M1_3 (`explorer_m1_3`)  
**Project:** AION OS Android Edge Node PoST  
**Date:** 2026-08-05  
**Target Path:** `C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\explorer_m1_3\analysis.md`  
**Scope:** Milestone 1 — Bare-Metal C++ PoST Engine & JNI Bridge (Build & Toolchain Focus)

---

## 1. Executive Summary & Problem Scope

This report defines the complete, production-ready build configuration specification and project layout for **Milestone 1** of the AION OS Android Edge Node project.

### Core Objectives:
1. **Target ABI Compilation Specs**: Formulate exact NDK compilation parameters for `libaion_post.so` targeting `arm64-v8a` (physical hardware) and `x86_64` (Android emulator).
2. **Project Build Configuration**: Provide complete, copy-pasteable build configuration specs for:
   - `settings.gradle.kts`
   - Root `build.gradle.kts`
   - `gradle.properties`
   - `app/build.gradle.kts`
   - `app/CMakeLists.txt`
   - `app/src/main/AndroidManifest.xml`
3. **Contract & Hierarchy Alignment**: Ensure 100% compliance with `PROJECT.md`, adopting package namespace `com.aionos.edgenode` and supporting the `PoStNativeBridge` Kotlin contract.

---

## 2. Environment & Toolchain Requirements

| Component | Target Version | Purpose in AION Edge Node |
|---|---|---|
| **Compile SDK** | `API 34` (Android 14) | Modern Android SDK APIs and system permissions. |
| **Min SDK** | `API 26` (Android 8.0) | Memory management primitives (`posix_memalign`) & Foreground Services. |
| **Android NDK** | `r25+` (e.g. `25.2.9519653`) | Clang toolchain, libc++, sysroot cross-compilation for bare-metal C++. |
| **CMake** | `3.22.1+` | Native CMake build engine integrated with AGP. |
| **C++ Standard** | `C++17` | Aligned memory allocation, `<chrono>`, `<vector>`, `<thread>`, `<cstdint>`. |
| **Android Gradle Plugin (AGP)** | `8.2.2` | Gradle build automation engine for Android and NDK JNI integration. |
| **Kotlin** | `1.9.22` | Kotlin language support for JNI bindings and App Daemon. |
| **Java JDK** | `JDK 17` | Execution environment required for AGP 8.2+ and Gradle 8.4+. |

---

## 3. Comprehensive Project File Hierarchy Blueprint

The directory structure follows modern Android application conventions and matches `PROJECT.md` contracts:

```
aion_edge_node/
├── build.gradle.kts                      # Root Gradle build file (plugins, clean task)
├── settings.gradle.kts                   # Repositories & module inclusions
├── gradle.properties                     # JVM heap & AndroidX settings
├── gradlew / gradlew.bat                 # Gradle Wrapper scripts
├── gradle/
│   └── wrapper/
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties     # Gradle 8.4 distribution
└── app/
    ├── build.gradle.kts                  # App module build configuration (NDK, CMake, dependencies)
    ├── CMakeLists.txt                    # CMake native build script for libaion_post.so
    └── src/
        ├── main/
        │   ├── AndroidManifest.xml       # Permissions, Application, Activity & Service manifest
        │   ├── cpp/                      # Bare-Metal Native C++ Engine Sources
        │   │   ├── post_engine.h         # PoST Engine memory allocation & compute header
        │   │   ├── post_engine.cpp       # 3-stage memory-hard cryptographic loop implementation
        │   │   ├── sha256.h              # Pure C++ SHA-256 header
        │   │   ├── sha256.cpp            # SHA-256 implementation
        │   │   └── jni_bridge.cpp        # JNI native functions mapping to Kotlin
        │   └── java/com/aionos/edgenode/
        │       ├── jni/
        │       │   ├── PoStNativeBridge.kt  # Native JNI binding wrapper class
        │       │   └── PoSTResult.kt        # Data class for PoST output evaluation
        │       ├── service/
        │       │   └── PoStDaemonService.kt # Foreground service daemon
        │       ├── ui/
        │       │   └── MainActivity.kt      # Compose UI entry point
        │       └── model/
        │           └── PoStState.kt          # UI state machine data model
        └── androidTest/                  # Instrumentation Test Suite
            └── java/com/aionos/edgenode/
                └── AionPostNativeInstrumentedTest.kt # Native JNI hash attestation tests
```

---

## 4. Build Configuration Specifications

### 4.1 `settings.gradle.kts`
```kotlin
pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "aion_edge_node"
include(":app")
```

### 4.2 Root `build.gradle.kts`
```kotlin
plugins {
    id("com.android.application") version "8.2.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
```

### 4.3 `gradle.properties`
```properties
# Enable AndroidX support
android.useAndroidX=true

# Kotlin style
kotlin.code.style=official

# JVM memory configuration for Gradle & NDK compilation
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8

# Android non-transitive R classes for build speed optimization
android.nonTransitiveRClass=true
```

### 4.4 `app/build.gradle.kts`
```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.aionos.edgenode"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.aionos.edgenode"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        externalNativeBuild {
            cmake {
                cppFlags("-std=c++17 -O3 -Wall -Wextra -frtti -fexceptions")
                arguments(
                    "-DANDROID_STL=c++_shared",
                    "-DANDROID_PLATFORM=android-26"
                )
                abiFilters("arm64-v8a", "x86_64")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isDebuggable = true
            jniDebuggable = true
        }
    }

    externalNativeBuild {
        cmake {
            path = file("CMakeLists.txt")
            version = "3.22.1"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    testOptions {
        unitTests {
            isIncludeAndroidResources = true
            isReturnDefaultValues = true
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    // Unit testing libraries
    testImplementation("junit:junit:4.13.2")

    // Android Instrumentation & Espresso testing
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("androidx.test:runner:1.5.2")
    androidTestImplementation("androidx.test:rules:1.5.0")
}
```

### 4.5 `app/CMakeLists.txt`
```cmake
cmake_minimum_required(VERSION 3.22.1)
project("aion_post_engine" CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags for native performance
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -ffast-math")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -g")

# Source files for native C++ PoST core
set(NATIVE_SOURCES
    src/main/cpp/post_engine.cpp
    src/main/cpp/sha256.cpp
    src/main/cpp/jni_bridge.cpp
)

# Shared library target for Android JNI (libaion_post.so)
add_library(aion_post SHARED ${NATIVE_SOURCES})

# Include header directories
target_include_directories(aion_post PRIVATE src/main/cpp)

# Locate NDK logging library
find_library(log-lib log)

# Link NDK logging library
target_link_libraries(aion_post PRIVATE ${log-lib})
```

### 4.6 `app/src/main/AndroidManifest.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Permissions required for Foreground Daemon Service & Hardware Execution -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="AION Edge Node"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">

        <!-- Main UI Activity -->
        <activity
            android:name=".ui.MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- PoST Background Foreground Daemon Service -->
        <service
            android:name=".service.PoStDaemonService"
            android:enabled="true"
            android:exported="false"
            android:foregroundServiceType="specialUse">
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="Proof of Space-Time Infrastructure Node Computation" />
        </service>

    </application>

</manifest>
```

---

## 5. ABI Targets & NDK Cross-Compilation Specification

### 5.1 ABI Target Matrix

| Target ABI | Architecture | Primary Deployment Target | Compilation Flags / Notes |
|---|---|---|---|
| `arm64-v8a` | ARM 64-bit (AArch64) | Physical Android Hardware (Smartphones, Edge Devices) | Uses 64-bit pointers, 64-bit aligned memory (`posix_memalign`), ARM NEON vector instructions. Optimized via `-O3`. |
| `x86_64` | Intel/AMD 64-bit | Android Emulator (AVD) & CI/CD Test Runners | Native host execution inside x86 development environments without ARM emulation translation overhead. |

### 5.2 NDK STL Selection (`c++_shared`)
- **Choice**: `-DANDROID_STL=c++_shared`
- **Rationale**: Dynamic linking against `libc++_shared.so` provided by NDK. Avoids duplicate C++ runtime state across shared objects, ensures proper exception handling (`-fexceptions`), runtime type information (`-frtti`), and complete standard library features (such as `std::aligned_alloc`, `std::vector`, `std::thread`, `std::chrono`).

---

## 6. Verification Method & Build Commands

1. **Gradle Build Assembly Test**:
   ```bash
   ./gradlew assembleDebug
   ```
   *Expected Outcome*: Successful build generating `app-debug.apk` containing `lib/arm64-v8a/libaion_post.so` and `lib/x86_64/libaion_post.so`.

2. **Native Shared Library Inspection**:
   - Inspect APK native libraries using `unzip -l app/build/outputs/apk/debug/app-debug.apk`:
     - Must contain `lib/arm64-v8a/libaion_post.so`
     - Must contain `lib/x86_64/libaion_post.so`

3. **Android Instrumentation JNI Verification**:
   ```bash
   ./gradlew connectedAndroidTest
   ```
   *Expected Outcome*: Instrumentation tests load `libaion_post.so` and assert deterministic SHA-256 hash outputs.

---

## 7. Conclusions & Recommendations for Implementer

1. All build files use explicit Kotlin DSL (`.gradle.kts`) and CMake 3.22.1 to guarantee reproducible command-line builds.
2. Package namespace is strictly unified to `com.aionos.edgenode`.
3. Next Step: Implementer agent (`implementer_m1`) can take these specs directly to construct the project structure and build files in `app/`.
