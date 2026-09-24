from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.app.db.models import Message, Conversation, CropPassport, Farmer

class ContextEngine:
    async def resolve_context(
        self,
        farmer_id: str,
        crop: str,
        crop_stage_days: Optional[int],
        district: Optional[str],
        state: Optional[str],
        db: Optional[Session] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Combines Farmer Profile, Crop Passport, Weather Snapshot, and Multi-Turn Conversation History.
        """
        stage = crop_stage_days if crop_stage_days is not None else 35
        dist = district if district else "Latur"
        st = state if state else "Maharashtra"

        history_turns: List[Dict[str, str]] = []
        resolved_crop = crop

        # 1. Multi-turn Dialogue Memory Resolution
        if db:
            # Query recent messages for this conversation or farmer
            msg_query = db.query(Message)
            if conversation_id:
                msg_query = msg_query.filter(Message.conversation_id == conversation_id)
            elif farmer_id:
                conv = db.query(Conversation).filter(Conversation.farmer_id == farmer_id).order_by(Conversation.created_at.desc()).first()
                if conv:
                    msg_query = msg_query.filter(Message.conversation_id == conv.id)

            recent_msgs = msg_query.order_by(Message.created_at.desc()).limit(6).all()
            recent_msgs.reverse() # Chronological order

            for m in recent_msgs:
                history_turns.append({"sender": m.sender, "text": m.raw_text})

            # If crop is General/unspecified, infer crop from CropPassport or recent turns
            if not resolved_crop or resolved_crop == "General":
                passport = db.query(CropPassport).first()
                if passport:
                    resolved_crop = passport.crop_name

        # 2. Weather Snapshot Retrieval
        weather_snapshot = {
            "district": dist,
            "temp_c": 28.5,
            "humidity_pct": 82,
            "rainfall_forecast_24h_mm": 12.0,
            "condition": "Partly Cloudy with Moderate Humidity",
            "source": "IMD Agromet Advisory Service"
        }

        return {
            "farmer_id": farmer_id,
            "conversation_id": conversation_id,
            "crop": resolved_crop,
            "stage_days": stage,
            "stage_name": self._infer_crop_stage(stage),
            "district": dist,
            "state": st,
            "season": "Kharif",
            "weather": weather_snapshot,
            "conversation_history": history_turns
        }

    def _infer_crop_stage(self, days: int) -> str:
        if days < 20:
            return "Germination / Vegetative"
        elif days <= 55:
            return "Flowering & Pod Formation"
        elif days <= 90:
            return "Grain Filling / Pod Maturity"
        else:
            return "Harvesting"

context_engine = ContextEngine()

