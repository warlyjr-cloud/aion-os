## 2026-08-05T13:50:10Z
You are Test Writer M3 (test_writer_m3) for Milestone 3 of the AION OS Android Edge Node project.

Project Root: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node
Working Directory: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\.agents\test_writer_m3
Original Request Path: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\ORIGINAL_REQUEST.md
Project File: C:\Users\GABRIELA APSOL\teamwork_projects\aion_edge_node\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All test implementations must be genuine. DO NOT hardcode test assertions to pass blindly, create facade tests, or bypass JNI calls. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Exclusive File Ownership:
You own creation of:
- `app/src/androidTest/java/com/aionos/edgenode/AionPostNativeInstrumentedTest.kt`
- `app/src/test/java/com/aionos/edgenode/AionPostNativeUnitTest.kt`

Tasks & Implementation Objectives:
1. Initialize briefing/progress files in `.agents/test_writer_m3/`.
2. Implement `AionPostNativeInstrumentedTest.kt` in `app/src/androidTest/java/com/aionos/edgenode/`:
   - Annotate with `@RunWith(AndroidJUnit4::class)` or `@RunWith(JUnit4::class)`.
   - Test 1: Native JNI Library Load & Handle Allocation (`allocateMemory(16)` returns non-zero handle).
   - Test 2: Native PoST Execution (`computePoSt` returns `PoSTResult` with status 0, non-null 32-byte digest, 64-char hex, execution time > 0ms, and allocated RAM == 16MB).
   - Test 3: Deterministic Hash Verification (Same seed + iterations = identical proof hash digest; different seed = distinct digest).
   - Test 4: Hardware Effort Attestation (Assert execution time > 0 and non-trivial memory walk mutations).
   - Test 5: Atomic Cancellation & Thread Safety (`cancelPoSt` triggers cancelled status code 2).
   - Test 6: Memory Release Cleanup (`releaseMemory` releases native context, subsequent calls on released handle throw `IllegalStateException`).
3. Implement `AionPostNativeUnitTest.kt` in `app/src/test/java/com/aionos/edgenode/` for JVM-side JNI / state machine unit verification.
4. Verify tests, document in `changes.md`, write `handoff.md`, and send a message to orchestrator when finished.
