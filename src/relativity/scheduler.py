import psutil
import time
import signal
import threading
import logging

class TimeDilationEngine:
    """
    Applies the concept of Relativistic Time Dilation to OS processes.
    Heavy processes (creating compute 'gravity') have their local time slowed down
    relative to the rest of the OS using SIGSTOP and SIGCONT.
    """
    def __init__(self, threshold_percent: float = 80.0, tick_interval: float = 2.0):
        self.threshold = threshold_percent
        self.tick_interval = tick_interval
        self.running = False

    def _find_heavy_processes(self) -> list[psutil.Process]:
        heavy = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                # psutil cpu_percent over an interval requires two calls, but we can use the non-blocking one
                # For more accuracy, we could sleep, but we'll use a rough estimate for MVP
                cpu = p.cpu_percent(interval=None)
                if cpu > self.threshold:
                    name = p.info['name']
                    # Protect vital organs
                    if name not in ['aiond', 'python', 'python3', 'bash', 'systemd', 'sshd']:
                        heavy.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return heavy

    def _apply_dilation(self, process: psutil.Process):
        try:
            pid = process.pid
            name = process.name()
            logging.warning(f"[\u2622\ufe0f RELATIVITY] Gravity Well detected at PID {pid} ({name}). Dilating time...")
            
            # Freeze the process in its own timeline
            process.send_signal(signal.SIGSTOP)
            
            # The process experiences 0 seconds while the OS experiences X seconds
            time.sleep(self.tick_interval * 0.8) 
            
            # Resume the timeline
            process.send_signal(signal.SIGCONT)
            logging.warning(f"[\u2622\ufe0f RELATIVITY] Time un-dilated for PID {pid} ({name}).")
        except Exception as e:
            logging.error(f"[RELATIVITY] Failed to dilate time for PID {process.pid}: {e}")

    def loop(self):
        # Initial call to populate cpu_percent
        for p in psutil.process_iter():
            try: p.cpu_percent(interval=None)
            except: pass
            
        while self.running:
            time.sleep(self.tick_interval)
            heavy_procs = self._find_heavy_processes()
            for p in heavy_procs:
                threading.Thread(target=self._apply_dilation, args=(p,), daemon=True).start()

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.loop, daemon=True).start()
            logging.info("[\u2622\ufe0f RELATIVITY] Time Dilation Engine started.")
            
    def stop(self):
        self.running = False
