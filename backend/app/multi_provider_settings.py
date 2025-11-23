import os
from typing import Dict, Optional, Any
from llama_index.core.settings import Settings
from llama_index.core.llms import LLM
from llama_index.core.embeddings import BaseEmbedding
from app.services.provider_service import provider_service


class MultiProviderSettings:
    """Multi-provider settings manager that supports all 10 AI providers simultaneously."""
    
    def __init__(self):
        self.providers = {}
        self.provider_configs = {}
        self.current_provider = os.getenv("DEFAULT_PROVIDER", "openai")
        self._init_providers()
    
    async def _load_provider_configs(self):
        """Load provider configurations from database."""
        try:
            from app.services.provider_service import provider_service
            configs = await provider_service.get_all_provider_configs()
            for config in configs:
                if config.enabled:
                    try:
                        self.providers[config.id] = self._init_provider_from_config(config.id, config.dict())
                        print(f"✅ Loaded provider: {config.name} ({config.provider_type})")
                    except Exception as e:
                        print(f"❌ Failed to initialize {config.name}: {e}")
        except Exception as e:
            print(f"Warning: Failed to load provider configs from database: {e}")
            # Fallback to environment-based initialization
            self._init_from_env()

    def _init_from_env(self):
        """Initialize providers from environment variables (fallback)."""
        # Initialize OpenRouter first (primary provider)
        if os.getenv("ENABLE_OPENROUTER", "true").lower() == "true":
            try:
                self.providers["openrouter"] = self._init_openrouter()
                print("✅ OpenRouter initialized successfully (primary provider)")
            except Exception as e:
                print(f"❌ Warning: Failed to initialize OpenRouter: {e}")
        
        # Initialize Gemini if enabled
        if os.getenv("ENABLE_GEMINI", "false").lower() == "true":
            try:
                self.providers["gemini"] = self._init_gemini()
                print("✅ Gemini initialized successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini: {e}")
        
        # Initialize OpenAI if enabled (fallback)
        if os.getenv("ENABLE_OPENAI", "false").lower() == "true":
            try:
                self.providers["openai"] = self._init_openai()
                print("✅ OpenAI initialized successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI: {e}")

    def _init_providers(self):
        """Initialize all available providers based on configurations."""
        # For now, use environment-based initialization
        # Database-based initialization will be handled by API endpoints
        self._init_from_env()
        
        # Set the current provider
        if self.current_provider in self.providers:
            self.set_provider(self.current_provider)
        elif self.providers:
            # Fallback to first available provider
            self.set_provider(list(self.providers.keys())[0])
        else:
            raise ValueError("No providers are enabled. Please enable at least one provider.")
    
    def _init_openai(self) -> Dict[str, any]:
        """Initialize OpenAI provider."""
        from llama_index.core.constants import DEFAULT_TEMPERATURE
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
        
        max_tokens = os.getenv("LLM_MAX_TOKENS")
        config = {
            "model": os.getenv("MODEL", "gpt-4o-mini"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)),
            "max_tokens": int(max_tokens) if max_tokens is not None else None,
        }
        llm = OpenAI(**config)
        
        dimensions = os.getenv("EMBEDDING_DIM")
        embed_config = {
            "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            "dimensions": int(dimensions) if dimensions is not None else None,
        }
        embed_model = OpenAIEmbedding(**embed_config)
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": "OpenAI",
            "model": os.getenv("MODEL", "gpt-4o-mini"),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        }
    
    def _init_gemini(self) -> Dict[str, any]:
        """Initialize Gemini provider."""
        from llama_index.embeddings.gemini import GeminiEmbedding
        from llama_index.llms.gemini import Gemini
        
        model_name = f"models/{os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')}"
        embed_model_name = f"models/{os.getenv('GEMINI_EMBEDDING_MODEL', 'text-embedding-004')}"
        
        llm = Gemini(model=model_name)
        embed_model = GeminiEmbedding(model_name=embed_model_name)
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": "Google Gemini",
            "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "embedding_model": os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
        }
    
    def _init_openrouter(self) -> Dict[str, any]:
        """Initialize OpenRouter provider from environment variables."""
        from app.llms.openrouter_llm import OpenRouterLLM
        from llama_index.embeddings.openai import OpenAIEmbedding
        
        # Get configuration from environment
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
        embedding_model = os.getenv("OPENROUTER_EMBEDDING_MODEL", "text-embedding-3-small")
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        # Initialize custom OpenRouter LLM
        llm = OpenRouterLLM(
            model=model,
            api_key=api_key,
            api_base="https://openrouter.ai/api/v1",
            max_tokens=4096,
            context_window=4096,
            temperature=0.7,
            provider_order=["x-ai", "openai", "anthropic", "google"]
        )
        
        # OpenRouter doesn't support embeddings API, use HuggingFace for law-ai/InLegalBERT
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        embed_model = HuggingFaceEmbedding(
            model_name="law-ai/InLegalBERT"
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": "OpenRouter",
            "model": model,
            "embedding_model": "law-ai/InLegalBERT"
        }

    def _init_provider_from_config(self, provider_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize provider from database configuration."""
        provider_type = config.get("provider_type")
        
        if provider_type == "openai":
            return self._init_openai_from_config(config)
        elif provider_type == "gemini":
            return self._init_gemini_from_config(config)
        elif provider_type == "anthropic":
            return self._init_anthropic_from_config(config)
        elif provider_type == "groq":
            return self._init_groq_from_config(config)
        elif provider_type == "ollama":
            return self._init_ollama_from_config(config)
        elif provider_type == "mistral":
            return self._init_mistral_from_config(config)
        elif provider_type == "azure-openai":
            return self._init_azure_openai_from_config(config)
        elif provider_type == "t-systems":
            return self._init_t_systems_from_config(config)
        elif provider_type == "fastembed":
            return self._init_fastembed_from_config(config)
        elif provider_type == "openrouter":
            return self._init_openrouter_from_config(config)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    def _init_openai_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize OpenAI provider from config."""
        from llama_index.core.constants import DEFAULT_TEMPERATURE
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
        
        llm_config = {
            "model": config.get("model", "gpt-4o-mini"),
            "temperature": config.get("temperature", DEFAULT_TEMPERATURE),
            "max_tokens": config.get("max_tokens"),
            "api_key": config.get("api_key")
        }
        llm = OpenAI(**{k: v for k, v in llm_config.items() if v is not None})
        
        embed_config = {
            "model": config.get("embedding_model", "text-embedding-3-small"),
            "dimensions": config.get("dimensions"),
            "api_key": config.get("api_key")
        }
        embed_model = OpenAIEmbedding(**{k: v for k, v in embed_config.items() if v is not None})
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "OpenAI"),
            "model": config.get("model", "gpt-4o-mini"),
            "embedding_model": config.get("embedding_model", "text-embedding-3-small")
        }

    def _init_gemini_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Gemini provider from config."""
        from llama_index.embeddings.gemini import GeminiEmbedding
        from llama_index.llms.gemini import Gemini
        
        model_name = f"models/{config.get('model', 'gemini-1.5-flash')}"
        embed_model_name = f"models/{config.get('embedding_model', 'text-embedding-004')}"
        
        llm = Gemini(model=model_name, api_key=config.get("api_key"))
        embed_model = GeminiEmbedding(model_name=embed_model_name, api_key=config.get("api_key"))
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "Google Gemini"),
            "model": config.get("model", "gemini-1.5-flash"),
            "embedding_model": config.get("embedding_model", "text-embedding-004")
        }

    def _init_anthropic_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Anthropic provider from config."""
        from llama_index.llms.anthropic import Anthropic
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
        
        llm = Anthropic(
            model=config.get("model", "claude-3-sonnet-20240229"),
            api_key=config.get("api_key")
        )
        embed_model = FastEmbedEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "Anthropic Claude"),
            "model": config.get("model", "claude-3-sonnet-20240229"),
            "embedding_model": "fastembed-all-MiniLM-L6-v2"
        }

    def _init_groq_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Groq provider from config."""
        from llama_index.llms.groq import Groq
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
        
        llm = Groq(
            model=config.get("model", "llama3-8b-8192"),
            api_key=config.get("api_key")
        )
        embed_model = FastEmbedEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "Groq"),
            "model": config.get("model", "llama3-8b-8192"),
            "embedding_model": "fastembed-all-MiniLM-L6-v2"
        }

    def _init_ollama_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Ollama provider from config."""
        from llama_index.llms.ollama.base import Ollama
        from llama_index.embeddings.ollama import OllamaEmbedding
        
        llm = Ollama(
            model=config.get("model", "llama2"),
            base_url=config.get("base_url", "http://127.0.0.1:11434")
        )
        embed_model = OllamaEmbedding(
            model_name=config.get("embedding_model", "nomic-embed-text"),
            base_url=config.get("base_url", "http://127.0.0.1:11434")
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "Ollama"),
            "model": config.get("model", "llama2"),
            "embedding_model": config.get("embedding_model", "nomic-embed-text")
        }

    def _init_mistral_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Mistral provider from config."""
        from llama_index.llms.mistralai import MistralAI
        from llama_index.embeddings.mistralai import MistralAIEmbedding
        
        llm = MistralAI(
            model=config.get("model", "mistral-small"),
            api_key=config.get("api_key")
        )
        embed_model = MistralAIEmbedding(
            model_name=config.get("embedding_model", "mistral-embed"),
            api_key=config.get("api_key")
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "Mistral AI"),
            "model": config.get("model", "mistral-small"),
            "embedding_model": config.get("embedding_model", "mistral-embed")
        }

    def _init_azure_openai_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Azure OpenAI provider from config."""
        from llama_index.llms.azure_openai import AzureOpenAI
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        
        custom_config = config.get("custom_config", {})
        azure_config = {
            "api_key": config.get("api_key"),
            "azure_endpoint": config.get("base_url"),
            "api_version": custom_config.get("api_version", "2024-02-15-preview")
        }
        
        llm = AzureOpenAI(
            model=config.get("model"),
            deployment_name=custom_config.get("deployment_name"),
            **azure_config
        )
        embed_model = AzureOpenAIEmbedding(
            model=config.get("embedding_model"),
            deployment_name=custom_config.get("embedding_deployment_name"),
            **azure_config
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "Azure OpenAI"),
            "model": config.get("model"),
            "embedding_model": config.get("embedding_model")
        }

    def _init_t_systems_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize T-Systems provider from config."""
        from llama_index.llms.openai_like import OpenAILike
        from app.llmhub import TSIEmbedding
        
        llm = OpenAILike(
            model=config.get("model"),
            api_key=config.get("api_key"),
            api_base=config.get("base_url"),
            is_chat_model=True,
            is_function_calling_model=False,
            context_window=4096
        )
        embed_model = TSIEmbedding(
            model_name=config.get("embedding_model", "text-embedding-3-large"),
            api_key=config.get("api_key"),
            api_base=config.get("base_url")
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "T-Systems LLM Hub"),
            "model": config.get("model"),
            "embedding_model": config.get("embedding_model", "text-embedding-3-large")
        }

    def _init_fastembed_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize FastEmbed provider from config."""
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
        from llama_index.llms.ollama.base import Ollama  # Use Ollama as default LLM for FastEmbed
        
        embed_model = FastEmbedEmbedding(
            model_name=config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        )
        llm = Ollama(
            model=config.get("model", "llama2"),
            base_url=config.get("base_url", "http://127.0.0.1:11434")
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "FastEmbed"),
            "model": config.get("model", "llama2"),
            "embedding_model": config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        }
    
    def _init_openrouter_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize OpenRouter provider from config."""
        from app.llms.openrouter_llm import OpenRouterLLM
        from llama_index.embeddings.fastembed import FastEmbedEmbedding
        
        # Initialize custom OpenRouter LLM
        llm = OpenRouterLLM(
            model=config.get("model", "anthropic/claude-sonnet-4"),
            api_key=config.get("api_key"),
            api_base="https://openrouter.ai/api/v1",
            max_tokens=config.get("max_tokens", 4096),
            context_window=config.get("context_window", 4096),
            temperature=config.get("temperature", 0.7),
            provider_order=config.get("provider_order", ["x-ai", "openai", "anthropic", "google"])
        )
        
        # OpenRouter doesn't support embeddings API, use FastEmbed instead
        embed_model = FastEmbedEmbedding(
            model_name="BAAI/bge-small-en-v1.5"
        )
        
        return {
            "llm": llm,
            "embed_model": embed_model,
            "name": config.get("name", "OpenRouter"),
            "model": config.get("model", "anthropic/claude-sonnet-4"),
            "embedding_model": "law-ai/InLegalBERT"
        }
    
    def set_provider(self, provider_name: str):
        """Set the active provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available. Available: {list(self.providers.keys())}")
        
        self.current_provider = provider_name
        provider = self.providers[provider_name]
        
        # Update global settings
        Settings.llm = provider["llm"]
        Settings.embed_model = provider["embed_model"]
        
        print(f"✅ Switched to provider: {provider['name']} ({provider_name})")
        print(f"   LLM Model: {provider['model']}")
        print(f"   Embedding Model: {provider['embedding_model']}")
        
        # Set chunk settings
        Settings.chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
        Settings.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "20"))
        
        # Clear index cache to force recreation with new embedding model
        try:
            from app.api.chat.engine.index import clear_provider_cache
            clear_provider_cache()  # Clear all caches when switching providers
            print(f"🔄 Cleared index cache for provider switch")
        except Exception as e:
            print(f"Warning: Failed to clear index cache: {e}")
    
    def get_current_provider(self) -> str:
        """Get the current active provider name."""
        return self.current_provider
    
    def get_available_providers(self) -> Dict[str, Dict[str, any]]:
        """Get all available providers with their metadata."""
        return {
            name: {
                "name": provider["name"],
                "model": provider["model"],
                "embedding_model": provider["embedding_model"],
                "active": name == self.current_provider
            }
            for name, provider in self.providers.items()
        }
    
    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, any]]:
        """Get information about a specific provider."""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            return {
                "name": provider["name"],
                "model": provider["model"],
                "embedding_model": provider["embedding_model"],
                "active": provider_name == self.current_provider
            }
        return None


# Global instance (initialized lazily)
multi_provider_settings = None


def _get_multi_provider_settings():
    """Get or create multi-provider settings instance."""
    global multi_provider_settings
    if multi_provider_settings is None:
        multi_provider_settings = MultiProviderSettings()
    return multi_provider_settings


def init_multi_provider_settings():
    """Initialize multi-provider settings."""
    return _get_multi_provider_settings()


def get_current_provider() -> str:
    """Get the current active provider."""
    # Check if multi-provider is enabled
    if os.getenv("ENABLE_MULTI_PROVIDER", "false").lower() != "true":
        return None  # Single-provider mode
    return _get_multi_provider_settings().get_current_provider()


def set_provider(provider_name: str):
    """Set the active provider."""
    _get_multi_provider_settings().set_provider(provider_name)

def reload_providers_from_db():
    """Reload providers from database configuration."""
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(multi_provider_settings._load_provider_configs())
        loop.close()
        return True
    except Exception as e:
        print(f"Error reloading providers: {e}")
        return False


def get_available_providers() -> Dict[str, Dict[str, any]]:
    """Get all available providers."""
    if os.getenv("ENABLE_MULTI_PROVIDER", "false").lower() != "true":
        return {}  # Single-provider mode
    return _get_multi_provider_settings().get_available_providers()
