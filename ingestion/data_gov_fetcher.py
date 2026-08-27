import httpx
import os
import uuid
from typing import List, Dict, Any
from backend.app.config import settings
from backend.app.db.database import SessionLocal
from backend.app.db.models import KnowledgeDocument

DEFAULT_RESOURCE_ID = "374a23ed-9705-4e78-9a3b-28043b81eb08"

async def fetch_and_ingest_data_gov_kcc(
    api_key: str = None,
    resource_id: str = None,
    limit: int = 50,
    state_filter: str = "Maharashtra"
) -> Dict[str, Any]:
    """
    Fetches real Kisan Call Centre (KCC) call transcripts directly from data.gov.in REST API
    and indexes them into FasalMitra's Knowledge Base.
    """
    active_api_key = api_key or settings.DATA_GOV_IN_API_KEY or os.getenv("DATA_GOV_IN_API_KEY", "")
    target_resource_id = resource_id or os.getenv("DATA_GOV_KCC_RESOURCE_ID", DEFAULT_RESOURCE_ID)

    if not active_api_key:
        return {
            "status": "SKIPPED",
            "message": "DATA_GOV_IN_API_KEY not configured. Using local offline datasets.",
            "count": 0
        }

    url = f"https://api.data.gov.in/resource/{target_resource_id}"
    params = {
        "api-key": active_api_key,
        "format": "json",
        "limit": limit
    }
    headers = {
        "User-Agent": "FasalMitra-AgriAdvisory/1.0"
    }

    try:
        async with httpx.AsyncClient(timeout=25.0, verify=False) as client:
            res = await client.get(url, params=params, headers=headers)
            
            if res.status_code != 200:
                return {
                    "status": "ERROR",
                    "message": f"data.gov.in API returned HTTP status {res.status_code}",
                    "count": 0
                }

            data = res.json()
            
            # Check for API error response (e.g. Meta not found or invalid key)
            if data.get("status") == "error":
                error_msg = data.get("message", "Unknown error from data.gov.in")
                return {
                    "status": "RESOURCE_NOT_FOUND",
                    "message": f"data.gov.in API returned error: '{error_msg}'. Ensure valid catalog Resource ID.",
                    "count": 0
                }

            records = data.get("records", [])

            if not records:
                return {
                    "status": "NO_RECORDS",
                    "message": "No KCC records returned by data.gov.in API for this resource ID.",
                    "count": 0
                }

            session = SessionLocal()
            ingested_count = 0

            try:
                for rec in records:
                    state = rec.get("state", state_filter)
                    district = rec.get("district", "Latur")
                    crop = rec.get("crop", rec.get("sector", "General"))
                    query_text = rec.get("querytext", rec.get("kccans", rec.get("querytype", "")))
                    ans_text = rec.get("kccans", "")

                    if not query_text and not ans_text:
                        content = f"Record: {str(rec)}"
                    else:
                        content = f"Farmer Query: {query_text}\nKCC Expert Advice: {ans_text}"

                    doc_id = f"DOC-KCC-DATAGOV-{uuid.uuid4().hex[:8].upper()}"

                    doc = KnowledgeDocument(
                        id=doc_id,
                        source_name="Kisan Call Centre (data.gov.in API)",
                        authority_tier=1,
                        title=f"KCC Call Record - {crop} ({district})",
                        crop=crop,
                        district=district,
                        state=state,
                        content=content
                    )
                    session.add(doc)
                    ingested_count += 1

                session.commit()
                return {
                    "status": "SUCCESS",
                    "message": f"Successfully ingested {ingested_count} real KCC records from data.gov.in API into Knowledge Database.",
                    "count": ingested_count
                }
            finally:
                session.close()

    except Exception as e:
        return {
            "status": "FAILED",
            "message": f"Error fetching from data.gov.in API: {str(e)}",
            "count": 0
        }
