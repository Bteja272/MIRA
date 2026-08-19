from __future__ import annotations

import math
import threading
import time
from collections import (
    defaultdict,
    deque,
)

from fastapi import Request

from app.core.security_config import (
    security_settings,
)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[
            str,
            deque[float],
        ] = defaultdict(deque)

        self._lock = (
            threading.Lock()
        )

    def check(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> int:
        now = time.monotonic()

        cutoff = (
            now - window_seconds
        )

        with self._lock:
            events = self._events[
                key
            ]

            while (
                events
                and events[0] <= cutoff
            ):
                events.popleft()

            if len(events) >= limit:
                oldest = events[0]

                retry_after = (
                    window_seconds
                    - (
                        now - oldest
                    )
                )

                return max(
                    1,
                    math.ceil(
                        retry_after
                    ),
                )

            events.append(now)

        return 0


rate_limiter = InMemoryRateLimiter()


def get_client_key(
    request: Request,
) -> str:
    # Do not trust X-Forwarded-For here.
    # Trusted proxy handling belongs at
    # the deployment layer.
    if request.client is None:
        return "unknown"

    return (
        request.client.host
        or "unknown"
    )


def get_rate_limit_policy(
    request: Request,
) -> tuple[
    str,
    int,
    int,
]:
    path = request.url.path

    client_key = get_client_key(
        request
    )

    if (
        path == "/auth/login"
        and request.method == "POST"
    ):
        return (
            f"login:{client_key}",
            security_settings
            .rate_limit_login_requests,
            security_settings
            .rate_limit_login_window_seconds,
        )

    if (
        path == "/auth/register"
        and request.method == "POST"
    ):
        return (
            f"register:{client_key}",
            security_settings
            .rate_limit_register_requests,
            security_settings
            .rate_limit_register_window_seconds,
        )

    if (
        path == "/auth/refresh"
        and request.method == "POST"
    ):
        return (
            f"refresh:{client_key}",
            security_settings
            .rate_limit_refresh_requests,
            security_settings
            .rate_limit_refresh_window_seconds,
        )

    return (
        f"general:{client_key}",
        security_settings
        .rate_limit_general_requests,
        security_settings
        .rate_limit_general_window_seconds,
    )