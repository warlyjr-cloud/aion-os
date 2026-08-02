$ErrorActionPreference = "Stop"

function Deny-ToolCall {
    param([string]$Reason)
    @{
        hookSpecificOutput = @{
            hookEventName = "PreToolUse"
            permissionDecision = "deny"
            permissionDecisionReason = $Reason
        }
    } | ConvertTo-Json -Depth 5 -Compress
    exit 0
}

try {
    $event = ($input | Out-String) | ConvertFrom-Json
} catch {
    [Console]::Error.WriteLine("AION guard could not parse hook input; refusing the tool call.")
    exit 2
}

$projectRoot = [IO.Path]::GetFullPath($env:CLAUDE_PROJECT_DIR).TrimEnd('\', '/')
$toolName = [string]$event.tool_name
$toolInput = $event.tool_input

if ($toolName -eq "Bash") {
    $command = [string]$toolInput.command
    $blockedCommands = @(
        '(?i)(^|[;&|]\s*)(sudo|su|doas)\b',
        '(?i)Start-Process\b.*-Verb\s+RunAs',
        '(?i)\b(rm\s+-rf|Remove-Item\b[^\r\n]*-(Recurse|Force)|del\s+/[sfq])\b',
        '(?i)\b(git\s+(reset\s+--hard|push\b[^\r\n]*--force)|mkfs\b|dd\s+if=|shutdown\b|reboot\b)'
    )
    foreach ($pattern in $blockedCommands) {
        if ($command -match $pattern) {
            Deny-ToolCall "AION blocks privilege escalation, destructive host commands, and history rewriting."
        }
    }
    if ($command -match '(?i)\b(curl|wget|Invoke-WebRequest|ssh|scp|git\s+(push|pull|fetch|clone)|gh\s+)\b') {
        Deny-ToolCall "Network or external-service access requires a separate, explicit human-approved path."
    }
}

$pathValues = @()
foreach ($property in @('file_path', 'path', 'notebook_path')) {
    if ($null -ne $toolInput.$property -and [string]$toolInput.$property -ne '') {
        $pathValues += [string]$toolInput.$property
    }
}

foreach ($rawPath in $pathValues) {
    $candidate = if ([IO.Path]::IsPathRooted($rawPath)) {
        [IO.Path]::GetFullPath($rawPath)
    } else {
        [IO.Path]::GetFullPath((Join-Path $projectRoot $rawPath))
    }
    if (-not ($candidate -eq $projectRoot -or $candidate.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase))) {
        Deny-ToolCall "File access outside CLAUDE_PROJECT_DIR is blocked."
    }
    $relative = $candidate.Substring($projectRoot.Length).TrimStart('\', '/').Replace('\', '/')
    if ($relative -match '(^|/)\.env($|\.)') {
        Deny-ToolCall "Reading or editing .env files is blocked."
    }
    $isWrite = $toolName -match '^(Write|Edit|MultiEdit|NotebookEdit)$'
    if ($isWrite -and $relative -match '^(docs/(SAFETY_CONSTITUTION|TCB_SPECIFICATION)\.md|src/tcb/|policies/|benchmarks/os_evobench/reserved/|\.github/workflows/)') {
        Deny-ToolCall "This is a protected AION path. Use a separate human-reviewed change process."
    }
}

exit 0
