"""AI Provider abstraction layer for provider-agnostic AI operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.features.intelligence.models import (
    AICategory,
    AIMerchant,
    AIProviderType,
    AIRequest,
    AIResponse,
    SanitizedContext,
)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def categorize(
        self,
        context: SanitizedContext,
        existing_categories: list[str],
    ) -> AICategory:
        """Suggest a category for a transaction.
        
        Args:
            context: Sanitized transaction context
            existing_categories: List of valid categories
            
        Returns:
            AICategory with suggestion and confidence
        """
        pass

    @abstractmethod
    async def suggest_merchant(
        self,
        context: SanitizedContext,
    ) -> AIMerchant:
        """Suggest a canonical merchant name.
        
        Args:
            context: Sanitized transaction context
            
        Returns:
            AIMerchant with suggestion and confidence
        """
        pass

    @abstractmethod
    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict],
        context_data: dict[str, Any],
    ) -> str:
        """Generate a chat response about financial data.
        
        Args:
            user_message: User's question
            conversation_history: Prior messages in format [{"role": "...", "content": "..."}]
            context_data: Sanitized financial context for the query
            
        Returns:
            Assistant's response
        """
        pass

    @abstractmethod
    async def generate_insight_text(
        self,
        insight_data: dict[str, Any],
    ) -> str:
        """Generate natural language text for an insight.
        
        Args:
            insight_data: Structured insight data
            
        Returns:
            Natural language description
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
        """
        self.api_key = api_key
        self.model = model
        self._available = bool(api_key)

    async def categorize(
        self,
        context: SanitizedContext,
        existing_categories: list[str],
    ) -> AICategory:
        """Suggest a category using OpenAI."""
        # Implementation will be added in subsequent commits
        # This is the interface definition
        raise NotImplementedError("OpenAI integration coming in next milestone")

    async def suggest_merchant(
        self,
        context: SanitizedContext,
    ) -> AIMerchant:
        """Suggest a merchant using OpenAI."""
        raise NotImplementedError("OpenAI integration coming in next milestone")

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict],
        context_data: dict[str, Any],
    ) -> str:
        """Generate chat response using OpenAI."""
        raise NotImplementedError("OpenAI integration coming in next milestone")

    async def generate_insight_text(
        self,
        insight_data: dict[str, Any],
    ) -> str:
        """Generate insight text using OpenAI."""
        raise NotImplementedError("OpenAI integration coming in next milestone")

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self._available


class GeminiProvider(AIProvider):
    """Google Gemini API provider implementation."""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            model: Model name (default: gemini-pro)
        """
        self.api_key = api_key
        self.model = model
        self._available = bool(api_key)

    async def categorize(
        self,
        context: SanitizedContext,
        existing_categories: list[str],
    ) -> AICategory:
        """Suggest a category using Gemini."""
        raise NotImplementedError("Gemini integration coming in next milestone")

    async def suggest_merchant(
        self,
        context: SanitizedContext,
    ) -> AIMerchant:
        """Suggest a merchant using Gemini."""
        raise NotImplementedError("Gemini integration coming in next milestone")

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict],
        context_data: dict[str, Any],
    ) -> str:
        """Generate chat response using Gemini."""
        raise NotImplementedError("Gemini integration coming in next milestone")

    async def generate_insight_text(
        self,
        insight_data: dict[str, Any],
    ) -> str:
        """Generate insight text using Gemini."""
        raise NotImplementedError("Gemini integration coming in next milestone")

    def is_available(self) -> bool:
        """Check if Gemini is available."""
        return self._available


class OllamaProvider(AIProvider):
    """Local Ollama provider for privacy-first on-device AI."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral"):
        """Initialize Ollama provider.
        
        Args:
            base_url: Ollama API base URL (default: localhost:11434)
            model: Model name (default: mistral)
        """
        self.base_url = base_url
        self.model = model
        self._available = False  # Will check connectivity in is_available()

    async def categorize(
        self,
        context: SanitizedContext,
        existing_categories: list[str],
    ) -> AICategory:
        """Suggest a category using Ollama."""
        raise NotImplementedError("Ollama integration coming in next milestone")

    async def suggest_merchant(
        self,
        context: SanitizedContext,
    ) -> AIMerchant:
        """Suggest a merchant using Ollama."""
        raise NotImplementedError("Ollama integration coming in next milestone")

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict],
        context_data: dict[str, Any],
    ) -> str:
        """Generate chat response using Ollama."""
        raise NotImplementedError("Ollama integration coming in next milestone")

    async def generate_insight_text(
        self,
        insight_data: dict[str, Any],
    ) -> str:
        """Generate insight text using Ollama."""
        raise NotImplementedError("Ollama integration coming in next milestone")

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        # TODO: Implement connectivity check
        return self._available


class MockAIProvider(AIProvider):
    """Mock provider for testing and development."""

    def __init__(self):
        """Initialize mock provider."""
        self._available = True

    async def categorize(
        self,
        context: SanitizedContext,
        existing_categories: list[str],
    ) -> AICategory:
        """Return mock category suggestion."""
        from backend.app.features.intelligence.models import ConfidenceLevel
        
        return AICategory(
            category=existing_categories[0] if existing_categories else "Other",
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            reasoning="Mock suggestion",
        )

    async def suggest_merchant(
        self,
        context: SanitizedContext,
    ) -> AIMerchant:
        """Return mock merchant suggestion."""
        from backend.app.features.intelligence.models import ConfidenceLevel
        
        return AIMerchant(
            merchant=context.merchant,
            confidence=0.90,
            confidence_level=ConfidenceLevel.HIGH,
            reasoning="Mock suggestion",
        )

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict],
        context_data: dict[str, Any],
    ) -> str:
        """Return mock chat response."""
        return "Mock response to your question about your finances."

    async def generate_insight_text(
        self,
        insight_data: dict[str, Any],
    ) -> str:
        """Return mock insight text."""
        return "Your spending has been stable this month."

    def is_available(self) -> bool:
        """Mock provider is always available."""
        return self._available


class AIProviderFactory:
    """Factory for creating AI provider instances."""

    @staticmethod
    def create(
        provider_type: AIProviderType | str,
        **kwargs,
    ) -> AIProvider:
        """Create an AI provider instance.
        
        Args:
            provider_type: Type of provider to create
            **kwargs: Provider-specific configuration
            
        Returns:
            AIProvider instance
            
        Raises:
            ValueError: If provider type is unknown
        """
        if isinstance(provider_type, str):
            provider_type = AIProviderType(provider_type.lower())

        if provider_type == AIProviderType.OPENAI:
            api_key = kwargs.get("api_key")
            model = kwargs.get("model", "gpt-4")
            if not api_key:
                raise ValueError("OpenAI provider requires 'api_key'")
            return OpenAIProvider(api_key=api_key, model=model)

        if provider_type == AIProviderType.GEMINI:
            api_key = kwargs.get("api_key")
            model = kwargs.get("model", "gemini-pro")
            if not api_key:
                raise ValueError("Gemini provider requires 'api_key'")
            return GeminiProvider(api_key=api_key, model=model)

        if provider_type == AIProviderType.OLLAMA:
            base_url = kwargs.get("base_url", "http://localhost:11434")
            model = kwargs.get("model", "mistral")
            return OllamaProvider(base_url=base_url, model=model)

        raise ValueError(f"Unknown provider type: {provider_type}")
