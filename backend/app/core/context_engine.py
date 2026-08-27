from typing import Dict, Any, Optional

class ContextEngine:
    async def resolve_context(
        self,
        farmer_id: str,
        crop: str,
        crop_stage_days: Optional[int],
        district: Optional[str],
        state: Optional[str]
    ) -> Dict[str, Any]:
        """
        Combines Farmer Profile, Crop Passport, and Weather Snapshot.
        """
        stage = crop_stage_days if crop_stage_days is not None else 35
        dist = district if district else "Latur"
        st = state if state else "Maharashtra"

        # Weather retrieval (Mock / IMD API integration)
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
            "crop": crop,
            "stage_days": stage,
            "stage_name": self._infer_crop_stage(stage),
            "district": dist,
            "state": st,
            "season": "Kharif",
            "weather": weather_snapshot
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
