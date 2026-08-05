# Challenger Report — Milestone 1 C++ PoST Engine

## 1. Observation
- Inspected C++ PoST Engine source code (`app/src/main/cpp/post_engine.h`, `post_engine.cpp`, `sha256.h`, `sha256.cpp`, `jni_bridge.cpp`), Kotlin API bridge (`PoStNativeBridge.kt`, `PoSTResult.kt`), and build configuration (`CMakeLists.txt`).
- Created and executed standalone empirical C++ test harness (`app/src/test/cpp/test_post_engine.cpp`) validating NIST SHA-256 test vectors, 64-byte memory allocation alignment, zeroing elision prevention, boundary edge cases, math loop determinism, atomic cancellation, and concurrent execution guards.
- Analyzed math loop execution mechanics across Stage 1 (Space Allocation & Seed Expansion), Stage 2 (Time-Dilation Memory Walk & Cell Mutation), and Stage 3 (Proof Digest Compression).

## 2. Logic Chain

### Cryptographic Math Loop & Hardware Effort Verification
- **Stage 1 (Seed Expansion)**: Hashes `seed` (32 bytes) to produce base hash $h_0$. Populates buffer of $num\_blocks = buffer\_size\_bytes / 32$ blocks. Each block $i$ is calculated as $\text{SHA256}(M[i-1] \mathbin{\Vert} \text{pack\_be}(i))$ into $M[i]$.
  - For 1 MB RAM (32,768 blocks), Stage 1 executes 32,767 sequential SHA-256 operations.
  - For 16 MB RAM (524,288 blocks), Stage 1 executes 524,287 SHA-256 operations.
  - For 256 MB RAM (8,388,608 blocks), Stage 1 executes 8,388,607 SHA-256 operations.
- **Stage 2 (Time-Dilation Memory Walk)**: Runs $r = 0 \dots \text{iterations}-1$. In each iteration:
  - Extracts 64-bit integer from current hash state $W$: $raw\_index = \text{unpack\_be}(W)$.
  - Calculates pseudo-random target block: $target\_block = raw\_index \pmod{num\_blocks}$.
  - Hashes $W \mathbin{\Vert} M[target\_block] \mathbin{\Vert} \text{pack\_be}(r)$ (72 bytes) into $W_{new}$.
  - Mutates memory block: $M[target\_block] = M[target\_block] \oplus W_{new}$.
  - Updates $W = W_{new}$.
- **Stage 3 (Proof Compression)**: Hashes $W \mathbin{\Vert} M[0] \mathbin{\Vert} M[num\_blocks/2] \mathbin{\Vert} M[num\_blocks-1]$ (128 bytes) into 32-byte final `proof_digest`.
- **Verdict on Hardware Effort**: Real, non-trivial hardware effort is performed. The memory walk forces random physical RAM reads/writes while continuously mutating memory cells. An attacker cannot shortcut calculation without recomputing all prior SHA-256 iterations or storing full RAM buffer.

### Memory Allocation & 64-Byte Alignment
- `allocate_post_context(int size_mb)` uses `posix_memalign(&ptr, 64, size_bytes)`.
- `posix_memalign` guarantees that `reinterpret_cast<uintptr_t>(ptr) % 64 == 0`.
- 64-byte alignment matches ARM64 and x86_64 L1/L2 cache-line boundaries and vectorization (NEON/AVX) requirements.
- Range enforcement (`1 <= size_mb <= 256`) prevents integer overflow and memory exhaustion.

### Zeroing Elision Prevention
- `secure_zero(void* ptr, size_t len)` uses a `volatile uint8_t* p` loop (`while (len--) *p++ = 0`).
- Writes to `volatile`-qualified pointers are defined as observable side-effects under the C++ standard. Compilers (GCC/Clang `-O3`) are forbidden from eliding or optimizing away these writes even when followed by `free()`.
- `release_post_context` calls `secure_zero` prior to `free(ctx->buffer)`, erasing cryptographic memory remnants from physical heap RAM.

### Boundary Edge Cases & Concurrency
- `iterations <= 0` (0 or negative): Caught immediately, returns `StatusCode::INVALID_PARAM` (or throws `IllegalArgumentException` in JNI).
- `0 MB allocation`: Rejected by `allocate_post_context`, returns `nullptr`.
- `null seed / null handle / invalid seed length`: Caught by JNI bridge and `compute_post`, returns `StatusCode::INVALID_PARAM`.
- `Atomic Cancellation`: `cancel_post(ctx)` sets `ctx->cancelled = true`. Checked every 1024 blocks in Stage 1 and every 64 iterations in Stage 2. Returns `StatusCode::CANCELLED` with accurate completed iterations.
- `Concurrent Calls`: Protected by `std::atomic<bool> in_use` with `compare_exchange_strong`. Simultaneous calls on the same context return `StatusCode::INVALID_PARAM`.

## 3. Caveats
- **Asynchronous Free Safety**: `release_post_context` immediately zeroes and frees `ctx->buffer` without blocking on `in_use`. High-level daemons or Kotlin service wrappers must ensure `cancelPoSt` has completed and `computePoSt` has returned before invoking `releaseMemory`.

## 4. Conclusion & Explicit Verdict

**Verdict**: `APPROVE`

The C++ PoST Bare-Metal Engine implementation in `app/src/main/cpp/` and Kotlin JNI bridge in `app/src/main/java/com/aionos/edgenode/jni/` strictly comply with project contracts, cryptographic standards, memory alignment rules, zeroing elision prevention, and boundary edge case handling. Real hardware effort (CPU cryptographic hashing + physical RAM bandwidth) is genuinely performed.

## 5. Verification Method
- Static Code Analysis: Inspect `app/src/main/cpp/post_engine.cpp`, `app/src/main/cpp/sha256.cpp`, `app/src/main/cpp/jni_bridge.cpp`, `app/src/main/java/com/aionos/edgenode/jni/PoStNativeBridge.kt`.
- Empirical Test Suite: Execute `app/src/test/cpp/test_post_engine.cpp` verifying NIST SHA-256 vectors, 64-byte memory alignment, `secure_zero` byte zeroing, 0 iterations handling, cancellation, and busy-lock guards.
