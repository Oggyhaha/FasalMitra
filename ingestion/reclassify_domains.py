#!/usr/bin/env python3
"""
Re-classify existing chunks into proper domains and improve retrieval
"""

import json
from pathlib import Path

def classify_domain_from_content(text: str) -> tuple:
    """Better domain classification based on content keywords."""
    text_lower = text.lower()
    
    # Domain keywords with weights
    domain_keywords = {
        "livestock": ["livestock", "पशु", "मवेशी", "पशुपालन", "dairy", "दुग्ध", "गोपालन", "cattle", "भैंस", "बकरी", "भेड़", "पोल्ट्री", "मुर्गी", "fisheries", "मछली", "मत्स्य", "aquaculture", "animal husbandry", "milk production", "poultry farming"],
        "fruits": ["fruit", "फल", "horticulture", "बागवानी", "mango", "आम", "केला", "banana", "पपीता", "papaya", "अनार", "guava", "अमरूद", "संतरा", "orange", "नींबू", "lemon", "लीची", "litchi", "coconut", "नारियल", "sapota", "chiku", "pomegranate", "anarc"],
        "vegetables": ["vegetable", "सब्जी", "भाजी", "tomato", "टमाटर", "प्याज", "onion", "आलू", "potato", "मिर्च", "chilli", "बैंगन", "brinjal", "भिंडी", "okra", "कद्दू", "pumpkin", "लौकी", "cabbage", "cauliflower", "spinach", "पालक"],
        "weather": ["weather", "मौसम", "हवामान", "rainfall", "वर्षा", "बारिश", "temperature", "तापमान", "humidity", "आर्द्रता", "forecast", "पूर्वानुमान", "agromet", "कृषि मौसम", "monsoon", "मानसून", "rain", "ड्राउट", "drought"],
        "market": ["market", "मंडी", "बाजार", "price", "भाव", "कीमत", "rate", "दर", "arrival", "आवक", "mandi", "procurement", "खरीद", "MSP", "न्यूनतम समर्थन मूल्य", "wholesale", "retail", "market price", "commodity price"],
        "schemes": ["scheme", "योजना", "स्कीम", "subsidy", "सब्सिडी", "अनुदान", "loan", "ऋण", "insurance", "बीमा", "कृषि बीमा", "PM-KISAN", "किसान सम्मान", "किसान क्रेडिट", "fasal bima", "प्रधानमंत्री", "सरकारी योजना", "subsidy scheme"],
        "soil_water": ["soil", "मिट्टी", "माती", "water", "पानी", "पाणी", "irrigation", "सिंचाई", "fertilizer", "उर्वरक", "खाद", "nutrient", "पोषक", "organic", "जैविक", "vermicompost", "compost", "drip irrigation", "sprinkler", "soil health", "soil testing"],
        "crops": ["crop", "पिक", "फसल", "kheti", "खेती", "cultivation", "खेतीबाड़ी", "sowing", "बुआई", "harvest", "कटाई", "yield", "उत्पादन", "उत्पन्न", "variety", "किस्म", "seed", "बीज", "wheat", "गेहूं", "rice", "धान", "चावल", "cotton", "कपास", "soybean", "सोयाबीन", "maize", "मक्का", "chickpea", "चना", "groundnut", "मूंगफली", "mustard", "सरसों"],
    }
    
    scores = {}
    for domain, keywords in domain_keywords.items():
        scores[domain] = sum(2 if kw in text_lower else 0 for kw in keywords)
    
    primary_domain = max(scores, key=scores.get) if max(scores.values()) > 0 else "crops"
    
    # Subdomain detection
    subdomain = ""
    if primary_domain == "crops":
        if any(k in text_lower for k in ["wheat", "गेहूं", "rice", "धान", "paddy"]): subdomain = "cereals"
        elif any(k in text_lower for k in ["cotton", "कपास"]): subdomain = "fiber"
        elif any(k in text_lower for k in ["soybean", "सोयाबीन", "groundnut", "mustard"]): subdomain = "oilseeds"
        elif any(k in text_lower for k in ["chickpea", "चना", "pigeonpea", "अरहर"]): subdomain = "pulses"
    elif primary_domain == "livestock":
        if any(k in text_lower for k in ["dairy", "milk", "दूध"]): subdomain = "dairy"
        elif any(k in text_lower for k in ["poultry", "मुर्गी", "chicken"]): subdomain = "poultry"
        elif any(k in text_lower for k in ["goat", "बकरी", "sheep", "भेड़"]): subdomain = "small_ruminants"
    
    return primary_domain, subdomain


def reclassify_chunks():
    input_file = Path("extracted_chunks.jsonl")
    output_file = Path("extracted_chunks_reclassified.jsonl")
    
    count = 0
    domains = {}
    
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            if not line.strip():
                continue
            chunk = json.loads(line)
            
            # Re-classify
            domain, subdomain = classify_domain_from_content(chunk.get("content", "") + " " + chunk.get("title", ""))
            
            chunk["domain"] = domain
            chunk["subdomain"] = subdomain
            
            domains[domain] = domains.get(domain, 0) + 1
            count += 1
            
            outfile.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    
    print(f"Reclassified {count} chunks")
    print(f"Domain distribution: {domains}")
    return output_file


if __name__ == "__main__":
    reclassify_chunks()