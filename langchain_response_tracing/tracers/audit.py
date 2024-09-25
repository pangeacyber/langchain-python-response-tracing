from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping
from typing import Any, override

from langchain_core.tracers.base import BaseTracer
from langchain_core.tracers.schemas import Run
from pangea import PangeaConfig
from pangea.services import Audit
from pydantic import SecretStr

__all__ = ["PangeaAuditCallbackHandler"]


class PangeaAuditCallbackHandler(BaseTracer):
    """
    Tracer that creates an event in Pangea's Secure Audit Log when a response is
    generated.
    """

    _client: Audit

    def __init__(
        self,
        *,
        token: SecretStr,
        config_id: str | None = None,
        domain: str = "aws.us.pangea.cloud",
        log_missing_parent: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            token: Pangea Secure Audit Log API token.
            config_id: Pangea Secure Audit Log configuration ID.
            domain: Pangea API domain.
        """

        super().__init__(**kwargs)
        self.log_missing_parent = log_missing_parent
        self._client = Audit(token=token.get_secret_value(), config=PangeaConfig(domain=domain), config_id=config_id)

    @override
    def _persist_run(self, run: Run) -> None:
        pass

    @override
    def _on_llm_end(self, run: Run) -> None:
        if not run.outputs:
            return

        if "generations" not in run.outputs:
            return

        generations: Iterable[Mapping[str, Any]] = itertools.chain.from_iterable(run.outputs["generations"])
        text_generations: list[str] = [x["text"] for x in generations if "text" in x]

        if len(text_generations) == 0:
            return

        self._client.log_bulk(
            [
                {
                    "timestamp": run.start_time,
                    "action": "llm/end",
                    "source": run.name,
                    "message": "Ending LLM.",
                    "new": x,
                }
                for x in text_generations
            ]
        )
