from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import asyncio
import time

# Import schemas directly to avoid circular imports
from pydantic import BaseModel, Field
from enum import Enum

class ProviderType(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OLLAMA = "ollama"
    MISTRAL = "mistral"
    AZURE_OPENAI = "azure-openai"
    T_SYSTEMS = "t-systems"
    FASTEMBED = "fastembed"
    OPENROUTER = "openrouter"

class ProviderConfigCreate(BaseModel):
    name: str = Field(..., description="Display name for the provider")
    provider_type: ProviderType = Field(..., description="Type of provider")
    enabled: bool = Field(default=False, description="Whether provider is enabled")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Custom base URL for the provider")
    model: str = Field(..., description="LLM model name")
    embedding_model: str = Field(..., description="Embedding model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for the model")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens for the model")
    dimensions: Optional[int] = Field(None, ge=1, description="Embedding dimensions")
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration options")

class ProviderConfigUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    embedding_model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    dimensions: Optional[int] = Field(None, ge=1)
    custom_config: Optional[Dict[str, Any]] = None

class ProviderConfigOut(BaseModel):
    id: str = Field(..., description="Unique identifier for the provider config")
    name: str = Field(..., description="Display name for the provider")
    provider_type: str = Field(..., description="Type of provider")
    enabled: bool = Field(default=False, description="Whether provider is enabled")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Custom base URL for the provider")
    model: str = Field(..., description="LLM model name")
    embedding_model: str = Field(..., description="Embedding model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for the model")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens for the model")
    dimensions: Optional[int] = Field(None, ge=1, description="Embedding dimensions")
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration options")
    status: str = Field(..., description="Status of the provider (active, inactive, error)")
    last_tested: Optional[str] = Field(None, description="Last time the provider was tested")
    error_message: Optional[str] = Field(None, description="Last error message if any")

class ProviderTestResponse(BaseModel):
    success: bool
    message: str
    llm_test: Optional[bool] = None
    embedding_test: Optional[bool] = None
    response_time: Optional[float] = None

class ProviderStatus(BaseModel):
    id: str
    name: str
    provider_type: str
    enabled: bool
    status: str
    model: str
    embedding_model: str
    last_tested: Optional[str] = None
    error_message: Optional[str] = None

class ProviderService:
    @property
    def provider_collection(self):
        from app.db import async_mongodb
        return async_mongodb.db.provider_configs

    async def create_provider_config(self, config: ProviderConfigCreate) -> ProviderConfigOut:
        """Create a new provider configuration."""
        provider_id = str(uuid.uuid4())
        config_dict = config.dict()
        config_dict["id"] = provider_id
        config_dict["status"] = "inactive"
        config_dict["last_tested"] = None
        config_dict["error_message"] = None
        
        await self.provider_collection.insert_one(config_dict)
        return ProviderConfigOut(**config_dict)

    async def get_provider_config(self, provider_id: str) -> Optional[ProviderConfigOut]:
        """Get a provider configuration by ID."""
        config = await self.provider_collection.find_one({"id": provider_id})
        if config:
            return ProviderConfigOut(**config)
        return None

    async def get_all_provider_configs(self) -> List[ProviderConfigOut]:
        """Get all provider configurations."""
        configs = await self.provider_collection.find().to_list(length=None)
        return [ProviderConfigOut(**config) for config in configs]

    async def update_provider_config(self, provider_id: str, update: ProviderConfigUpdate) -> Optional[ProviderConfigOut]:
        """Update a provider configuration."""
        update_dict = {k: v for k, v in update.dict().items() if v is not None}
        if not update_dict:
            return await self.get_provider_config(provider_id)
        
        result = await self.provider_collection.update_one(
            {"id": provider_id}, 
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return await self.get_provider_config(provider_id)
        return None

    async def delete_provider_config(self, provider_id: str) -> bool:
        """Delete a provider configuration."""
        result = await self.provider_collection.delete_one({"id": provider_id})
        return result.deleted_count > 0

    async def get_provider_statuses(self) -> List[ProviderStatus]:
        """Get status of all providers."""
        configs = await self.get_all_provider_configs()
        return [
            ProviderStatus(
                id=config.id,
                name=config.name,
                provider_type=config.provider_type.value,
                enabled=config.enabled,
                status=config.status,
                model=config.model,
                embedding_model=config.embedding_model,
                last_tested=config.last_tested,
                error_message=config.error_message
            )
            for config in configs
        ]

    async def test_provider_connection(self, provider_id: str, test_config: Optional[Dict] = None) -> ProviderTestResponse:
        """Test a provider connection."""
        config = await self.get_provider_config(provider_id)
        if not config:
            return ProviderTestResponse(success=False, message="Provider configuration not found")
        
        # Use test config if provided, otherwise use stored config
        test_data = test_config or config.dict()
        
        try:
            start_time = time.time()
            
            # Test LLM connection
            llm_test = await self._test_llm_connection(test_data)
            
            # Test embedding connection
            embedding_test = await self._test_embedding_connection(test_data)
            
            response_time = time.time() - start_time
            
            success = llm_test and embedding_test
            message = "Connection test successful" if success else "Connection test failed"
            
            # Update last tested time
            await self.provider_collection.update_one(
                {"id": provider_id},
                {
                    "$set": {
                        "last_tested": datetime.utcnow().isoformat(),
                        "status": "active" if success else "error",
                        "error_message": None if success else "Connection test failed"
                    }
                }
            )
            
            return ProviderTestResponse(
                success=success,
                message=message,
                llm_test=llm_test,
                embedding_test=embedding_test,
                response_time=response_time
            )
            
        except Exception as e:
            # Update error status
            await self.provider_collection.update_one(
                {"id": provider_id},
                {
                    "$set": {
                        "last_tested": datetime.utcnow().isoformat(),
                        "status": "error",
                        "error_message": str(e)
                    }
                }
            )
            
            return ProviderTestResponse(
                success=False,
                message=f"Connection test failed: {str(e)}"
            )

    async def _test_llm_connection(self, config: Dict) -> bool:
        """Test LLM connection for a provider."""
        try:
            import asyncio
            
            # Create a temporary LLM instance for testing
            llm = self._create_llm_instance(config)
            if llm:
                # Simple test query
                response = await llm.acomplete("Hello")
                return response is not None
            return False
        except Exception:
            return False

    async def _test_embedding_connection(self, config: Dict) -> bool:
        """Test embedding connection for a provider."""
        try:
            # Create a temporary embedding instance for testing
            embed_model = self._create_embedding_instance(config)
            if embed_model:
                # Simple test embedding
                response = await embed_model.aget_text_embedding("Hello")
                return response is not None and len(response) > 0
            return False
        except Exception:
            return False

    def _create_llm_instance(self, config: Dict):
        """Create LLM instance based on provider type."""
        provider_type = config.get("provider_type")
        
        if provider_type == "openai":
            from llama_index.llms.openai import OpenAI
            return OpenAI(
                model=config.get("model", "gpt-3.5-turbo"),
                api_key=config.get("api_key"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens")
            )
        elif provider_type == "gemini":
            from llama_index.llms.gemini import Gemini
            return Gemini(
                model=f"models/{config.get('model', 'gemini-1.5-flash')}",
                api_key=config.get("api_key")
            )
        elif provider_type == "anthropic":
            from llama_index.llms.anthropic import Anthropic
            return Anthropic(
                model=config.get("model", "claude-3-sonnet-20240229"),
                api_key=config.get("api_key")
            )
        elif provider_type == "groq":
            from llama_index.llms.groq import Groq
            return Groq(
                model=config.get("model", "llama3-8b-8192"),
                api_key=config.get("api_key")
            )
        elif provider_type == "ollama":
            from llama_index.llms.ollama.base import Ollama
            return Ollama(
                model=config.get("model", "llama2"),
                base_url=config.get("base_url", "http://127.0.0.1:11434")
            )
        elif provider_type == "mistral":
            from llama_index.llms.mistralai import MistralAI
            return MistralAI(
                model=config.get("model", "mistral-small"),
                api_key=config.get("api_key")
            )
        elif provider_type == "azure-openai":
            from llama_index.llms.azure_openai import AzureOpenAI
            return AzureOpenAI(
                model=config.get("model"),
                api_key=config.get("api_key"),
                azure_endpoint=config.get("base_url"),
                api_version=config.get("custom_config", {}).get("api_version", "2024-02-15-preview"),
                deployment_name=config.get("custom_config", {}).get("deployment_name")
            )
        elif provider_type == "t-systems":
            from llama_index.llms.openai_like import OpenAILike
            return OpenAILike(
                model=config.get("model"),
                api_key=config.get("api_key"),
                api_base=config.get("base_url"),
                is_chat_model=True,
                is_function_calling_model=False,
                context_window=4096
            )
        elif provider_type == "openrouter":
            from llama_index.llms.openai import OpenAI
            return OpenAI(
                model=config.get("model"),
                api_key=config.get("api_key"),
                api_base="https://openrouter.ai/api/v1"
            )
        return None

    def _create_embedding_instance(self, config: Dict):
        """Create embedding instance based on provider type."""
        provider_type = config.get("provider_type")
        
        if provider_type == "openai":
            from llama_index.embeddings.openai import OpenAIEmbedding
            return OpenAIEmbedding(
                model=config.get("embedding_model", "text-embedding-3-small"),
                api_key=config.get("api_key"),
                dimensions=config.get("dimensions")
            )
        elif provider_type == "gemini":
            from llama_index.embeddings.gemini import GeminiEmbedding
            return GeminiEmbedding(
                model_name=f"models/{config.get('embedding_model', 'text-embedding-004')}",
                api_key=config.get("api_key")
            )
        elif provider_type in ["anthropic", "groq"]:
            # Use FastEmbed for providers without native embeddings
            from llama_index.embeddings.fastembed import FastEmbedEmbedding
            return FastEmbedEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        elif provider_type == "ollama":
            from llama_index.embeddings.ollama import OllamaEmbedding
            return OllamaEmbedding(
                model_name=config.get("embedding_model", "nomic-embed-text"),
                base_url=config.get("base_url", "http://127.0.0.1:11434")
            )
        elif provider_type == "mistral":
            from llama_index.embeddings.mistralai import MistralAIEmbedding
            return MistralAIEmbedding(
                model_name=config.get("embedding_model", "mistral-embed"),
                api_key=config.get("api_key")
            )
        elif provider_type == "azure-openai":
            from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
            return AzureOpenAIEmbedding(
                model=config.get("embedding_model"),
                api_key=config.get("api_key"),
                azure_endpoint=config.get("base_url"),
                api_version=config.get("custom_config", {}).get("api_version", "2024-02-15-preview"),
                deployment_name=config.get("custom_config", {}).get("embedding_deployment_name")
            )
        elif provider_type == "t-systems":
            from app.llmhub import TSIEmbedding
            return TSIEmbedding(
                model_name=config.get("embedding_model", "text-embedding-3-large"),
                api_key=config.get("api_key"),
                api_base=config.get("base_url")
            )
        elif provider_type == "fastembed":
            from llama_index.embeddings.fastembed import FastEmbedEmbedding
            return FastEmbedEmbedding(
                model_name=config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            )
        elif provider_type == "openrouter":
            from llama_index.embeddings.openai import OpenAIEmbedding
            return OpenAIEmbedding(
                model=config.get("embedding_model", "text-embedding-3-small"),
                api_key=config.get("api_key"),
                api_base="https://openrouter.ai/api/v1"
            )
        return None

provider_service = ProviderService()
