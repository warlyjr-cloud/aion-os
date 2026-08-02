$ErrorActionPreference = "Stop"

try {
    $event = ($input | Out-String) | ConvertFrom-Json
} catch {
    [Console]::Error.WriteLine("AION stop guard could not parse hook input.")
    exit 2
}
if ([bool]$event.stop_hook_active) { exit 0 }

$message = [string]$event.last_assistant_message
$unsupportedClaims = @(
    '(?i)(?<!não )\bé\s+estado\s+da\s+arte\b',
    '(?i)\balcanç(ou|amos)\s+(o\s+)?SOTA\b',
    '(?i)\bRSI\s+completo\s+(foi\s+)?(implementado|atingido|concluído)\b',
    '(?i)\b(seguran\S+a\s+absoluta|totalmente\s+seguro)\b',
    '(?i)\b(pronto\s+para\s+produ\S+o|production[- ]ready)\b',
    '(?i)\btodos\s+os\s+testes\s+passaram\b'
)
foreach ($pattern in $unsupportedClaims) {
    if ($message -match $pattern) {
        @{ decision = "block"; reason = "AION forbids unqualified SOTA, RSI, absolute-security, production-readiness, or test-success claims. Qualify the statement and cite executed evidence plus unexecuted checks." } | ConvertTo-Json -Compress
        exit 0
    }
}
exit 0
