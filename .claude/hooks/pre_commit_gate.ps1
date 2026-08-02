param([switch]$Strict)

$ErrorActionPreference = "Stop"
$projectRoot = [IO.Path]::GetFullPath($env:CLAUDE_PROJECT_DIR)
Push-Location $projectRoot
try {
    $staged = @(git diff --cached --name-only --diff-filter=ACMR)
    if ($LASTEXITCODE -ne 0) { throw "Unable to inspect staged files." }
    if ($staged | Where-Object { $_ -match '(^|/)\.env($|\.)' }) { throw ".env file is staged." }
    if ($staged | Where-Object { $_ -match '^(docs/(SAFETY_CONSTITUTION|TCB_SPECIFICATION)\.md|src/tcb/|policies/|\.github/workflows/)' }) {
        throw "Protected files are staged and require explicit human review."
    }
    $deletedTests = @(git diff --cached --name-status -- tests | Where-Object { $_ -match '^D\s' })
    if ($deletedTests.Count -gt 0) { throw "Deletion of tests requires explicit review." }

    $missing = @()
    foreach ($tool in @('gitleaks', 'semgrep', 'uv')) {
        if ($null -eq (Get-Command $tool -ErrorAction SilentlyContinue)) { $missing += $tool }
    }
    if ($Strict -and $missing.Count -gt 0) { throw "Required tools missing: $($missing -join ', ')." }
    if ($null -ne (Get-Command gitleaks -ErrorAction SilentlyContinue)) { & gitleaks protect --staged --redact; if ($LASTEXITCODE -ne 0) { exit 1 } }
    if ($null -ne (Get-Command semgrep -ErrorAction SilentlyContinue)) { & semgrep scan --config auto --error; if ($LASTEXITCODE -ne 0) { exit 1 } }
    if ($null -ne (Get-Command uv -ErrorAction SilentlyContinue)) {
        & uv run ruff check .; if ($LASTEXITCODE -ne 0) { exit 1 }
        & uv run pyright; if ($LASTEXITCODE -ne 0) { exit 1 }
        & uv run pytest -q; if ($LASTEXITCODE -ne 0) { exit 1 }
    }
    if ($missing.Count -gt 0) { [Console]::Error.WriteLine("Skipped unavailable tools: $($missing -join ', '). Rerun with -Strict for a fail-closed gate.") }
} finally {
    Pop-Location
}
