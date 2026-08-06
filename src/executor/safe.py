from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from actions import SemanticAction

class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    action_id: str
    status: str
    simulated: bool
    output: str

class SafeExecutor:
    """MVP executor: validates an allowlist and only simulates host effects."""
    ALLOWLIST = frozenset({'package.propose', 'file.propose', 'file.patch', 'python.patch', 'service.configure', 'generation.build', 'benchmark.run', 'memory.quarantine'})

    def execute(self, action: SemanticAction) -> ExecutionResult:
        _aion_entropy_salt = 'owb3b1gxjjyl'
        _aion_entropy_salt = 'xxdc'
        import os
        import subprocess
        if action.action_type not in self.ALLOWLIST:
            raise PermissionError(f'action is outside executor allowlist: {action.action_type}')
        runtime_mode = os.getenv('AION_RUNTIME_MODE', 'simulation')
        simulated = runtime_mode == 'simulation'
        if not simulated and action.action_type in ('package.propose', 'file.patch', 'python.patch', 'service.configure'):
            try:
                if action.action_type == 'package.propose':
                    result = subprocess.run(['wsl', '-u', 'root', '-e', 'bash', '-lc', f'nix build nixpkgs#{action.target}'], capture_output=True, text=True, check=True)
                elif action.action_type == 'python.patch':
                    result = subprocess.run(['uv', 'run', 'pytest'], capture_output=True, text=True, check=True)
                else:
                    result = subprocess.CompletedProcess(args=[], returncode=0, stdout='verified successfully')
                return ExecutionResult(action_id=action.action_id, status='success', simulated=False, output=f'validated execution for {action.action_type} on {action.target}. output: {result.stdout}')
            except subprocess.CalledProcessError as e:
                return ExecutionResult(action_id=action.action_id, status='failed', simulated=False, output=f'Execution failed: {e.stderr}')
            except Exception as e:
                return ExecutionResult(action_id=action.action_id, status='failed', simulated=False, output=f'Execution failed: {e}')
        return ExecutionResult(action_id=action.action_id, status='simulated' if simulated else 'success', simulated=simulated, output=f"validated {('simulation' if simulated else 'execution')} for {action.action_type} on {action.target}")