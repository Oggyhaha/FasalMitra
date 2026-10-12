import re
import os
import httpx
from typing import Dict, Any, Optional, Tuple

class GeoTracker:
    def __init__(self):
        self._ip_cache: Dict[str, Dict[str, str]] = {}

        # All 33 Districts of Gujarat
        self.gujarat_districts = {
            "ahmedabad": "Ahmedabad", "amdavad": "Ahmedabad", "amreli": "Amreli",
            "anand": "Anand", "aravalli": "Aravalli", "banaskantha": "Banaskantha",
            "palanpur": "Banaskantha", "dantiwada": "Banaskantha", "bharuch": "Bharuch",
            "bhavnagar": "Bhavnagar", "botad": "Botad", "chhota udepur": "Chhota Udepur",
            "chhotaudepur": "Chhota Udepur", "dahod": "Dahod", "dang": "Dang",
            "devbhumi dwarka": "Devbhumi Dwarka", "dwarka": "Devbhumi Dwarka",
            "gandhinagar": "Gandhinagar", "gir somnath": "Gir Somnath", "veraval": "Gir Somnath",
            "jamnagar": "Jamnagar", "junagadh": "Junagadh", "kheda": "Kheda", "nadiad": "Kheda",
            "kutch": "Kutch", "kachchh": "Kutch", "bhuj": "Kutch", "mahisagar": "Mahisagar",
            "lunawada": "Mahisagar", "mehsana": "Mehsana", "mahesana": "Mehsana",
            "morbi": "Morbi", "narmada": "Narmada", "rajpipla": "Narmada", "navsari": "Navsari",
            "panchmahal": "Panchmahal", "godhra": "Panchmahal", "patan": "Patan",
            "porbandar": "Porbandar", "rajkot": "Rajkot", "sabarkantha": "Sabarkantha",
            "himatnagar": "Sabarkantha", "surat": "Surat", "surendranagar": "Surendranagar",
            "tapi": "Tapi", "vyara": "Tapi", "vadodara": "Vadodara", "baroda": "Vadodara",
            "valsad": "Valsad"
        }

        # Major Districts of other prominent agricultural states
        self.other_state_districts = {
            # Maharashtra
            "latur": ("Maharashtra", "Latur"), "pune": ("Maharashtra", "Pune"),
            "nagpur": ("Maharashtra", "Nagpur"), "nashik": ("Maharashtra", "Nashik"),
            "solapur": ("Maharashtra", "Solapur"), "amravati": ("Maharashtra", "Amravati"),
            "akola": ("Maharashtra", "Akola"), "nanded": ("Maharashtra", "Nanded"),
            "aurangabad": ("Maharashtra", "Chhatrapati Sambhajinagar"), "sambhajinagar": ("Maharashtra", "Chhatrapati Sambhajinagar"),
            "beed": ("Maharashtra", "Beed"), "jalna": ("Maharashtra", "Jalna"),
            "kolhapur": ("Maharashtra", "Kolhapur"), "sangli": ("Maharashtra", "Sangli"),
            "satara": ("Maharashtra", "Satara"), "yavatmal": ("Maharashtra", "Yavatmal"),
            "buldhana": ("Maharashtra", "Buldhana"), "wardha": ("Maharashtra", "Wardha"),
            # Punjab
            "ludhiana": ("Punjab", "Ludhiana"), "amritsar": ("Punjab", "Amritsar"),
            "jalandhar": ("Punjab", "Jalandhar"), "bathinda": ("Punjab", "Bathinda"),
            "patiala": ("Punjab", "Patiala"), "ferozepur": ("Punjab", "Ferozepur"),
            # Haryana
            "karnal": ("Haryana", "Karnal"), "hisar": ("Haryana", "Hisar"),
            "rohtak": ("Haryana", "Rohtak"), "sirsa": ("Haryana", "Sirsa"),
            # Madhya Pradesh
            "indore": ("Madhya Pradesh", "Indore"), "bhopal": ("Madhya Pradesh", "Bhopal"),
            "ujjain": ("Madhya Pradesh", "Ujjain"), "dewas": ("Madhya Pradesh", "Dewas"),
            "sehore": ("Madhya Pradesh", "Sehore"), "vidisha": ("Madhya Pradesh", "Vidisha"),
            # Uttar Pradesh
            "lucknow": ("Uttar Pradesh", "Lucknow"), "varanasi": ("Uttar Pradesh", "Varanasi"),
            "kanpur": ("Uttar Pradesh", "Kanpur"), "agra": ("Uttar Pradesh", "Agra"),
            "meerut": ("Uttar Pradesh", "Meerut"), "bareilly": ("Uttar Pradesh", "Bareilly"),
            # Rajasthan
            "jaipur": ("Rajasthan", "Jaipur"), "jodhpur": ("Rajasthan", "Jodhpur"),
            "kota": ("Rajasthan", "Kota"), "sri ganganagar": ("Rajasthan", "Sri Ganganagar"),
            # Karnataka
            "bengaluru": ("Karnataka", "Bengaluru"), "mysuru": ("Karnataka", "Mysuru"),
            "dharwad": ("Karnataka", "Dharwad"), "belagavi": ("Karnataka", "Belagavi"),
            # Andhra Pradesh & Telangana
            "hyderabad": ("Telangana", "Hyderabad"), "warangal": ("Telangana", "Warangal"),
            "guntur": ("Andhra Pradesh", "Guntur"), "krishna": ("Andhra Pradesh", "Krishna"),
            # Tamil Nadu
            "coimbatore": ("Tamil Nadu", "Coimbatore"), "madurai": ("Tamil Nadu", "Madurai"),
            "thanjavur": ("Tamil Nadu", "Thanjavur"), "salem": ("Tamil Nadu", "Salem"),
            # West Bengal
            "kolkata": ("West Bengal", "Kolkata"), "bardhaman": ("West Bengal", "Purba Bardhaman"),
            "hooghly": ("West Bengal", "Hooghly"), "nadia": ("West Bengal", "Nadia")
        }

        # Language-to-State Correlation Defaults
        self.language_state_defaults = {
            "gu": ("Gujarat", "Anand"),
            "mr": ("Maharashtra", "Latur"),
            "pa": ("Punjab", "Ludhiana"),
            "te": ("Andhra Pradesh", "Guntur"),
            "ta": ("Tamil Nadu", "Coimbatore"),
            "kn": ("Karnataka", "Dharwad"),
            "ml": ("Kerala", "Palakkad"),
            "bn": ("West Bengal", "Purba Bardhaman"),
            "or": ("Odisha", "Cuttack"),
            "as": ("Assam", "Jorhat"),
            "ur": ("Uttar Pradesh", "Lucknow"),
            "hi": ("Madhya Pradesh", "Indore"),
            "ne": ("Sikkim", "Gangtok"),
            "kok": ("Goa", "North Goa"),
            "mai": ("Bihar", "Darbhanga"),
            "doi": ("Jammu and Kashmir", "Jammu"),
            "ks": ("Jammu and Kashmir", "Srinagar"),
            "mni": ("Manipur", "Imphal"),
            "brx": ("Assam", "Kokrajhar"),
            "sat": ("Jharkhand", "Ranchi"),
            "en": ("Gujarat", "Anand") # Default fallback
        }

    async def resolve_ip(self, ip_address: Optional[str]) -> Optional[Dict[str, str]]:
        """Resolves client IP address to State and District/City via GeoIP lookup with caching."""
        if not ip_address:
            return None

        # Clean IP (handle proxies like X-Forwarded-For: 203.0.113.195, 70.41.3.18)
        ip = ip_address.split(',')[0].strip()

        # Ignore local development IPs
        if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith("192.168.") or ip.startswith("10."):
            # Check if environment or simulated override exists
            sim_state = os.getenv("SIMULATE_GEO_STATE", "Gujarat")
            sim_dist = os.getenv("SIMULATE_GEO_DISTRICT", "Anand")
            return {"state": sim_state, "district": sim_dist, "city": sim_dist, "country": "India"}

        if ip in self._ip_cache:
            return self._ip_cache[ip]

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"https://ipapi.co/{ip}/json/")
                if resp.status_code == 200:
                    data = resp.json()
                    res = {
                        "state": data.get("region", "Gujarat"),
                        "district": data.get("city", "Anand"),
                        "city": data.get("city", "Anand"),
                        "country": data.get("country_name", "India")
                    }
                    self._ip_cache[ip] = res
                    return res
        except Exception:
            pass

        return None

    def detect_location(
        self,
        query_text: str,
        client_ip_data: Optional[Dict[str, str]] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        detected_lang: Optional[str] = None,
        requested_district: Optional[str] = None,
        requested_state: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Intelligently resolves State and District from:
        1. Explicit override if already specific (not general Latur)
        2. Query text district mention (e.g. 'Rajkot', 'Surat', 'Banaskantha')
        3. GPS Pin coordinates
        4. Client IP Geolocation
        5. Language correlation (e.g. Gujarati -> Gujarat)
        """
        # 1. Check for District Mention directly in farmer query
        text_lower = query_text.lower() if query_text else ""

        # Check Gujarat districts first
        for d_key, d_name in self.gujarat_districts.items():
            if re.search(r'\b' + re.escape(d_key) + r'\b', text_lower):
                return "Gujarat", d_name

        # Check other state districts
        for d_key, (st_name, dist_name) in self.other_state_districts.items():
            if re.search(r'\b' + re.escape(d_key) + r'\b', text_lower):
                return st_name, dist_name

        # 2. Check GPS Pin Coordinates (Reverse geocoding boundary box for Gujarat: ~20.1 to 24.7 N, 68.1 to 74.5 E)
        if lat is not None and lon is not None:
            if 20.1 <= lat <= 24.7 and 68.1 <= lon <= 74.5:
                return "Gujarat", "Anand"
            elif 15.6 <= lat <= 22.0 and 72.6 <= lon <= 80.9:
                return "Maharashtra", "Latur"

        # 3. Check Client IP Geolocation
        if client_ip_data and client_ip_data.get("state"):
            state = client_ip_data["state"]
            dist = client_ip_data.get("district") or client_ip_data.get("city") or "Anand"
            # Normalize common names
            if "gujarat" in state.lower():
                return "Gujarat", dist if dist in self.gujarat_districts.values() else "Anand"
            return state, dist

        # 4. Check Explicit Request (if not default Latur)
        if requested_district and requested_district.lower() not in ["latur", "none", ""]:
            req_dist_lower = requested_district.lower()
            if req_dist_lower in self.gujarat_districts:
                return "Gujarat", self.gujarat_districts[req_dist_lower]
            return requested_state or "Gujarat", requested_district

        if requested_state and requested_state.lower() not in ["maharashtra", "none", ""]:
            return requested_state, requested_district or "Anand"

        # 5. Language-to-State Correlation
        if detected_lang and detected_lang in self.language_state_defaults:
            return self.language_state_defaults[detected_lang]

        # Default fallback
        return "Gujarat", "Anand"

    def get_regional_agro_profile(self, state: str, district: str) -> Dict[str, Any]:
        """Provides state-specific agricultural authorities, research institutes, and context."""
        st_lower = state.lower()
        if "gujarat" in st_lower:
            return {
                "state": "Gujarat",
                "district": district,
                "authorities": "Anand Agricultural University (AAU), Junagadh Agricultural University (JAU), NAU, SDAU & ICAR-ATARI Zone VIII",
                "portal_scheme": "Gujarat i-Khedut Portal & Mukhyamantri Kisan Sahay Yojana",
                "soil_context": "Black Cotton Soils, Sandy Loam, Coastal Alluvium",
                "climate_zone": "Saurashtra / North Gujarat Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Gujarat"
            }
        elif "maharashtra" in st_lower:
            return {
                "state": "Maharashtra",
                "district": district,
                "authorities": "MPKV Rahuri, VNMKV Parbhani, PDKV Akola & ICAR Maharashtra",
                "portal_scheme": "MahaDBT Farmer Portal & Nanaji Deshmukh Krishi Sanjivani Yojana",
                "soil_context": "Deep Black Clay (Regur Soils), Medium Loam",
                "climate_zone": "Marathwada / Vidarbha Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Maharashtra"
            }
        elif "punjab" in st_lower:
            return {
                "state": "Punjab",
                "district": district,
                "authorities": "Punjab Agricultural University (PAU) Ludhiana & ICAR-ATARI Zone I",
                "portal_scheme": "Punjab Agriculture & Farmers Welfare Schemes",
                "soil_context": "Alluvial Loam Soils",
                "climate_zone": "Trans-Gangetic Plains",
                "weather_station": f"IMD Agromet Advisory - {district}, Punjab"
            }
        else:
            return {
                "state": state,
                "district": district,
                "authorities": f"State Agricultural University (SAU) & ICAR KVK {district}",
                "portal_scheme": "PM-Kisan & State Department of Agriculture",
                "soil_context": "Regional Alluvial and Loamy Soil",
                "climate_zone": f"{state} Regional Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory Service - {district}, {state}"
            }

geo_tracker = GeoTracker()
