from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

import httpx

from services.api_client import BackendClient


class LlmServiceError(Exception):
    pass


SYSTEM_PROMPT = """You are an LMS Telegram bot assistant.

Use the provided tools whenever the user asks about labs, learners, scores, pass rates,
groups, timelines, completion, top learners, or data freshness. Prefer tool calls over
guessing. If the user asks an ambiguous question, ask a short clarifying question.

For greetings or obvious gibberish, reply helpfully without tools.

When tool results are available, summarize them clearly and include concrete numbers.
If the user asks to compare labs, rank labs, find the best lab, or find the worst lab,
first get the lab list and then call the needed analytics tool for every relevant lab
before answering. Do not stop after checking only one lab when the question asks about
all labs. Do not ask a follow-up question if the available tools already let you finish
the comparison.
"""


@dataclass(slots=True)
class LlmClient:
    base_url: str
    api_key: str
    model: str
    backend_client: BackendClient
    timeout_seconds: float = 30.0

    def _tool_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_items",
                    "description": "List labs and tasks from the LMS backend.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_learners",
                    "description": "List enrolled students and their groups.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_scores",
                    "description": "Get score buckets for a lab such as lab-04.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, for example lab-04.",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pass_rates",
                    "description": "Get per-task average scores and attempts for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, for example lab-04.",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_timeline",
                    "description": "Get submissions per day for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, for example lab-04.",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_groups",
                    "description": "Get per-group performance data for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, for example lab-04.",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_learners",
                    "description": "Get top learners by average score for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, for example lab-04.",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "How many learners to return.",
                                "default": 5,
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_completion_rate",
                    "description": "Get completion rate percentage for a lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, for example lab-04.",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_sync",
                    "description": "Refresh LMS data from the autochecker pipeline.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "get_items":
            return self.backend_client.get_items()
        if name == "get_learners":
            return self.backend_client.get_learners()
        if name == "get_scores":
            return self.backend_client.get_scores(str(arguments["lab"]))
        if name == "get_pass_rates":
            return self.backend_client.get_pass_rates(str(arguments["lab"]))
        if name == "get_timeline":
            return self.backend_client.get_timeline(str(arguments["lab"]))
        if name == "get_groups":
            return self.backend_client.get_groups(str(arguments["lab"]))
        if name == "get_top_learners":
            limit = int(arguments.get("limit", 5))
            return self.backend_client.get_top_learners(str(arguments["lab"]), limit)
        if name == "get_completion_rate":
            return self.backend_client.get_completion_rate(str(arguments["lab"]))
        if name == "trigger_sync":
            return self.backend_client.trigger_sync()
        raise LlmServiceError(f"Unknown tool requested by LLM: {name}")

    def _chat(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self._tool_schemas(),
            "tool_choice": "auto",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise LlmServiceError(
                f"LLM error: HTTP {exc.response.status_code} {exc.response.reason_phrase}"
            ) from exc
        except httpx.RequestError as exc:
            raise LlmServiceError(f"LLM error: {exc}") from exc

    def route(self, user_text: str) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

        for _ in range(8):
            response = self._chat(messages)
            message = response["choices"][0]["message"]
            tool_calls = message.get("tool_calls") or []
            content = message.get("content")

            if not tool_calls:
                if isinstance(content, str) and content.strip():
                    lower_content = content.lower()
                    if any(
                        phrase in lower_content
                        for phrase in [
                            "i will now check",
                            "i will check",
                            "i will call a tool",
                            "i'll call a tool",
                            "calling a tool",
                            "let me check",
                            "i'll check",
                            "i need to check",
                            "let me call a tool",
                            "would you like me to check",
                        ]
                    ):
                        messages.append(
                            {
                                "role": "assistant",
                                "content": content,
                            }
                        )
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "Continue the analysis by calling the needed tools now. "
                                    "Do not ask me for permission if you already have enough "
                                    "tools to continue."
                                ),
                            }
                        )
                        print(
                            "[summary] LLM stopped early; asking it to continue with tools",
                            file=sys.stderr,
                        )
                        continue
                    return content.strip()
                return "I couldn't produce a response yet. Try asking in a more specific way."

            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": tool_calls,
                }
            )

            for tool_call in tool_calls:
                name = tool_call["function"]["name"]
                raw_arguments = tool_call["function"].get("arguments", "{}")
                arguments = json.loads(raw_arguments) if raw_arguments else {}
                print(
                    f"[tool] LLM called: {name}({json.dumps(arguments, ensure_ascii=True)})",
                    file=sys.stderr,
                )
                result = self._execute_tool(name, arguments)
                if isinstance(result, list):
                    result_summary = f"{len(result)} records"
                elif isinstance(result, dict):
                    result_summary = ", ".join(sorted(result.keys()))
                else:
                    result_summary = type(result).__name__
                print(f"[tool] Result: {result_summary}", file=sys.stderr)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            print(
                f"[summary] Feeding {len(tool_calls)} tool results back to LLM",
                file=sys.stderr,
            )

        raise LlmServiceError("LLM error: tool loop did not finish after 8 iterations.")
