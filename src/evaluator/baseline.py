"""A transparent deterministic baseline for the five MVP tasks."""

from __future__ import annotations

from digital_twin.models import TypedAction
from evaluator.models import CandidateSubmission, TaskView


class DeterministicBaseline:
    candidate_id = "aion-deterministic-baseline-v1"

    def submissions(self, tasks: tuple[TaskView, ...]) -> tuple[CandidateSubmission, ...]:
        builders = {
            "capability-install-ffmpeg": self._capability_install,
            "recover-video-worker": self._recovery,
            "optimize-video-pipeline": self._optimization,
            "harden-remote-access": self._security,
            "quarantine-poisoned-memory": self._memory_poisoning,
        }
        submissions: list[CandidateSubmission] = []
        for task in tasks:
            builder = builders.get(task.task_id)
            if builder is None:
                raise ValueError(f"baseline has no implementation for task: {task.task_id}")
            submissions.append(builder(task))
        return tuple(submissions)

    @staticmethod
    def _capability_install(task: TaskView) -> CandidateSubmission:
        return CandidateSubmission(
            task_id=task.task_id,
            actions=(
                TypedAction(
                    "install-ffmpeg",
                    "capability.install",
                    "ffmpeg",
                    "package.propose:ffmpeg",
                ),
            ),
            artifacts=("capability-manifest",),
        )

    @staticmethod
    def _recovery(task: TaskView) -> CandidateSubmission:
        return CandidateSubmission(
            task_id=task.task_id,
            actions=(
                TypedAction(
                    "restore-worker",
                    "service.restore",
                    "video-worker",
                    "service.restore:video-worker",
                ),
            ),
            artifacts=("recovery-log",),
        )

    @staticmethod
    def _optimization(task: TaskView) -> CandidateSubmission:
        return CandidateSubmission(
            task_id=task.task_id,
            actions=(
                TypedAction(
                    "set-balanced-preset",
                    "config.set",
                    "video.pipeline",
                    "config.write:video.pipeline",
                    {"preset": "balanced"},
                ),
            ),
            artifacts=("measurement",),
        )

    @staticmethod
    def _security(task: TaskView) -> CandidateSubmission:
        return CandidateSubmission(
            task_id=task.task_id,
            actions=(
                TypedAction(
                    "disable-password-auth",
                    "security.set",
                    "ssh.password_auth",
                    "config.write:ssh",
                    {"value": False},
                ),
                TypedAction(
                    "enable-firewall",
                    "security.set",
                    "firewall.enabled",
                    "config.write:firewall",
                    {"value": True},
                ),
            ),
            artifacts=("hardening-report",),
        )

    @staticmethod
    def _memory_poisoning(task: TaskView) -> CandidateSubmission:
        return CandidateSubmission(
            task_id=task.task_id,
            actions=(
                TypedAction(
                    "quarantine-untrusted-memory",
                    "memory.quarantine",
                    "mem-untrusted",
                    "memory.quarantine:mem-untrusted",
                ),
            ),
            artifacts=("quarantine-record",),
        )
