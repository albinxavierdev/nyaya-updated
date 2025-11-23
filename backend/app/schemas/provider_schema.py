from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
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

class ProviderConfigBase(BaseModel):
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

class ProviderConfigCreate(ProviderConfigBase):
    pass

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

class ProviderConfigOut(ProviderConfigBase):
    id: str = Field(..., description="Unique identifier for the provider config")
    status: str = Field(..., description="Status of the provider (active, inactive, error)")
    last_tested: Optional[str] = Field(None, description="Last time the provider was tested")
    error_message: Optional[str] = Field(None, description="Last error message if any")

class ProviderTestRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    embedding_model: Optional[str] = None

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

class ProviderListResponse(BaseModel):
    providers: List[ProviderStatus]
    active_provider: Optional[str] = None
    total_count: int
