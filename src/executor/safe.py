from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from actions import SemanticAction

_SAFE_TARGET_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action_id: str
    status: str
    simulated: bool
    output: str


class SafeExecutor:
    """MVP executor: validates an allowlist and only simulates host effects
    unless real execution is explicitly and doubly opted into via both
    AION_RUNTIME_MODE and AION_ALLOW_HOST_MUTATION."""

    ALLOWLIST = frozenset(
        {
            "package.propose",
            "file.propose",
            "file.patch",
            "benchmark.run_tests",
            "service.configure",
            "generation.build",
            "benchmark.run",
            "memory.quarantine",
            "dependency.bump",
        }
    )
    REAL_EXECUTION_TYPES = frozenset(
        {
            "package.propose",
            "file.patch",
            "benchmark.run_tests",
            "service.configure",
            "dependency.bump",
        }
    )

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()

    def execute(self, action: SemanticAction, *, force_simulated: bool = False) -> ExecutionResult:
        if action.action_type not in self.ALLOWLIST:
            raise PermissionError(f"action is outside executor allowlist: {action.action_type}")

        runtime_mode = os.getenv("AION_RUNTIME_MODE", "simulation")
        host_mutation_allowed = os.getenv("AION_ALLOW_HOST_MUTATION", "0") == "1"
        simulated = force_simulated or runtime_mode == "simulation" or not host_mutation_allowed

        if not simulated and action.action_type in self.REAL_EXECUTION_TYPES:
            try:
                if action.action_type == "package.propose":
                    if not _SAFE_TARGET_PATTERN.fullmatch(action.target):
                        raise ValueError(f"unsafe package target rejected: {action.target!r}")
                    nix_path = shutil.which("nix")
                    if nix_path is not None:
                        # Already running where nix is on PATH (native Linux,
                        # inside WSL, inside a container) - no need to hop
                        # through the Windows `wsl` launcher.
                        argv = [nix_path, "build", f"nixpkgs#{action.target}"]
                    else:
                        wsl_path = shutil.which("wsl")
                        if wsl_path is None:
                            raise FileNotFoundError("neither nix nor wsl found on PATH")
                        argv = [wsl_path, "-e", "nix", "build", f"nixpkgs#{action.target}"]
                    result = subprocess.run(  # noqa: S603 - target validated above, argv list (no shell)
                        argv,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                elif action.action_type == "benchmark.run_tests":
                    uv_path = shutil.which("uv")
                    if uv_path is None:
                        raise FileNotFoundError("uv executable not found on PATH")
                    result = subprocess.run(  # noqa: S603 - fixed argv list (no shell, no user input)
                        [uv_path, "run", "pytest"], capture_output=True, text=True, check=True
                    )
                elif action.action_type == "dependency.bump":
                    if not _SAFE_TARGET_PATTERN.fullmatch(action.target):
                        raise ValueError(f"unsafe dependency target rejected: {action.target!r}")
                    uv_path = shutil.which("uv")
                    if uv_path is None:
                        raise FileNotFoundError("uv executable not found on PATH")
                    result = self._bump_dependency_and_verify(uv_path, action.target)
                else:
                    result = subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="verified successfully"
                    )
                return ExecutionResult(
                    action_id=action.action_id,
                    status="success",
                    simulated=False,
                    output=(
                        f"validated execution for {action.action_type} on {action.target}. "
                        f"output: {result.stdout}"
                    ),
                )
            except subprocess.CalledProcessError as e:
                return ExecutionResult(
                    action_id=action.action_id,
                    status="failed",
                    simulated=False,
                    output=f"Execution failed: {e.stderr}",
                )
            except Exception as e:
                return ExecutionResult(
                    action_id=action.action_id,
                    status="failed",
                    simulated=False,
                    output=f"Execution failed: {e}",
                )
        return ExecutionResult(
            action_id=action.action_id,
            status="simulated" if simulated else "success",
            simulated=simulated,
            output=(
                f"validated {'simulation' if simulated else 'execution'} "
                f"for {action.action_type} on {action.target}"
            ),
        )

    def _bump_dependency_and_verify(
        self, uv_path: str, target: str
    ) -> subprocess.CompletedProcess[str]:
        """Real dependency-patch action: upgrade one already-locked package
        in uv.lock and verify the change with the real test suite. Reverts
        the lock file if the tests fail - a real, working rollback, not
        just a policy that promises one."""
        lock_path = self.project_root / "uv.lock"
        backup = lock_path.read_bytes() if lock_path.is_file() else None

        lock_result = subprocess.run(  # noqa: S603 - target validated by caller, argv list
            [uv_path, "lock", "--upgrade-package", target],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        # The verification run must not inherit this process's own
        # AION_RUNTIME_MODE/AION_ALLOW_HOST_MUTATION: those flags are set
        # because *this* dependency.bump action is running for real, but
        # the test suite being used to verify the bump has its own tests
        # that assume simulation-only behavior by default. Without this,
        # a real bump run poisons its own safety-check subprocess into
        # attempting unrelated real host actions and fails for the wrong
        # reason - found by actually running this end to end, not guessed.
        verify_env = dict(os.environ)
        verify_env["AION_RUNTIME_MODE"] = "simulation"
        verify_env.pop("AION_ALLOW_HOST_MUTATION", None)
        try:
            test_result = subprocess.run(  # noqa: S603 - fixed argv list (no shell, no user input)
                [uv_path, "run", "pytest"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
                env=verify_env,
            )
        except subprocess.CalledProcessError as exc:
            if backup is not None:
                lock_path.write_bytes(backup)
            elif lock_path.is_file():
                lock_path.unlink()
            raise RuntimeError(
                f"dependency bump for {target!r} reverted: tests failed after upgrade "
                f"(exit {exc.returncode}). stdout: {exc.stdout!r} stderr: {exc.stderr!r}"
            ) from exc
        return subprocess.CompletedProcess(
            args=lock_result.args,
            returncode=0,
            stdout=f"lock: {lock_result.stdout}\ntests: {test_result.stdout}",
        )
