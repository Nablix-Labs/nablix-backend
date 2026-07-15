import asyncio

from fastapi import APIRouter

from app.api.auth import AccessToken
from app.core.config import get_settings
from app.models.rag import RAGRetrieveRequest, RAGRetrieveResponse
from app.services.rag_retrieval import retrieve_content


router = APIRouter()


@router.post("/retrieve", response_model=RAGRetrieveResponse)
async def retrieve_rag(
    request: RAGRetrieveRequest,
    _access_token: AccessToken,
) -> RAGRetrieveResponse:
    return await asyncio.to_thread(retrieve_content, request, get_settings())
