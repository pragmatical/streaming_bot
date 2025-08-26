from __future__ import annotations

from typing import Optional

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from ..config.settings import settings


SYSTEM_PROMPT = (
    "You are a helpful assistant. Keep responses concise and stream updates as they are available."
)


class KernelService:
    """Set up and manage a Semantic Kernel instance for chat with Azure OpenAI."""

    def __init__(self) -> None:
        self._kernel: Optional[sk.Kernel] = None

    def get_kernel(self) -> sk.Kernel:
        if self._kernel is None:
            kernel = sk.Kernel()

            if not (
                settings.azure_openai_api_key
                and settings.azure_openai_endpoint
                and settings.azure_openai_deployment
            ):
                # Create kernel anyway; attempts to use it will fail with a clear message
                self._kernel = kernel
                return kernel

            service_id = "azure-openai-chat"
            chat_service = AzureChatCompletion(
                service_id=service_id,
                deployment_name=settings.azure_openai_deployment,
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )

            kernel.add_service(chat_service)
            self._kernel = kernel
        return self._kernel
