import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.app.db.database import get_db
from backend.app.db.models import KnowledgeDocument
from ingestion.data_gov_fetcher import fetch_and_ingest_data_gov_kcc

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

class DocumentIngestRequest(BaseModel):
    source_name: str
    authority_tier: int = 1
    title: str
    crop: str
    district: str
    state: str = "Maharashtra"
    content: str

@router.post("/upload")
def ingest_document(
    doc: DocumentIngestRequest,
    db: Session = Depends(get_db)
):
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    new_doc = KnowledgeDocument(
        id=doc_id,
        source_name=doc.source_name,
        authority_tier=doc.authority_tier,
        title=doc.title,
        crop=doc.crop,
        district=doc.district,
        state=doc.state,
        content=doc.content
    )
    db.add(new_doc)
    db.commit()
    return {"status": "SUCCESS", "document_id": doc_id, "message": "Document indexed successfully into hybrid knowledge store."}


@router.post("/sync-data-gov")
async def sync_data_gov_api(
    api_key: Optional[str] = Query(None, description="data.gov.in API key"),
    limit: int = Query(50, description="Number of records to fetch"),
    state: str = Query("Maharashtra", description="State filter")
):
    """
    Automated Data.gov.in API Sync Endpoint.
    Directly pulls real Kisan Call Centre (KCC) transcripts from data.gov.in REST API using API Key.
    """
    result = await fetch_and_ingest_data_gov_kcc(api_key=api_key, limit=limit, state_filter=state)
    return result
