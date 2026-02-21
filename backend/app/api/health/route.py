import os
from fastapi import APIRouter, HTTPException

from app.db import async_mongodb

health_router = APIRouter()


@health_router.get("")
async def health():
    """Report whether the app, database, and vector store are reachable."""
    out = {"ok": True}

    try:
        await async_mongodb.db.command("ping")
        out["db"] = "ok"
        config = await async_mongodb.db.config.find_one({"_id": "app_config"})
        out["db_setup"] = config is not None
    except Exception as e:
        out["ok"] = False
        out["db"] = str(e)
        out["db_setup"] = False

    url = os.getenv("QDRANT_URL")
    if not url:
        out["qdrant"] = "not configured"
    else:
        try:
            import qdrant_client
            client = qdrant_client.QdrantClient(
                url=url,
                api_key=os.getenv("QDRANT_API_KEY") or None,
            )
            client.get_collections()
            out["qdrant"] = "ok"
        except Exception as e:
            out["ok"] = False
            out["qdrant"] = str(e)

    if not out["ok"]:
        raise HTTPException(status_code=503, detail=out)
    return out
