import logging
import signal
import threading
import time

import psutil


class CpuLoadThrottler:
    """
    Periodically pauses (SIGSTOP) processes whose CPU usage exceeds a
    threshold for a fraction of each tick, then resumes them (SIGCONT).
    """

    def __init__(self, threshold_percent: float = 80.0, tick_interval: float = 2.0):
        self.threshold = threshold_percent
        self.tick_interval = tick_interval
        self.running = False

    def _find_heavy_processes(self) -> list[psutil.Process]:
        heavy: list[psutil.Process] = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                # psutil cpu_percent over an interval requires two calls, but
                # we can use the non-blocking one. For more accuracy, we
                # could sleep, but we'll use a rough estimate for MVP.
                cpu = p.cpu_percent(interval=None)
                if cpu > self.threshold:
                    name = p.info["name"]
                    # Never throttle the daemon or core OS processes.
                    if name not in ["aiond", "python", "python3", "bash", "systemd", "sshd"]:
                        heavy.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return heavy

    def _throttle(self, process: psutil.Process):
        try:
            pid = process.pid
            name = process.name()
            logging.warning(f"[throttle] pausing heavy process PID {pid} ({name}).")

            # SIGSTOP/SIGCONT are POSIX-only (this targets Linux/WSL, not
            # native Windows); the surrounding try/except handles any
            # platform that lacks them.
            process.send_signal(
                signal.SIGSTOP  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            )

            time.sleep(self.tick_interval * 0.8)

            process.send_signal(
                signal.SIGCONT  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            )
            logging.warning(f"[throttle] resumed PID {pid} ({name}).")
        except Exception as e:
            logging.error(f"[throttle] failed to throttle PID {process.pid}: {e}")

    def loop(self):
        # Initial call to populate cpu_percent
        for p in psutil.process_iter():
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        while self.running:
            time.sleep(self.tick_interval)
            heavy_procs = self._find_heavy_processes()
            for p in heavy_procs:
                threading.Thread(target=self._throttle, args=(p,), daemon=True).start()

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.loop, daemon=True).start()
            logging.info("[throttle] CPU load throttler started.")

    def stop(self):
        self.running = False
