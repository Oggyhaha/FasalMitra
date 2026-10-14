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

        # Comprehensive District-to-State Mapping for ALL Indian States & UTs
        self.all_india_districts: Dict[str, Tuple[str, str]] = {
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
            "ahmednagar": ("Maharashtra", "Ahilyanagar"), "dhule": ("Maharashtra", "Dhule"),
            "jalgaon": ("Maharashtra", "Jalgaon"), "osmanabad": ("Maharashtra", "Dharashiv"),
            "parbhani": ("Maharashtra", "Parbhani"), "chandrapur": ("Maharashtra", "Chandrapur"),
            # Punjab
            "ludhiana": ("Punjab", "Ludhiana"), "amritsar": ("Punjab", "Amritsar"),
            "jalandhar": ("Punjab", "Jalandhar"), "bathinda": ("Punjab", "Bathinda"),
            "patiala": ("Punjab", "Patiala"), "ferozepur": ("Punjab", "Ferozepur"),
            "sangrur": ("Punjab", "Sangrur"), "gurdaspur": ("Punjab", "Gurdaspur"),
            "hoshiarpur": ("Punjab", "Hoshiarpur"), "moga": ("Punjab", "Moga"),
            "mansa": ("Punjab", "Mansa"), "fazilka": ("Punjab", "Fazilka"),
            "kapurthala": ("Punjab", "Kapurthala"), "faridkot": ("Punjab", "Faridkot"),
            # Haryana
            "karnal": ("Haryana", "Karnal"), "hisar": ("Haryana", "Hisar"),
            "rohtak": ("Haryana", "Rohtak"), "sirsa": ("Haryana", "Sirsa"),
            "ambala": ("Haryana", "Ambala"), "bhiwani": ("Haryana", "Bhiwani"),
            "gurugram": ("Haryana", "Gurugram"), "kurukshetra": ("Haryana", "Kurukshetra"),
            "panipat": ("Haryana", "Panipat"), "sonipat": ("Haryana", "Sonipat"),
            "yamunanagar": ("Haryana", "Yamunanagar"), "fatehabad": ("Haryana", "Fatehabad"),
            # Uttar Pradesh
            "lucknow": ("Uttar Pradesh", "Lucknow"), "varanasi": ("Uttar Pradesh", "Varanasi"),
            "kanpur": ("Uttar Pradesh", "Kanpur"), "agra": ("Uttar Pradesh", "Agra"),
            "meerut": ("Uttar Pradesh", "Meerut"), "bareilly": ("Uttar Pradesh", "Bareilly"),
            "aligarh": ("Uttar Pradesh", "Aligarh"), "ayodhya": ("Uttar Pradesh", "Ayodhya"),
            "faizabad": ("Uttar Pradesh", "Ayodhya"), "gorakhpur": ("Uttar Pradesh", "Gorakhpur"),
            "jhansi": ("Uttar Pradesh", "Jhansi"), "prayagraj": ("Uttar Pradesh", "Prayagraj"),
            "allahabad": ("Uttar Pradesh", "Prayagraj"), "mathura": ("Uttar Pradesh", "Mathura"),
            "moradabad": ("Uttar Pradesh", "Moradabad"), "muzaffarnagar": ("Uttar Pradesh", "Muzaffarnagar"),
            "saharanpur": ("Uttar Pradesh", "Saharanpur"), "barabanki": ("Uttar Pradesh", "Barabanki"),
            "budaun": ("Uttar Pradesh", "Budaun"), "sitapur": ("Uttar Pradesh", "Sitapur"),
            # Madhya Pradesh
            "indore": ("Madhya Pradesh", "Indore"), "bhopal": ("Madhya Pradesh", "Bhopal"),
            "ujjain": ("Madhya Pradesh", "Ujjain"), "dewas": ("Madhya Pradesh", "Dewas"),
            "sehore": ("Madhya Pradesh", "Sehore"), "vidisha": ("Madhya Pradesh", "Vidisha"),
            "jabalpur": ("Madhya Pradesh", "Jabalpur"), "gwalior": ("Madhya Pradesh", "Gwalior"),
            "sagar": ("Madhya Pradesh", "Sagar"), "rewa": ("Madhya Pradesh", "Rewa"),
            "satna": ("Madhya Pradesh", "Satna"), "ratlam": ("Madhya Pradesh", "Ratlam"),
            "mandsaur": ("Madhya Pradesh", "Mandsaur"), "neemuch": ("Madhya Pradesh", "Neemuch"),
            "hoshangabad": ("Madhya Pradesh", "Narmadapuram"), "narmadapuram": ("Madhya Pradesh", "Narmadapuram"),
            "khargone": ("Madhya Pradesh", "Khargone"), "khandwa": ("Madhya Pradesh", "Khandwa"),
            "dhar": ("Madhya Pradesh", "Dhar"), "chhindwara": ("Madhya Pradesh", "Chhindwara"),
            # Rajasthan
            "jaipur": ("Rajasthan", "Jaipur"), "jodhpur": ("Rajasthan", "Jodhpur"),
            "kota": ("Rajasthan", "Kota"), "sri ganganagar": ("Rajasthan", "Sri Ganganagar"),
            "ganganagar": ("Rajasthan", "Sri Ganganagar"), "bikaner": ("Rajasthan", "Bikaner"),
            "udaipur": ("Rajasthan", "Udaipur"), "ajmer": ("Rajasthan", "Ajmer"),
            "alwar": ("Rajasthan", "Alwar"), "bhilwara": ("Rajasthan", "Bhilwara"),
            "sikar": ("Rajasthan", "Sikar"), "nagaur": ("Rajasthan", "Nagaur"),
            "chittorgarh": ("Rajasthan", "Chittorgarh"), "hanumangarh": ("Rajasthan", "Hanumangarh"),
            "baran": ("Rajasthan", "Baran"), "jhalawar": ("Rajasthan", "Jhalawar"),
            # Karnataka
            "bengaluru": ("Karnataka", "Bengaluru"), "bangalore": ("Karnataka", "Bengaluru"),
            "mysuru": ("Karnataka", "Mysuru"), "mysore": ("Karnataka", "Mysuru"),
            "dharwad": ("Karnataka", "Dharwad"), "belagavi": ("Karnataka", "Belagavi"),
            "belgaum": ("Karnataka", "Belagavi"), "shivamogga": ("Karnataka", "Shivamogga"),
            "shimoga": ("Karnataka", "Shivamogga"), "tumakuru": ("Karnataka", "Tumakuru"),
            "kalaburagi": ("Karnataka", "Kalaburagi"), "gulbarga": ("Karnataka", "Kalaburagi"),
            "ballari": ("Karnataka", "Ballari"), "bellary": ("Karnataka", "Ballari"),
            "vijayapura": ("Karnataka", "Vijayapura"), "bijapur": ("Karnataka", "Vijayapura"),
            "hassan": ("Karnataka", "Hassan"), "mandya": ("Karnataka", "Mandya"),
            "raichur": ("Karnataka", "Raichur"), "bagalkote": ("Karnataka", "Bagalkote"),
            "haveri": ("Karnataka", "Haveri"), "udupi": ("Karnataka", "Udupi"),
            # Andhra Pradesh
            "guntur": ("Andhra Pradesh", "Guntur"), "krishna": ("Andhra Pradesh", "Krishna"),
            "vijayawada": ("Andhra Pradesh", "Krishna"), "visakhapatnam": ("Andhra Pradesh", "Visakhapatnam"),
            "kurnool": ("Andhra Pradesh", "Kurnool"), "anantapur": ("Andhra Pradesh", "Anantapur"),
            "chittoor": ("Andhra Pradesh", "Chittoor"), "east godavari": ("Andhra Pradesh", "East Godavari"),
            "west godavari": ("Andhra Pradesh", "West Godavari"), "prakasam": ("Andhra Pradesh", "Prakasam"),
            "nellore": ("Andhra Pradesh", "SPSR Nellore"), "kadapa": ("Andhra Pradesh", "YSR Kadapa"),
            # Telangana
            "hyderabad": ("Telangana", "Hyderabad"), "warangal": ("Telangana", "Warangal"),
            "karimnagar": ("Telangana", "Karimnagar"), "khammam": ("Telangana", "Khammam"),
            "nizamabad": ("Telangana", "Nizamabad"), "nalgonda": ("Telangana", "Nalgonda"),
            "mahabubnagar": ("Telangana", "Mahabubnagar"), "medak": ("Telangana", "Medak"),
            "adilabad": ("Telangana", "Adilabad"), "rangareddy": ("Telangana", "Rangareddy"),
            # Tamil Nadu
            "coimbatore": ("Tamil Nadu", "Coimbatore"), "madurai": ("Tamil Nadu", "Madurai"),
            "thanjavur": ("Tamil Nadu", "Thanjavur"), "salem": ("Tamil Nadu", "Salem"),
            "tiruchirappalli": ("Tamil Nadu", "Tiruchirappalli"), "trichy": ("Tamil Nadu", "Tiruchirappalli"),
            "chennai": ("Tamil Nadu", "Chennai"), "tirunelveli": ("Tamil Nadu", "Tirunelveli"),
            "erode": ("Tamil Nadu", "Erode"), "dindigul": ("Tamil Nadu", "Dindigul"),
            "vellore": ("Tamil Nadu", "Vellore"), "cuddalore": ("Tamil Nadu", "Cuddalore"),
            "tiruvarur": ("Tamil Nadu", "Tiruvarur"), "dharmapuri": ("Tamil Nadu", "Dharmapuri"),
            # Kerala
            "palakkad": ("Kerala", "Palakkad"), "thiruvananthapuram": ("Kerala", "Thiruvananthapuram"),
            "trivandrum": ("Kerala", "Thiruvananthapuram"), "kochi": ("Kerala", "Ernakulam"),
            "ernakulam": ("Kerala", "Ernakulam"), "thrissur": ("Kerala", "Thrissur"),
            "kottayam": ("Kerala", "Kottayam"), "alappuzha": ("Kerala", "Alappuzha"),
            "kozhikode": ("Kerala", "Kozhikode"), "malappuram": ("Kerala", "Malappuram"),
            "wayanad": ("Kerala", "Wayanad"), "idukki": ("Kerala", "Idukki"),
            "kannur": ("Kerala", "Kannur"), "kollam": ("Kerala", "Kollam"),
            # West Bengal
            "kolkata": ("West Bengal", "Kolkata"), "bardhaman": ("West Bengal", "Purba Bardhaman"),
            "burdwan": ("West Bengal", "Purba Bardhaman"), "hooghly": ("West Bengal", "Hooghly"),
            "nadia": ("West Bengal", "Nadia"), "murshidabad": ("West Bengal", "Murshidabad"),
            "medinipur": ("West Bengal", "Paschim Medinipur"), "midnapore": ("West Bengal", "Paschim Medinipur"),
            "malda": ("West Bengal", "Malda"), "jalpaiguri": ("West Bengal", "Jalpaiguri"),
            "darjeeling": ("West Bengal", "Darjeeling"), "birbhum": ("West Bengal", "Birbhum"),
            "bankura": ("West Bengal", "Bankura"), "north 24 parganas": ("West Bengal", "North 24 Parganas"),
            # Bihar
            "patna": ("Bihar", "Patna"), "muzaffarpur": ("Bihar", "Muzaffarpur"),
            "bhagalpur": ("Bihar", "Bhagalpur"), "darbhanga": ("Bihar", "Darbhanga"),
            "gaya": ("Bihar", "Gaya"), "samastipur": ("Bihar", "Samastipur"),
            "purnia": ("Bihar", "Purnia"), "rohtas": ("Bihar", "Rohtas"),
            "nalanda": ("Bihar", "Nalanda"), "chhapra": ("Bihar", "Saran"),
            "vaishali": ("Bihar", "Vaishali"), "begusarai": ("Bihar", "Begusarai"),
            # Odisha
            "cuttack": ("Odisha", "Cuttack"), "bhubaneswar": ("Odisha", "Khurda"),
            "khurda": ("Odisha", "Khurda"), "sambalpur": ("Odisha", "Sambalpur"),
            "balasore": ("Odisha", "Balasore"), "ganjam": ("Odisha", "Ganjam"),
            "puri": ("Odisha", "Puri"), "bargarh": ("Odisha", "Bargarh"),
            "kalahandi": ("Odisha", "Kalahandi"), "koraput": ("Odisha", "Koraput"),
            "bolangir": ("Odisha", "Balangir"), "mayurbhanj": ("Odisha", "Mayurbhanj"),
            # Assam
            "guwahati": ("Assam", "Kamrup Metropolitan"), "kamrup": ("Assam", "Kamrup"),
            "jorhat": ("Assam", "Jorhat"), "dibrugarh": ("Assam", "Dibrugarh"),
            "silchar": ("Assam", "Cachar"), "nagaon": ("Assam", "Nagaon"),
            "sonitpur": ("Assam", "Sonitpur"), "tezpur": ("Assam", "Sonitpur"),
            "barpeta": ("Assam", "Barpeta"), "tinsukia": ("Assam", "Tinsukia"),
            "kokrajhar": ("Assam", "Kokrajhar"), "golaghat": ("Assam", "Golaghat"),
            # Chhattisgarh
            "raipur": ("Chhattisgarh", "Raipur"), "bilaspur": ("Chhattisgarh", "Bilaspur"),
            "durg": ("Chhattisgarh", "Durg"), "rajnandgaon": ("Chhattisgarh", "Rajnandgaon"),
            "bastar": ("Chhattisgarh", "Bastar"), "surguja": ("Chhattisgarh", "Surguja"),
            "korba": ("Chhattisgarh", "Korba"), "janjgir": ("Chhattisgarh", "Janjgir-Champa"),
            # Jharkhand
            "ranchi": ("Jharkhand", "Ranchi"), "jamshedpur": ("Jharkhand", "East Singhbhum"),
            "dhanbad": ("Jharkhand", "Dhanbad"), "bokaro": ("Jharkhand", "Bokaro"),
            "hazaribagh": ("Jharkhand", "Hazaribagh"), "deoghar": ("Jharkhand", "Deoghar"),
            "dumka": ("Jharkhand", "Dumka"), "palamu": ("Jharkhand", "Palamu"),
            # Himachal Pradesh
            "shimla": ("Himachal Pradesh", "Shimla"), "kangra": ("Himachal Pradesh", "Kangra"),
            "mandi": ("Himachal Pradesh", "Mandi"), "kullu": ("Himachal Pradesh", "Kullu"),
            "solan": ("Himachal Pradesh", "Solan"), "una": ("Himachal Pradesh", "Una"),
            "hamirpur": ("Himachal Pradesh", "Hamirpur"), "chamba": ("Himachal Pradesh", "Chamba"),
            # Uttarakhand
            "dehradun": ("Uttarakhand", "Dehradun"), "haridwar": ("Uttarakhand", "Haridwar"),
            "udham singh nagar": ("Uttarakhand", "Udham Singh Nagar"), "pantnagar": ("Uttarakhand", "Udham Singh Nagar"),
            "nainital": ("Uttarakhand", "Nainital"), "almora": ("Uttarakhand", "Almora"),
            "tehri": ("Uttarakhand", "Tehri Garhwal"), "pauri": ("Uttarakhand", "Pauri Garhwal"),
            # Jammu and Kashmir & Ladakh
            "srinagar": ("Jammu and Kashmir", "Srinagar"), "jammu": ("Jammu and Kashmir", "Jammu"),
            "anantnag": ("Jammu and Kashmir", "Anantnag"), "baramulla": ("Jammu and Kashmir", "Baramulla"),
            "pulwama": ("Jammu and Kashmir", "Pulwama"), "udhampur": ("Jammu and Kashmir", "Udhampur"),
            "kathua": ("Jammu and Kashmir", "Kathua"), "kupwara": ("Jammu and Kashmir", "Kupwara"),
            "leh": ("Ladakh", "Leh"), "kargil": ("Ladakh", "Kargil"),
            # Goa
            "panaji": ("Goa", "North Goa"), "north goa": ("Goa", "North Goa"),
            "south goa": ("Goa", "South Goa"), "margao": ("Goa", "South Goa"),
            # North-Eastern States
            "imphal": ("Manipur", "Imphal West"), "shillong": ("Meghalaya", "East Khasi Hills"),
            "aizawl": ("Mizoram", "Aizawl"), "kohima": ("Nagaland", "Kohima"),
            "dimapur": ("Nagaland", "Dimapur"), "gangtok": ("Sikkim", "East Sikkim"),
            "agartala": ("Tripura", "West Tripura"), "itanagar": ("Arunachal Pradesh", "Papum Pare"),
            # Delhi & UTs
            "delhi": ("Delhi", "New Delhi"), "new delhi": ("Delhi", "New Delhi"),
            "chandigarh": ("Chandigarh", "Chandigarh"), "puducherry": ("Puducherry", "Puducherry"),
            "pondicherry": ("Puducherry", "Puducherry")
        }

        # Canonical State Names in India
        self.indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal", "Jammu and Kashmir",
            "Ladakh", "Delhi", "Puducherry", "Chandigarh"
        ]

        # Language-to-State Correlation Defaults for all 23 Languages
        self.language_state_defaults = {
            "gu": ("Gujarat", "Anand"),
            "mr": ("Maharashtra", "Pune"),
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
            "sd": ("Rajasthan", "Jodhpur"),
            "sa": ("Uttarakhand", "Dehradun"),
            "en": ("Gujarat", "Anand")
        }

    async def resolve_ip(self, ip_address: Optional[str]) -> Optional[Dict[str, str]]:
        """Resolves client IP address to State and District/City via GeoIP lookup with caching."""
        if not ip_address:
            return None

        # Clean IP (handle proxies like X-Forwarded-For: 203.0.113.195, 70.41.3.18)
        ip = ip_address.split(',')[0].strip()

        # Handle local development IPs
        if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith("192.168.") or ip.startswith("10."):
            sim_state = os.getenv("SIMULATE_GEO_STATE", "Gujarat")
            sim_dist = os.getenv("SIMULATE_GEO_DISTRICT", "Anand")
            return {"state": sim_state, "district": sim_dist, "city": sim_dist, "country": "India"}

        if ip in self._ip_cache:
            return self._ip_cache[ip]

        try:
            async with httpx.AsyncClient(timeout=3.5) as client:
                resp = await client.get(f"https://ipapi.co/{ip}/json/")
                if resp.status_code == 200:
                    data = resp.json()
                    region = data.get("region", "")
                    city = data.get("city", "")

                    # Normalize region to canonical Indian state
                    matched_state = self._normalize_state_name(region)
                    res = {
                        "state": matched_state or region or "Gujarat",
                        "district": city or "Anand",
                        "city": city or "Anand",
                        "country": data.get("country_name", "India")
                    }
                    self._ip_cache[ip] = res
                    return res
        except Exception:
            pass

        return None

    def _normalize_state_name(self, raw_name: str) -> Optional[str]:
        """Normalizes freeform or API region names into official Indian state names."""
        if not raw_name:
            return None
        name_lower = raw_name.lower().strip()
        for state in self.indian_states:
            if state.lower() == name_lower or state.lower() in name_lower:
                return state
        # Aliases
        aliases = {
            "orissa": "Odisha",
            "uttaranchal": "Uttarakhand",
            "pondicherry": "Puducherry",
            "j&k": "Jammu and Kashmir",
            "jammu & kashmir": "Jammu and Kashmir",
            "kashmir": "Jammu and Kashmir",
            "bengal": "West Bengal",
            "up": "Uttar Pradesh",
            "mp": "Madhya Pradesh",
            "ap": "Andhra Pradesh",
            "tn": "Tamil Nadu"
        }
        return aliases.get(name_lower)

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
        1. Query text state or district mention (e.g. 'Gujarat', 'Rajkot', 'Punjab', 'Ludhiana', 'Guntur')
        2. GPS Pin coordinates
        3. Client IP Geolocation
        4. Explicit override from request
        5. Language correlation (e.g. Punjabi -> Punjab, Telugu -> Andhra Pradesh)
        """
        text_lower = query_text.lower() if query_text else ""

        # 1A. Check for explicit State mention in query text
        for state in self.indian_states:
            if re.search(r'\b' + re.escape(state.lower()) + r'\b', text_lower):
                default_dist = self._get_default_district_for_state(state)
                # Also check if a specific district of this state is mentioned
                for d_key, (st_name, dist_name) in self.all_india_districts.items():
                    if st_name.lower() == state.lower() and re.search(r'\b' + re.escape(d_key) + r'\b', text_lower):
                        return state, dist_name
                return state, default_dist

        # 1B. Check for Gujarat districts first (priority for Gujarat queries)
        for d_key, d_name in self.gujarat_districts.items():
            if re.search(r'\b' + re.escape(d_key) + r'\b', text_lower):
                return "Gujarat", d_name

        # 1C. Check all other Indian districts
        for d_key, (st_name, dist_name) in self.all_india_districts.items():
            if re.search(r'\b' + re.escape(d_key) + r'\b', text_lower):
                return st_name, dist_name

        # 2. Check GPS Pin Coordinates (approximate boundary boxes)
        if lat is not None and lon is not None:
            gps_loc = self._resolve_gps_bounds(lat, lon)
            if gps_loc:
                return gps_loc

        # 3. Check Client IP Geolocation
        if client_ip_data and client_ip_data.get("state"):
            ip_state = self._normalize_state_name(client_ip_data["state"]) or client_ip_data["state"]
            ip_dist = client_ip_data.get("district") or client_ip_data.get("city") or self._get_default_district_for_state(ip_state)
            return ip_state, ip_dist

        # 4. Check Explicit Request
        if requested_state and requested_state.lower() not in ["none", "auto", ""]:
            norm_st = self._normalize_state_name(requested_state) or requested_state
            norm_dist = requested_district if requested_district and requested_district.lower() not in ["none", "auto", ""] else self._get_default_district_for_state(norm_st)
            return norm_st, norm_dist

        if requested_district and requested_district.lower() not in ["latur", "none", "auto", ""]:
            req_dist_lower = requested_district.lower()
            if req_dist_lower in self.gujarat_districts:
                return "Gujarat", self.gujarat_districts[req_dist_lower]
            if req_dist_lower in self.all_india_districts:
                return self.all_india_districts[req_dist_lower]
            return "Gujarat", requested_district

        # 5. Language-to-State Correlation
        if detected_lang and detected_lang in self.language_state_defaults:
            return self.language_state_defaults[detected_lang]

        # Default national fallback
        return "Gujarat", "Anand"

    def _resolve_gps_bounds(self, lat: float, lon: float) -> Optional[Tuple[str, str]]:
        """Resolves GPS coordinates into corresponding Indian state."""
        # Gujarat: ~20.1 to 24.7 N, 68.1 to 74.5 E
        if 20.1 <= lat <= 24.7 and 68.1 <= lon <= 74.5:
            return "Gujarat", "Anand"
        # Punjab: ~29.5 to 32.5 N, 73.8 to 76.9 E
        elif 29.5 <= lat <= 32.5 and 73.8 <= lon <= 76.9:
            return "Punjab", "Ludhiana"
        # Haryana: ~27.6 to 30.9 N, 74.4 to 77.6 E
        elif 27.6 <= lat <= 30.9 and 74.4 <= lon <= 77.6:
            return "Haryana", "Karnal"
        # Maharashtra: ~15.6 to 22.0 N, 72.6 to 80.9 E
        elif 15.6 <= lat <= 22.0 and 72.6 <= lon <= 80.9:
            return "Maharashtra", "Pune"
        # Tamil Nadu: ~8.0 to 13.5 N, 76.2 to 80.3 E
        elif 8.0 <= lat <= 13.5 and 76.2 <= lon <= 80.3:
            return "Tamil Nadu", "Coimbatore"
        # Karnataka: ~11.5 to 18.5 N, 74.0 to 78.6 E
        elif 11.5 <= lat <= 18.5 and 74.0 <= lon <= 78.6:
            return "Karnataka", "Dharwad"
        # Kerala: ~8.3 to 12.8 N, 74.8 to 77.4 E
        elif 8.3 <= lat <= 12.8 and 74.8 <= lon <= 77.4:
            return "Kerala", "Palakkad"
        # Andhra Pradesh & Telangana: ~12.6 to 19.9 N, 76.7 to 84.8 E
        elif 12.6 <= lat <= 19.9 and 76.7 <= lon <= 84.8:
            return "Andhra Pradesh", "Guntur"
        # West Bengal: ~21.5 to 27.2 N, 85.8 to 89.9 E
        elif 21.5 <= lat <= 27.2 and 85.8 <= lon <= 89.9:
            return "West Bengal", "Purba Bardhaman"
        # Uttar Pradesh: ~23.8 to 30.4 N, 77.1 to 84.6 E
        elif 23.8 <= lat <= 30.4 and 77.1 <= lon <= 84.6:
            return "Uttar Pradesh", "Lucknow"
        # Madhya Pradesh: ~21.1 to 26.9 N, 74.0 to 82.8 E
        elif 21.1 <= lat <= 26.9 and 74.0 <= lon <= 82.8:
            return "Madhya Pradesh", "Indore"
        # Rajasthan: ~23.0 to 30.2 N, 69.5 to 78.3 E
        elif 23.0 <= lat <= 30.2 and 69.5 <= lon <= 78.3:
            return "Rajasthan", "Jaipur"
        # Bihar: ~24.3 to 27.5 N, 83.3 to 88.3 E
        elif 24.3 <= lat <= 27.5 and 83.3 <= lon <= 88.3:
            return "Bihar", "Patna"
        # Odisha: ~17.8 to 22.6 N, 81.4 to 87.5 E
        elif 17.8 <= lat <= 22.6 and 81.4 <= lon <= 87.5:
            return "Odisha", "Cuttack"
        # Assam: ~24.1 to 28.2 N, 89.7 to 96.0 E
        elif 24.1 <= lat <= 28.2 and 89.7 <= lon <= 96.0:
            return "Assam", "Jorhat"
        return None

    def _get_default_district_for_state(self, state: str) -> str:
        defaults = {
            "Gujarat": "Anand", "Maharashtra": "Pune", "Punjab": "Ludhiana",
            "Haryana": "Karnal", "Uttar Pradesh": "Lucknow", "Madhya Pradesh": "Indore",
            "Rajasthan": "Jaipur", "Karnataka": "Dharwad", "Andhra Pradesh": "Guntur",
            "Telangana": "Warangal", "Tamil Nadu": "Coimbatore", "Kerala": "Palakkad",
            "West Bengal": "Purba Bardhaman", "Bihar": "Patna", "Odisha": "Cuttack",
            "Assam": "Jorhat", "Chhattisgarh": "Raipur", "Jharkhand": "Ranchi",
            "Himachal Pradesh": "Kangra", "Uttarakhand": "Dehradun", "Jammu and Kashmir": "Srinagar",
            "Ladakh": "Leh", "Goa": "North Goa", "Manipur": "Imphal",
            "Meghalaya": "East Khasi Hills", "Mizoram": "Aizawl", "Nagaland": "Kohima",
            "Sikkim": "East Sikkim", "Tripura": "West Tripura", "Arunachal Pradesh": "Papum Pare",
            "Delhi": "New Delhi", "Puducherry": "Puducherry", "Chandigarh": "Chandigarh"
        }
        return defaults.get(state, "Anand")

    def get_regional_agro_profile(self, state: str, district: str) -> Dict[str, Any]:
        """Provides authoritative state-specific agricultural profiles for ALL 28 States + UTs."""
        st = self._normalize_state_name(state) or state
        st_lower = st.lower()

        profiles = {
            "gujarat": {
                "state": "Gujarat",
                "district": district,
                "authorities": "Anand Agricultural University (AAU), Junagadh Agricultural University (JAU), NAU Navsari, SDAU Dantiwada & ICAR-ATARI Zone VIII",
                "portal_scheme": "Gujarat i-Khedut Portal & Mukhyamantri Kisan Sahay Yojana",
                "soil_context": "Medium Black Cotton Soils, Sandy Loam (Goradu), Coastal Alluvium",
                "climate_zone": "Saurashtra, Middle & North Gujarat Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Gujarat"
            },
            "maharashtra": {
                "state": "Maharashtra",
                "district": district,
                "authorities": "MPKV Rahuri, VNMKV Parbhani, Dr. PDKV Akola, Dr. BSKKV Dapoli & ICAR Maharashtra",
                "portal_scheme": "MahaDBT Farmer Portal & Nanaji Deshmukh Krishi Sanjivani Yojana (PoCRA)",
                "soil_context": "Deep Black Clay Soils (Regur), Medium Loam, Lateritic Coastal Soil",
                "climate_zone": "Western Maharashtra, Marathwada & Vidarbha Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Maharashtra"
            },
            "punjab": {
                "state": "Punjab",
                "district": district,
                "authorities": "Punjab Agricultural University (PAU) Ludhiana, GADVASU & ICAR-ATARI Zone I",
                "portal_scheme": "Punjab Agriculture & Farmers Welfare Department Portal & PAU Kisan App",
                "soil_context": "Alluvial Loam Soils (Indo-Gangetic Plain), Sandy Loam",
                "climate_zone": "Trans-Gangetic Plains Regional Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Punjab"
            },
            "haryana": {
                "state": "Haryana",
                "district": district,
                "authorities": "Chaudhary Charan Singh Haryana Agricultural University (CCS HAU) Hisar & ICAR-CSSRI Karnal",
                "portal_scheme": "Meri Fasal Mera Byora Portal & Bhavantar Bharpayee Yojana",
                "soil_context": "Alluvial Loam, Clay Loam, Saline-Alkaline Tracts",
                "climate_zone": "Western Indo-Gangetic Plain Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Haryana"
            },
            "uttar pradesh": {
                "state": "Uttar Pradesh",
                "district": district,
                "authorities": "CSAUK Kanpur, ANDUAT Ayodhya, SVPUAT Meerut, BUAT Banda & ICAR-IISR Lucknow",
                "portal_scheme": "UP Pardarshi Kisan Seva Yojana & Kisan Kalyan Mission",
                "soil_context": "Gangetic Alluvium, Loam, Sandy Loam, Bundelkhand Red & Black Soils",
                "climate_zone": "Upper, Middle & Eastern Gangetic Plains Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Uttar Pradesh"
            },
            "madhya pradesh": {
                "state": "Madhya Pradesh",
                "district": district,
                "authorities": "Jawaharlal Nehru Krishi Vishwa Vidyalaya (JNKVV) Jabalpur, RVSKVV Gwalior & ICAR-IISR Indore",
                "portal_scheme": "MP Kisan Kalyan Yojana & Bhavantar Bhugtan Portal",
                "soil_context": "Deep to Medium Black Cotton Soils (Malwa Plateau), Alluvial Soils (Chambal)",
                "climate_zone": "Central Plateau and Hills Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Madhya Pradesh"
            },
            "rajasthan": {
                "state": "Rajasthan",
                "district": district,
                "authorities": "SKRAU Bikaner, MPUAT Udaipur, SKNCOA Jobner, AU Kota, AU Jodhpur & ICAR-CAZRI Jodhpur",
                "portal_scheme": "RajKisan Sathi Portal & Mukhyamantri Krishak Sathi Yojana",
                "soil_context": "Desert Arid Sandy Soils, Brown Loam, Black Cotton Soils (Hadoti region)",
                "climate_zone": "Western Arid Region & Southern Humid Plain Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Rajasthan"
            },
            "karnataka": {
                "state": "Karnataka",
                "district": district,
                "authorities": "University of Agricultural Sciences (UAS) Bengaluru & UAS Dharwad, UHS Bagalkot & ICAR-ATARI Zone XI",
                "portal_scheme": "Karnataka Raitha Siri, FRUITS Portal & Raitha Samparka Kendras (RSK)",
                "soil_context": "Red Sandy Loam, Deep Black Soils (Deccan Trap), Coastal Laterite",
                "climate_zone": "Southern Transition & Northern Dry Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Karnataka"
            },
            "andhra pradesh": {
                "state": "Andhra Pradesh",
                "district": district,
                "authorities": "Acharya N.G. Ranga Agricultural University (ANGRAU) Guntur, Dr. YSRHU & ICAR-CTRI Rajahmundry",
                "portal_scheme": "YSR Rythu Bharosa & Rythu Bharosa Kendras (RBK)",
                "soil_context": "Deltaic Alluvium, Red Sandy Soils, Coastal Heavy Black Soils",
                "climate_zone": "Coastal Andhra & Rayalaseema Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Andhra Pradesh"
            },
            "telangana": {
                "state": "Telangana",
                "district": district,
                "authorities": "Professor Jayashankar Telangana State Agricultural University (PJTSAU) Hyderabad & ICAR-CRIDA",
                "portal_scheme": "Rythu Bandhu Scheme & Telangana Rythu Vedika",
                "soil_context": "Red Earths (Chalka), Medium to Deep Black Cotton Soils",
                "climate_zone": "Southern Telangana & Northern Telangana Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Telangana"
            },
            "tamil nadu": {
                "state": "Tamil Nadu",
                "district": district,
                "authorities": "Tamil Nadu Agricultural University (TNAU) Coimbatore, TANUVAS & ICAR-SBI Coimbatore",
                "portal_scheme": "Uzhavan Mobile App & Tamil Nadu Department of Agriculture Schemes",
                "soil_context": "Cauvery Deltaic Alluvial Soils, Red Loam, Black Soils",
                "climate_zone": "Cauvery Delta Zone & Southern Coastal Plains Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Tamil Nadu"
            },
            "kerala": {
                "state": "Kerala",
                "district": district,
                "authorities": "Kerala Agricultural University (KAU) Vellanikkara Thrissur, ICAR-CPCRI Kasaragod & ICAR-CTCRI",
                "portal_scheme": "Subhiksha Keralam Portal & Karshaka Mithram Portal",
                "soil_context": "Laterite Soils, Coastal Alluvium, Acidic Wetland Peaty Soils (Kari/Kuttanad)",
                "climate_zone": "Humid Tropics & Western Ghats Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Kerala"
            },
            "west bengal": {
                "state": "West Bengal",
                "district": district,
                "authorities": "Bidhan Chandra Krishi Viswavidyalaya (BCKV) Mohanpur, UBKV Cooch Behar & ICAR-CRIJAF",
                "portal_scheme": "Krishak Bandhu Portal & Bangla Shasya Bima",
                "soil_context": "Gangetic Alluvial Soils, Terai Soils, Coastal Saline Soil",
                "climate_zone": "Lower Gangetic Plains Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, West Bengal"
            },
            "bihar": {
                "state": "Bihar",
                "district": district,
                "authorities": "Bihar Agricultural University (BAU) Sabour, Dr. RPCAU Pusa Samastipur & ICAR-RCER Patna",
                "portal_scheme": "Bihar Krishi Portal (DBT Agriculture) & Mukhya Mantri Krishi Vikas Yojana",
                "soil_context": "Calcareous Alluvial Soils, Non-Calcareous Loamy Soils, Tal Soils",
                "climate_zone": "Middle Gangetic Plains (North & South Bihar) Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Bihar"
            },
            "odisha": {
                "state": "Odisha",
                "district": district,
                "authorities": "Odisha University of Agriculture and Technology (OUAT) Bhubaneswar & ICAR-NRRI Cuttack",
                "portal_scheme": "KALIA Scheme & Krushak Odisha Unified Portal",
                "soil_context": "Red & Yellow Soils, Coastal Alluvium, Black Soils (Hirakud Command)",
                "climate_zone": "Eastern Plateau and Hills & Coastal Plain Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Odisha"
            },
            "assam": {
                "state": "Assam",
                "district": district,
                "authorities": "Assam Agricultural University (AAU) Jorhat & ICAR-ATARI Zone VI Guwahati",
                "portal_scheme": "Mukhya Mantri Krishi Sa-Sajuli Yojana & Assam Agri Portal",
                "soil_context": "Brahmaputra Valley Alluvial Acidic Soils, Riverine Char Soils",
                "climate_zone": "Eastern Himalayan Region & Brahmaputra Valley Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Assam"
            },
            "chhattisgarh": {
                "state": "Chhattisgarh",
                "district": district,
                "authorities": "Indira Gandhi Krishi Vishwavidyalaya (IGKV) Raipur & ICAR Chhattisgarh KVKs",
                "portal_scheme": "Rajiv Gandhi Kisan Nyay Yojana & CG Kisaan Portal",
                "soil_context": "Matasi (Sandy Loam), Dorsa (Clay Loam), Kanhar (Heavy Deep Clay)",
                "climate_zone": "Eastern Plateau & Chhattisgarh Plains Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Chhattisgarh"
            },
            "jharkhand": {
                "state": "Jharkhand",
                "district": district,
                "authorities": "Birsa Agricultural University (BAU) Kanke Ranchi & ICAR-IIAB Ranchi",
                "portal_scheme": "Jharkhand Krishi Rin Mafi Yojana & Birsa Fasal Bima",
                "soil_context": "Red Sandy Soils (Tanr/Don upland-lowland system), Micaceous Soils",
                "climate_zone": "Chotanagpur Plateau Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Jharkhand"
            },
            "himachal pradesh": {
                "state": "Himachal Pradesh",
                "district": district,
                "authorities": "CSK HPKV Palampur & Dr. Y.S. Parmar University of Horticulture (UHF) Nauni Solan",
                "portal_scheme": "Prakritik Kheti Khushhal Kisan Yojana & HP Agriculture Portal",
                "soil_context": "Mountain Brown Soils, Podzolic Forest Soils, Sub-Montane Valley Soils",
                "climate_zone": "Western Himalayan Temperate & Sub-Temperate Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Himachal Pradesh"
            },
            "uttarakhand": {
                "state": "Uttarakhand",
                "district": district,
                "authorities": "G.B. Pant University of Agriculture and Technology (GBPUAT) Pantnagar & VCSGUUHF Bharsar",
                "portal_scheme": "Uttarakhand Organic Commodity Board & Pandit Deen Dayal Kisan Kalyan Yojana",
                "soil_context": "Tarai-Bhabar Alluvial Loam, Mountain Gravelly Soils",
                "climate_zone": "Western Himalayan Tarai & Hill Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Uttarakhand"
            },
            "jammu and kashmir": {
                "state": "Jammu and Kashmir",
                "district": district,
                "authorities": "SKUAST-Kashmir Shalimar & SKUAST-Jammu Chatha & ICAR-CITH Srinagar",
                "portal_scheme": "Holistic Agriculture Development Programme (HADP J&K) & Kisan Khidmat Portal",
                "soil_context": "Karewa Lacustrine Soils, Riverine Alluvium, Hill Loam",
                "climate_zone": "Western Himalayan Temperate & Sub-Tropical Jammu Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Jammu and Kashmir"
            },
            "goa": {
                "state": "Goa",
                "district": district,
                "authorities": "ICAR-Central Coastal Agricultural Research Institute (CCARI) Old Goa",
                "portal_scheme": "Goa Shetkari Adhar Scheme & Department of Agriculture Goa",
                "soil_context": "Coastal Laterite Soils, Alluvial Sandy Loam",
                "climate_zone": "West Coast Semi-Arid & Coastal Humid Agro-Climatic Zone",
                "weather_station": f"IMD Agromet Advisory - {district}, Goa"
            }
        }

        # Check matched profile
        for p_key, prof in profiles.items():
            if p_key in st_lower or st_lower in p_key:
                return prof

        # National / Regional Fallback for other states (Manipur, Tripura, Nagaland, Sikkim, etc.)
        return {
            "state": st,
            "district": district,
            "authorities": f"State Agricultural University (SAU), Central Agricultural University & ICAR KVK {district}",
            "portal_scheme": f"{st} State Agriculture Department & PM-Kisan Portal",
            "soil_context": f"Regional Alluvial, Loam and Cultivated Soil of {st}",
            "climate_zone": f"{st} Agro-Climatic Zone",
            "weather_station": f"IMD Agromet Advisory Service - {district}, {st}"
        }

geo_tracker = GeoTracker()
