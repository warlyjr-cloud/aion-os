param(
	[string]$RemoteHost = "root@your-server",
	[string]$RemotePath = "/opt/aion-os",
	[string]$ComposeFile = "deploy/docker-compose.prod.yml",
	[string]$Domain = "localhost",
	[string]$ImageRepository = "warlyjr-cloud/aion-os",
	[switch]$SkipBuild,
	[switch]$SkipPull,
	[switch]$Logs,
	[switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$composeFileRelative = $ComposeFile

function Invoke-RemoteCommand {
	param([string]$Command)
	Write-Host "> $Command"
	if ($WhatIf) {
		Write-Host "[WhatIf] Would run remote command"
		return
	}
	ssh $RemoteHost $Command
}

function Ensure-RemoteDirectory {
	Invoke-RemoteCommand "mkdir -p '$RemotePath'"
}

function Copy-ProjectToRemote {
	Ensure-RemoteDirectory
	Write-Host "Uploading repository to remote host..."
	if ($WhatIf) {
		Write-Host "[WhatIf] Would sync repository to remote host"
		return
	}
	rsync -av --delete --exclude '.git' --exclude '.venv' --exclude '__pycache__' --exclude '__pycache__' --exclude '.pytest_cache' --exclude '.coverage' "$repoRoot/" "${RemoteHost}:$RemotePath/"
}

function Write-RemoteEnvFile {
	$envCommand = @"
cat > '$RemotePath/.env' <<EOF
DOMAIN=$Domain
GITHUB_REPOSITORY=$ImageRepository
EOF
"@
	Invoke-RemoteCommand $envCommand
}

function Invoke-RemoteCompose {
	param([string]$Command)
	Invoke-RemoteCommand "cd '$RemotePath' && docker compose -f '$composeFileRelative' $Command"
}

Copy-ProjectToRemote
Write-RemoteEnvFile

if (-not $SkipPull) {
	Invoke-RemoteCompose "pull"
}

if (-not $SkipBuild) {
	Invoke-RemoteCompose "build --no-cache"
}

Invoke-RemoteCompose "up -d --remove-orphans"

if ($Logs) {
	Invoke-RemoteCompose "logs -f"
}
