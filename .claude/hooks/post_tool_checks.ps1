$ErrorActionPreference = "Stop"

try {
    $event = ($input | Out-String) | ConvertFrom-Json
} catch {
    [Console]::Error.WriteLine("AION post-tool check could not parse hook input.")
    exit 2
}

$projectRoot = [IO.Path]::GetFullPath($env:CLAUDE_PROJECT_DIR)
$rawPath = ''
if ($null -ne $event.tool_input.file_path) { $rawPath = [string]$event.tool_input.file_path }
elseif ($null -ne $event.tool_input.path) { $rawPath = [string]$event.tool_input.path }
if ($rawPath -eq '') { exit 0 }
$fullPath = if ([IO.Path]::IsPathRooted($rawPath)) { [IO.Path]::GetFullPath($rawPath) } else { [IO.Path]::GetFullPath((Join-Path $projectRoot $rawPath)) }
if (-not ($fullPath.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase))) {
    [Console]::Error.WriteLine("Changed path resolved outside project.")
    exit 2
}
$rootPrefix = $projectRoot.TrimEnd('\', '/')
$relative = $fullPath.Substring($rootPrefix.Length).TrimStart('\', '/').Replace('\', '/')

if ($relative -match '^(docs/(SAFETY_CONSTITUTION|TCB_SPECIFICATION)\.md|src/tcb/|policies/|benchmarks/os_evobench/reserved/|\.github/workflows/)') {
    @{
        hookSpecificOutput = @{
            hookEventName = "PostToolUse"
            additionalContext = "Protected AION file changed: $relative. Stop and obtain explicit human review; record it in the handoff."
        }
    } | ConvertTo-Json -Depth 4 -Compress
}

if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) { exit 0 }
if ($fullPath.EndsWith('.json', [StringComparison]::OrdinalIgnoreCase)) {
    try { Get-Content -Raw -LiteralPath $fullPath | ConvertFrom-Json | Out-Null } catch {
        [Console]::Error.WriteLine("Invalid JSON in ${relative}: $($_.Exception.Message)")
        exit 2
    }
}
if ($fullPath.EndsWith('.py', [StringComparison]::OrdinalIgnoreCase)) {
    if ($null -eq (Get-Command uv -ErrorAction SilentlyContinue)) {
        [Console]::Error.WriteLine("uv is unavailable; Ruff and Pyright were not executed.")
        exit 0
    }
    & uv run ruff check -- $relative
    if ($LASTEXITCODE -ne 0) { exit 2 }
    & uv run pyright $relative
    if ($LASTEXITCODE -ne 0) { exit 2 }
}

exit 0
