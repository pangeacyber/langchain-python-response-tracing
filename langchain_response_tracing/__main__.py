from __future__ import annotations

from typing import Any, override

import click
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from langchain_response_tracing.tracers import PangeaAuditCallbackHandler


class SecretStrParamType(click.ParamType):
    name = "secret"

    @override
    def convert(self, value: Any, param: click.Parameter | None = None, ctx: click.Context | None = None) -> SecretStr:
        if isinstance(value, SecretStr):
            return value

        return SecretStr(value)


SECRET_STR = SecretStrParamType()


@click.command()
@click.option("--model", default="gpt-4o-mini", show_default=True, required=True, help="OpenAI model.")
@click.option(
    "--audit-token",
    envvar="PANGEA_AUDIT_TOKEN",
    type=SECRET_STR,
    required=True,
    help="Pangea Secure Audit Log API token. May also be set via the `PANGEA_AUDIT_TOKEN` environment variable.",
)
@click.option(
    "--audit-config-id",
    help="Pangea Secure Audit Log configuration ID.",
)
@click.option(
    "--pangea-domain",
    envvar="PANGEA_DOMAIN",
    default="aws.us.pangea.cloud",
    show_default=True,
    required=True,
    help="Pangea API domain. May also be set via the `PANGEA_DOMAIN` environment variable.",
)
@click.option(
    "--openai-api-key",
    envvar="OPENAI_API_KEY",
    type=SECRET_STR,
    required=True,
    help="OpenAI API key. May also be set via the `OPENAI_API_KEY` environment variable.",
)
@click.argument("prompt")
def main(
    *,
    prompt: str,
    audit_token: SecretStr,
    audit_config_id: str | None = None,
    pangea_domain: str,
    model: str,
    openai_api_key: SecretStr,
) -> None:
    audit_callback = PangeaAuditCallbackHandler(token=audit_token, domain=pangea_domain, config_id=audit_config_id)
    chain = (
        ChatPromptTemplate.from_messages([("user", "{input}")])
        | ChatOpenAI(model=model, api_key=openai_api_key, callbacks=[audit_callback])
        | StrOutputParser()
    )
    click.echo(chain.invoke({"input": prompt}))


if __name__ == "__main__":
    main()
