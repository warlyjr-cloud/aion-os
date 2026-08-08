import concurrent.futures
import logging
from collections.abc import Callable
from typing import Any


class ParallelRaceExecutor:
    """
    Runs several candidate variations of a function concurrently and
    returns the result of whichever succeeds first, discarding the rest.
    """

    def __init__(self, dimensions: int = 3):
        self.dimensions = dimensions

    def race(self, func: Callable[..., Any], args_list: list[tuple[Any, ...]]) -> Any:
        logging.info(f"[parallel-race] launching {self.dimensions} candidate variations...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.dimensions) as executor:
            future_to_index = {
                executor.submit(func, *args): i
                for i, args in enumerate(args_list[: self.dimensions])
            }

            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    logging.info(f"[parallel-race] variation {index} succeeded; using its result.")
                    # Cancelling pending futures is not trivial in ThreadPoolExecutor;
                    # we simply ignore their results once one has succeeded.
                    return result
                except Exception as exc:
                    logging.warning(f"[parallel-race] variation {index} failed ({exc}), discarded.")

        raise RuntimeError("All parallel variations failed.")
