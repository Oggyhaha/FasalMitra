#!/usr/bin/env python3
"""
Metadata Reviewer UI for FasalMitra PDF Ingestion
Streamlit app to review and fix extracted chunk metadata.
Usage: streamlit run ingestion/metadata_reviewer.py -- --input ./chunks.jsonl
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# Constants
# ============================================================

INDIAN_STATES = [
    "", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

CROPS = [
    "", "Rice", "Wheat", "Cotton", "Soybean", "Sugarcane", "Chickpea",
    "Maize", "Mustard", "Groundnut", "Sorghum", "Pearl Millet", "Finger Millet",
    "Barley", "Pigeonpea", "Greengram", "Blackgram", "General"
]

DOC_TYPES = ["advisory", "textbook", "thesis", "extension", "unknown"]

AUTHORITY_TIERS = [1, 2, 3, 4, 5]

LANGUAGES = ["en", "mr", "hi", "gu", "ta", "te", "kn", "ml", "bn", "pa", "or", "mixed", "unknown"]

SEASONS = ["", "Kharif", "Rabi", "Zaid", "Perennial"]


# ============================================================
# Data Loading
# ============================================================

@st.cache_data
def load_chunks(filepath: str) -> List[Dict[str, Any]]:
    chunks = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def save_chunks(chunks: List[Dict[str, Any]], filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


# ============================================================
# Streamlit UI
# ============================================================

def main():
    # Parse command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSONL file")
    args, _ = parser.parse_known_args()
    
    input_path = args.input
    output_path = input_path.replace(".jsonl", "_reviewed.jsonl")
    
    st.set_page_config(
        page_title="FasalMitra Metadata Reviewer",
        page_icon="🌾",
        layout="wide"
    )
    
    # Load data
    if "chunks" not in st.session_state:
        st.session_state.chunks = load_chunks(input_path)
        st.session_state.current_idx = 0
        st.session_state.reviewed = set()
    
    chunks = st.session_state.chunks
    idx = st.session_state.current_idx
    total = len(chunks)
    
    # Header
    st.title("🌾 FasalMitra - PDF Chunk Metadata Reviewer")
    st.caption(f"Reviewing: {Path(input_path).name} | Output: {Path(output_path).name}")
    
    # Progress bar
    reviewed_count = len(st.session_state.reviewed)
    progress = reviewed_count / total if total > 0 else 0
    st.progress(progress, text=f"Reviewed: {reviewed_count} / {total} ({progress*100:.1f}%)")
    
    # Navigation
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", disabled=idx == 0, use_container_width=True):
            st.session_state.current_idx = max(0, idx - 1)
            st.rerun()
    with col2:
        if st.button("Next ➡️", disabled=idx >= total - 1, use_container_width=True):
            st.session_state.current_idx = min(total - 1, idx + 1)
            st.rerun()
    with col3:
        # Jump to chunk
        new_idx = st.number_input("Go to chunk", min_value=1, max_value=total, value=idx+1, label_visibility="collapsed")
        if new_idx - 1 != idx:
            st.session_state.current_idx = new_idx - 1
            st.rerun()
    with col4:
        if st.button("💾 Save All", type="primary", use_container_width=True):
            save_chunks(chunks, output_path)
            st.success(f"Saved {len(chunks)} chunks to {output_path}")
    
    st.divider()
    
    if total == 0:
        st.warning("No chunks loaded!")
        return
    
    # Current chunk
    chunk = chunks[idx]
    
    # Chunk info header
    st.subheader(f"Chunk {idx+1} / {total} — `{chunk['chunk_id']}`")
    
    # Source info
    with st.expander("📄 Source Info", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.text(f"File: {chunk['source_file']}")
            st.text(f"Path: {chunk['source_path']}")
        with c2:
            st.text(f"Doc Type: {chunk['doc_type']}")
            st.text(f"Authority Tier: {chunk['authority_tier']}")
            st.text(f"Language: {chunk['language']}")
    
    # Editable metadata form
    st.markdown("### 🏷️ Metadata (Edit as Needed)")
    
    with st.form(f"chunk_form_{idx}"):
        col_left, col_right = st.columns(2)
        
        with col_left:
            crop = st.selectbox("Crop *", CROPS, index=CROPS.index(chunk.get("crop", "")) if chunk.get("crop", "") in CROPS else 0)
            variety = st.text_input("Variety", value=chunk.get("variety", ""))
            state = st.selectbox("State", INDIAN_STATES, index=INDIAN_STATES.index(chunk.get("state", "")) if chunk.get("state", "") in INDIAN_STATES else 0)
            district = st.text_input("District", value=chunk.get("district", ""))
            season = st.selectbox("Season", SEASONS, index=SEASONS.index(chunk.get("season", "")) if chunk.get("season", "") in SEASONS else 0)
        
        with col_right:
            doc_type = st.selectbox("Document Type", DOC_TYPES, index=DOC_TYPES.index(chunk.get("doc_type", "unknown")) if chunk.get("doc_type", "unknown") in DOC_TYPES else 0)
            authority_tier = st.selectbox("Authority Tier (1=Highest)", AUTHORITY_TIERS, index=AUTHORITY_TIERS.index(chunk.get("authority_tier", 3)))
            language = st.selectbox("Language", LANGUAGES, index=LANGUAGES.index(chunk.get("language", "unknown")) if chunk.get("language", "unknown") in LANGUAGES else 0)
            stage_min = st.number_input("Stage Min Days", min_value=0, max_value=365, value=chunk.get("stage_min_days", 0))
            stage_max = st.number_input("Stage Max Days", min_value=0, max_value=365, value=chunk.get("stage_max_days", 120))
        
        valid_from = st.text_input("Valid From (YYYY-MM-DD)", value=chunk.get("valid_from", "2024-01-01"))
        valid_until = st.text_input("Valid Until (YYYY-MM-DD)", value=chunk.get("valid_until", "2028-12-31"))
        
        # Entities display (read-only)
        with st.expander("🔍 Extracted Entities (Auto-detected)", expanded=False):
            ent = chunk.get("entities", {})
            st.json(ent)
        
        # Chunk text preview
        with st.expander("📝 Chunk Text Preview", expanded=True):
            st.text_area("Text", value=chunk.get("text", "")[:3000], height=200, disabled=True)
        
        # Actions
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            approved = st.form_submit_button("✅ Approve & Next", type="primary", use_container_width=True)
        with col_b:
            skip = st.form_submit_button("⏭️ Skip (Keep Original)", use_container_width=True)
        with col_c:
            delete = st.form_submit_button("🗑️ Delete Chunk", use_container_width=True)
        
        if approved:
            # Update chunk
            chunks[idx].update({
                "crop": crop,
                "variety": variety,
                "state": state,
                "district": district,
                "season": season,
                "doc_type": doc_type,
                "authority_tier": authority_tier,
                "language": language,
                "stage_min_days": stage_min,
                "stage_max_days": stage_max,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "reviewed": True,
                "reviewed_at": pd.Timestamp.now().isoformat()
            })
            st.session_state.reviewed.add(idx)
            if idx < total - 1:
                st.session_state.current_idx = idx + 1
            st.rerun()
        
        if skip:
            chunks[idx]["reviewed"] = True
            st.session_state.reviewed.add(idx)
            if idx < total - 1:
                st.session_state.current_idx = idx + 1
            st.rerun()
        
        if delete:
            chunks.pop(idx)
            st.session_state.chunks = chunks
            st.session_state.current_idx = min(idx, len(chunks) - 1)
            st.rerun()
    
    # Sidebar stats
    with st.sidebar:
        st.header("📊 Statistics")
        st.metric("Total Chunks", total)
        st.metric("Reviewed", reviewed_count)
        st.metric("Remaining", total - reviewed_count)
        
        if chunks:
            # Crop distribution
            crop_counts = {}
            for c in chunks:
                crop_counts[c.get("crop", "Unknown")] = crop_counts.get(c.get("crop", "Unknown"), 0) + 1
            
            st.subheader("Crops")
            for crop, count in sorted(crop_counts.items(), key=lambda x: -x[1])[:10]:
                st.text(f"  {crop}: {count}")
            
            # Language distribution
            lang_counts = {}
            for c in chunks:
                lang_counts[c.get("language", "Unknown")] = lang_counts.get(c.get("language", "Unknown"), 0) + 1
            
            st.subheader("Languages")
            for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
                st.text(f"  {lang}: {count}")


if __name__ == "__main__":
    main()