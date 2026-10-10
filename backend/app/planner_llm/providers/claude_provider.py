import asyncio
import json
import os
import shutil
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from app.planner_llm.providers.base import (
    PipelineStep,
    Prompt,
    ProviderHealth,
    ProviderName,
    parse_json_object,
    probe_health,
    strict_json_schema,
)
from app.planner_llm.providers.errors import (
    ModelNotFoundError,
    ProviderAuthError,
    ProviderConnectionError,
    ProviderNotConfiguredError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class ClaudeCliProvider:
    """Claude through the local ``claude`` CLI (Claude Code) signed in on this machine.

    Runs ``claude -p`` with every tool disabled and ``--json-schema`` so the answer comes back as
    ``structured_output``. Uses the user's own Claude login, so no API key is stored here.
    """

    name: ProviderName = "claude"

    def __init__(
        self,
        *,
        cli_path: str = "claude",
        models: Mapping[PipelineStep, str],
        max_concurrency: int = 2,
        timeout_seconds: float = 180.0,
    ) -> None:
        self._cli_path = cli_path
        self._models = dict(models)
        self.max_concurrency = max(1, max_concurrency)
        self.timeout_seconds = timeout_seconds

    def model_for(self, step: PipelineStep) -> str:
        if step == "health_check":
            step = "clarify"
        return self._models.get(step) or self._models["clarify"]

    def _executable(self) -> str:
        path = shutil.which(self._cli_path)
        if path is None:
            raise ProviderNotConfiguredError(f"Claude CLI {self._cli_path!r} not found")
        return path

    async def generate_json(self, prompt: Prompt, schema: type[BaseModel]) -> dict[str, Any]:
        model = self.model_for(prompt.step)
        args = [
            self._executable(),
            "-p",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(strict_json_schema(schema)),
            "--tools",
            "",
            "--no-session-persistence",
            "--system-prompt",
            prompt.system,
            "--model",
            model,
        ]
        # The user text goes on stdin, not argv: it can be long and must stay out of `ps`.
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.expanduser("~"),
                env=env,
            )
        except OSError as exc:
            raise ProviderConnectionError("cannot start the Claude CLI") from exc
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(prompt.user.encode()), timeout=self.timeout_seconds
            )
        except TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise ProviderTimeoutError(
                f"Claude CLI timed out after {self.timeout_seconds:g}s"
            ) from exc

        try:
            reply = json.loads(stdout.decode(errors="replace"))
        except json.JSONDecodeError:
            reply = None
        if not isinstance(reply, dict):
            raise ProviderUnavailableError(f"Claude CLI exited with code {proc.returncode}")

        if reply.get("is_error") or proc.returncode != 0:
            detail = str(reply.get("result") or stderr.decode(errors="replace"))[:200].lower()
            if "login" in detail or "authenticat" in detail or "api key" in detail:
                raise ProviderAuthError("Claude CLI is not signed in; run `claude` and /login")
            if "model" in detail and ("not found" in detail or "invalid" in detail):
                raise ModelNotFoundError(f"Claude model {model!r} not found")
            raise ProviderUnavailableError("Claude CLI returned an error")

        structured = reply.get("structured_output")
        if isinstance(structured, dict):
            return structured
        return parse_json_object(reply.get("result"))

    async def health_check(self) -> ProviderHealth:
        return await probe_health(self)
