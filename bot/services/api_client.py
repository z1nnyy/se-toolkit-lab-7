from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class BackendServiceError(Exception):
    pass


@dataclass(slots=True)
class BackendClient:
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _request(
        self, method: str, path: str, *, params: dict[str, str] | None = None
    ) -> Any:
        url = f"{self.base_url.rstrip('/')}{path}"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.request(
                    method,
                    url,
                    headers=self._headers(),
                    params=params,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            reason = exc.response.reason_phrase
            raise BackendServiceError(
                f"Backend error: HTTP {status} {reason}. The backend service may be down."
            ) from exc
        except httpx.ConnectError as exc:
            raise BackendServiceError(
                f"Backend error: connection refused ({self.base_url}). Check that the services are running."
            ) from exc
        except httpx.TimeoutException as exc:
            raise BackendServiceError(
                f"Backend error: request timed out while contacting {self.base_url}."
            ) from exc
        except httpx.RequestError as exc:
            raise BackendServiceError(f"Backend error: {exc}") from exc

    def get_items(self) -> list[dict[str, Any]]:
        return self._request("GET", "/items/")

    def get_learners(self) -> list[dict[str, Any]]:
        return self._request("GET", "/learners/")

    def get_scores(self, lab: str) -> list[dict[str, Any]]:
        return self._request("GET", "/analytics/scores", params={"lab": lab})

    def get_pass_rates(self, lab: str) -> list[dict[str, Any]]:
        return self._request("GET", "/analytics/pass-rates", params={"lab": lab})

    def get_timeline(self, lab: str) -> list[dict[str, Any]]:
        return self._request("GET", "/analytics/timeline", params={"lab": lab})

    def get_groups(self, lab: str) -> list[dict[str, Any]]:
        return self._request("GET", "/analytics/groups", params={"lab": lab})

    def get_top_learners(self, lab: str, limit: int = 5) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/analytics/top-learners",
            params={"lab": lab, "limit": str(limit)},
        )

    def get_completion_rate(self, lab: str) -> dict[str, Any]:
        return self._request("GET", "/analytics/completion-rate", params={"lab": lab})

    def trigger_sync(self) -> dict[str, Any]:
        return self._request("POST", "/pipeline/sync")
