from __future__ import annotations

from typing import Optional

# Placeholder for Semantic Kernel setup; will be implemented later.


class KernelService:
    """Set up and manage a Semantic Kernel instance.

    For the initial scaffold, this is a placeholder. Implementation will
    initialize SK with Azure OpenAI chat completion connector.
    """

    def __init__(self) -> None:
        self._kernel: Optional[object] = None

    def get_kernel(self) -> object:
        if self._kernel is None:
            # TODO: Initialize Semantic Kernel with Azure OpenAI
            self._kernel = object()
        return self._kernel
