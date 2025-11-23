import os

from grpc import Status
import boto3
import tempfile
import shutil
from dotenv import load_dotenv
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field
from app.core.user import get_current_user
from app.models.user_model import User
from app.services.admin_service import admin_service
from app.schemas.admin_schema import UserOut, UsersOut, MessageOut, ErrorOut
from app.services.config_service import config_service
from app.multi_provider_settings import get_available_providers, get_current_provider, set_provider, reload_providers_from_db
from app.services.provider_service import provider_service, ProviderConfigCreate, ProviderConfigUpdate, ProviderConfigOut, ProviderTestResponse, ProviderStatus
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from app.api.chat.engine.vectordb import get_vector_store
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document
# from phoenix.trace import using_project

admin_router = APIRouter()

load_dotenv()
# AWS configuration

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

# Local storage configuration
DATA_DIR = os.getenv("DATA_DIR", "data")
PRIVATE_STORE_PATH = os.path.join(DATA_DIR)


def get_documents(
    directory: str, recursive: bool = True, filename_as_id: bool = True
) -> List[Document]:
    """
    Load documents from a specified directory using SimpleDirectoryReader.

    Args:
        directory (str): The path to the directory containing the documents.
        recursive (bool, optional): Whether to recursively search for documents in subdirectories. Defaults to True.
        filename_as_id (bool, optional): Whether to use the filename as the document ID. Defaults to True.

    Returns:
        List[Document]: A list of loaded documents.
    """
    reader = SimpleDirectoryReader(
        directory, recursive=recursive, filename_as_id=filename_as_id
    )
    documents = reader.load_data(show_progress=True)
    return documents


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None


def verify_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource",
        )
    return current_user


@admin_router.get(
    "/users", response_model=UsersOut, responses={403: {"model": ErrorOut}}
)
async def get_all_users(admin: User = Depends(verify_admin)) -> UsersOut:
    users = await admin_service.get_all_users()
    return UsersOut(users=[UserOut(**user) for user in users])


@admin_router.get(
    "/users/{user_id}",
    response_model=UserOut,
    responses={403: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
async def get_user(user_id: str, admin: User = Depends(verify_admin)) -> UserOut:
    user = await admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(**user)


@admin_router.put(
    "/users/{user_id}",
    response_model=MessageOut,
    responses={403: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
async def edit_user(
    user_id: str, user_update: UserUpdate, admin: User = Depends(verify_admin)
) -> MessageOut:
    success = await admin_service.edit_user(
        user_id, user_update.model_dump(exclude_unset=True)
    )
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return MessageOut(message="User updated successfully")


@admin_router.delete(
    "/users/{user_id}",
    response_model=MessageOut,
    responses={
        403: {"model": ErrorOut},
        404: {"model": ErrorOut},
        400: {"model": ErrorOut},
    },
)
async def delete_user(user_id: str, admin: User = Depends(verify_admin)) -> MessageOut:
    user = await admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete an admin user")

    success = await admin_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    return MessageOut(message="User deleted successfully")


@admin_router.get("/system-prompt")
async def get_system_prompt(admin: User = Depends(verify_admin)):
    system_prompt = await config_service.get_system_prompt()
    return {"system_prompt": system_prompt}


class SystemPromptUpdate(BaseModel):
    new_prompt: str


@admin_router.put("/system-prompt")
async def update_system_prompt(
    prompt_update: SystemPromptUpdate, admin: User = Depends(verify_admin)
):
    success = await config_service.update_system_prompt(prompt_update.new_prompt)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update system prompt")
    return {"message": "System prompt updated successfully"}


class ConversationStartersUpdate(BaseModel):
    new_starters: List[str] = Field(
        ...,
        description="A list of new conversation starter questions",
        min_items=1,
        example=[
            "What are the key provisions of the Indian Penal Code?",
            "How does bail work in criminal cases?",
            "What are my rights during police interrogation?",
            "Explain the process of filing a civil lawsuit",
        ],
    )


@admin_router.put(
    "/conversation-starters",
    response_model=MessageOut,
    responses={
        200: {
            "model": MessageOut,
            "description": "Conversation starters updated successfully",
        },
        500: {
            "model": ErrorOut,
            "description": "Failed to update conversation starters",
        },
    },
    summary="Update conversation starters",
    description="Update the list of conversation starter questions for the chat interface",
)
async def update_conversation_starters(
    starters_update: ConversationStartersUpdate, admin: User = Depends(verify_admin)
):
    success = await config_service.update_conversation_starters(
        starters_update.new_starters
    )
    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to update conversation starters"
        )
    return MessageOut(message="Conversation starters updated successfully")


@admin_router.post("/upload_data")
async def upload_and_ingest_data(
    file: UploadFile = File(...), admin: User = Depends(verify_admin)
):
    # with using_project("NYAYANTAR-Data-Ingest"):
    try:
        # Check if AWS credentials are available
        use_aws = all(
        [
            AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY,
            AWS_REGION,
            AWS_S3_BUCKET_NAME,
        ]
        )

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        if use_aws:
            # Initialize S3 client
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION,
            )

            # Upload file to S3
            folder_name = "admin_uploads/"
            file_key = f"{folder_name}{file.filename}"
            s3_client.upload_file(tmp_file_path, AWS_S3_BUCKET_NAME, file_key)

            # Generate the file URL
            file_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_key}"
        else:
            # Store file locally
            os.makedirs(PRIVATE_STORE_PATH, exist_ok=True)
            local_file_path = os.path.join(PRIVATE_STORE_PATH, file.filename)
            shutil.move(tmp_file_path, local_file_path)
            file_url = f"/api/files/data/{file.filename}"

        # Ingest file into vector database
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, file.filename)
            shutil.copy(
                local_file_path if not use_aws else tmp_file_path, file_path
            )

            documents = get_documents(temp_dir)

            # Set metadata for all documents
            for doc in documents:
                doc.metadata["private"] = "false"
                doc.metadata["file_id"] = file_key if use_aws else file.filename
                doc.metadata["user_id"] = "admin"
                doc.metadata["url"] = file_url
                doc.metadata["file_path"] = file_url
                doc.metadata["document_id"] = file_url
                doc.metadata["document_id"] = file_url

            vector_store = get_vector_store()

            pipeline = IngestionPipeline(
                transformations=[
                    SentenceSplitter(
                        chunk_size=Settings.chunk_size,
                        chunk_overlap=Settings.chunk_overlap,
                    ),
                    Settings.embed_model,
                ],
                vector_store=vector_store,
            )

            nodes = pipeline.run(documents=documents, show_progress=True)

        return JSONResponse(
            status_code=200,
            content={
                "file_url": file_url,
                "message": f"Ingestion complete. {len(nodes)} nodes inserted.",
                "storage": "S3" if use_aws else "Local",
            },
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# Provider Management Endpoints
@admin_router.get("/providers")
async def get_providers(admin: User = Depends(verify_admin)):
    """Get all available AI providers and their status."""
    try:
        providers = get_available_providers()
        current_provider = get_current_provider()
        return {
            "providers": providers,
            "current_provider": current_provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching providers: {str(e)}")


@admin_router.post("/providers/{provider_name}/switch")
async def switch_provider(provider_name: str, admin: User = Depends(verify_admin)):
    """Switch to a different AI provider."""
    try:
        # First reload providers from database to get latest configs
        reload_success = reload_providers_from_db()
        if not reload_success:
            print("Warning: Failed to reload providers from database")
        
        # Try to switch to the provider
        set_provider(provider_name)
        return {
            "message": f"Successfully switched to {provider_name}",
            "current_provider": provider_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error switching provider: {str(e)}")

@admin_router.post("/providers/switch-to-db")
async def switch_to_database_provider(admin: User = Depends(verify_admin)):
    """Switch to the first enabled provider from database configuration."""
    try:
        # Get all enabled providers from database
        configs = await provider_service.get_all_provider_configs()
        enabled_configs = [config for config in configs if config.enabled]
        
        if not enabled_configs:
            raise HTTPException(status_code=400, detail="No enabled providers found in database")
        
        # Use the first enabled provider
        provider_config = enabled_configs[0]
        
        # Initialize the provider from database config
        from app.multi_provider_settings import multi_provider_settings
        provider_data = multi_provider_settings._init_provider_from_config(provider_config.id, provider_config.dict())
        
        # Add to providers and set as current
        multi_provider_settings.providers[provider_config.id] = provider_data
        multi_provider_settings.set_provider(provider_config.id)
        
        # Clear any existing index cache to ensure fresh index creation
        try:
            from app.api.chat.engine.index import clear_provider_cache
            clear_provider_cache()
        except Exception as e:
            print(f"Warning: Failed to clear index cache: {e}")
        
        return {
            "message": f"Successfully switched to {provider_config.name} from database",
            "current_provider": provider_config.id,
            "provider_info": {
                "name": provider_config.name,
                "type": provider_config.provider_type,
                "model": provider_config.model,
                "embedding_model": provider_config.embedding_model
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error switching to database provider: {str(e)}")


@admin_router.get("/providers/current")
async def get_current_provider_info(admin: User = Depends(verify_admin)):
    """Get information about the current active provider."""
    try:
        current_provider = get_current_provider()
        providers = get_available_providers()
        return {
            "current_provider": current_provider,
            "provider_info": providers.get(current_provider, {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching current provider: {str(e)}")


# Provider Configuration Management Endpoints
@admin_router.get("/providers/configs", response_model=List[ProviderConfigOut])
async def get_provider_configs(admin: User = Depends(verify_admin)):
    """Get all provider configurations."""
    try:
        configs = await provider_service.get_all_provider_configs()
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching provider configs: {str(e)}")

@admin_router.post("/providers/configs", response_model=ProviderConfigOut)
async def create_provider_config(
    config: ProviderConfigCreate, 
    admin: User = Depends(verify_admin)
):
    """Create a new provider configuration."""
    try:
        new_config = await provider_service.create_provider_config(config)
        return new_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating provider config: {str(e)}")

@admin_router.get("/providers/configs/{provider_id}", response_model=ProviderConfigOut)
async def get_provider_config(provider_id: str, admin: User = Depends(verify_admin)):
    """Get a specific provider configuration."""
    try:
        config = await provider_service.get_provider_config(provider_id)
        if not config:
            raise HTTPException(status_code=404, detail="Provider configuration not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching provider config: {str(e)}")

@admin_router.put("/providers/configs/{provider_id}", response_model=ProviderConfigOut)
async def update_provider_config(
    provider_id: str, 
    update: ProviderConfigUpdate, 
    admin: User = Depends(verify_admin)
):
    """Update a provider configuration."""
    try:
        updated_config = await provider_service.update_provider_config(provider_id, update)
        if not updated_config:
            raise HTTPException(status_code=404, detail="Provider configuration not found")
        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating provider config: {str(e)}")

@admin_router.delete("/providers/configs/{provider_id}")
async def delete_provider_config(provider_id: str, admin: User = Depends(verify_admin)):
    """Delete a provider configuration."""
    try:
        success = await provider_service.delete_provider_config(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Provider configuration not found")
        return {"message": "Provider configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting provider config: {str(e)}")

@admin_router.post("/providers/configs/{provider_id}/test", response_model=ProviderTestResponse)
async def test_provider_connection(
    provider_id: str, 
    test_request: Optional[Dict] = None,
    admin: User = Depends(verify_admin)
):
    """Test a provider connection."""
    try:
        result = await provider_service.test_provider_connection(provider_id, test_request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing provider connection: {str(e)}")

@admin_router.post("/providers/configs/{provider_id}/enable")
async def toggle_provider(
    provider_id: str, 
    enabled: bool,
    admin: User = Depends(verify_admin)
):
    """Enable or disable a provider."""
    try:
        update = ProviderConfigUpdate(enabled=enabled)
        updated_config = await provider_service.update_provider_config(provider_id, update)
        if not updated_config:
            raise HTTPException(status_code=404, detail="Provider configuration not found")
        return {
            "message": f"Provider {'enabled' if enabled else 'disabled'} successfully",
            "enabled": enabled
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling provider: {str(e)}")

@admin_router.get("/providers/status")
async def get_provider_statuses(admin: User = Depends(verify_admin)):
    """Get status of all providers."""
    try:
        providers = await provider_service.get_provider_statuses()
        current_provider = get_current_provider()
        return {
            "providers": providers,
            "active_provider": current_provider,
            "total_count": len(providers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching provider statuses: {str(e)}")
