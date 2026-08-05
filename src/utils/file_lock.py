import time
from pathlib import Path

class FileLock:
    """A cross-platform file locking mechanism using atomic directory creation."""

    def __init__(self, path: Path, timeout: float = 10.0, retry_delay: float = 0.05):
        self.lock_path = Path(str(path) + ".lock")
        self.timeout = timeout
        self.retry_delay = retry_delay

    def __enter__(self) -> "FileLock":
        start_time = time.monotonic()
        while True:
            try:
                # Directory creation is atomic on POSIX and Windows.
                self.lock_path.mkdir(parents=True, exist_ok=False)
                break
            except FileExistsError:
                if time.monotonic() - start_time >= self.timeout:
                    raise TimeoutError(f"Could not acquire lock for {self.lock_path} within {self.timeout}s")
                time.sleep(self.retry_delay)
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        try:
            self.lock_path.rmdir()
        except OSError:
            pass
