import os
from typing import Dict
from dotenv import load_dotenv

from llama_index.core.settings import Settings

load_dotenv()


def init_settings():
    # OpenAI = main provider; OpenRouter = fallback when OPENAI_API_KEY is not set
    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if openai_key:
        _init_openai()
    elif openrouter_key:
        _init_openrouter()
    else:
        raise ValueError(
            "Set OPENAI_API_KEY (main) or OPENROUTER_API_KEY (fallback)"
        )

    Settings.chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
    Settings.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "20"))


# Canonical base URLs so env cannot override provider choice
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _init_openai():
    from llama_index.core.constants import DEFAULT_TEMPERATURE
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY for OpenAI provider (LLM and embeddings)")

    model = os.getenv("MODEL", "gpt-4o-mini")
    embed_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    max_tokens = os.getenv("LLM_MAX_TOKENS")
    temperature = os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)
    dimensions = os.getenv("EMBEDDING_DIM")

    Settings.llm = OpenAI(
        model=model,
        api_key=api_key,
        api_base=OPENAI_BASE_URL,
        temperature=float(temperature),
        max_tokens=int(max_tokens) if max_tokens else None,
    )
    embed_config = {
        "model": embed_model,
        "api_key": api_key,
        "api_base": OPENAI_BASE_URL,
    }
    if dimensions:
        embed_config["dimensions"] = int(dimensions)
    Settings.embed_model = OpenAIEmbedding(**embed_config)


def _init_openrouter():
    from llama_index.llms.openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENROUTER_API_KEY or OPENAI_API_KEY for OpenRouter")

    model = os.getenv("MODEL", "openai/gpt-oss-120b:free")
    max_tokens = os.getenv("LLM_MAX_TOKENS")
    temperature = os.getenv("LLM_TEMPERATURE", "0.7")

    Settings.llm = OpenAI(
        model=model,
        api_key=api_key,
        api_base=OPENROUTER_BASE_URL,
        max_tokens=int(max_tokens) if max_tokens else None,
        temperature=float(temperature),
    )
    _init_fastembed()


def _init_fastembed():
    from llama_index.embeddings.fastembed import FastEmbedEmbedding

    name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    model_map: Dict[str, str] = {
        "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
        "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    }
    Settings.embed_model = FastEmbedEmbedding(
        model_name=model_map.get(name, "sentence-transformers/all-MiniLM-L6-v2")
    )
