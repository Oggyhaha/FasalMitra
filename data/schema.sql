-- FasalMitra Supabase PostgreSQL Database Schema

CREATE TABLE IF NOT EXISTS farmers (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    phone_number VARCHAR UNIQUE,
    preferred_language VARCHAR DEFAULT 'hi',
    state VARCHAR,
    district VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS farms (
    id VARCHAR PRIMARY KEY,
    farmer_id VARCHAR REFERENCES farmers(id) ON DELETE CASCADE,
    farm_name VARCHAR DEFAULT 'Main Farm',
    area_acres FLOAT DEFAULT 2.5,
    soil_type VARCHAR,
    district VARCHAR NOT NULL,
    state VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS crop_passports (
    id VARCHAR PRIMARY KEY,
    farm_id VARCHAR REFERENCES farms(id) ON DELETE CASCADE,
    crop_name VARCHAR NOT NULL,
    variety VARCHAR,
    sowing_date VARCHAR,
    stage_days INTEGER DEFAULT 30,
    season VARCHAR DEFAULT 'Kharif'
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id VARCHAR PRIMARY KEY,
    source_name VARCHAR NOT NULL,
    authority_tier INTEGER DEFAULT 1,
    title VARCHAR NOT NULL,
    crop VARCHAR,
    stage_min_days INTEGER DEFAULT 0,
    stage_max_days INTEGER DEFAULT 120,
    district VARCHAR,
    state VARCHAR,
    content TEXT NOT NULL,
    valid_from VARCHAR,
    valid_until VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR PRIMARY KEY,
    farmer_id VARCHAR REFERENCES farmers(id) ON DELETE CASCADE,
    channel VARCHAR DEFAULT 'PHONE',
    status VARCHAR DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR NOT NULL,
    raw_text TEXT NOT NULL,
    language VARCHAR DEFAULT 'hi',
    audio_url VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS escalations (
    id VARCHAR PRIMARY KEY,
    message_id VARCHAR NOT NULL,
    farmer_id VARCHAR NOT NULL,
    farmer_name VARCHAR,
    phone_number VARCHAR,
    district VARCHAR,
    crop VARCHAR,
    question TEXT NOT NULL,
    risk_level VARCHAR DEFAULT 'MEDIUM',
    reason VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'OPEN',
    retrieved_evidence JSON,
    expert_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id VARCHAR PRIMARY KEY,
    query_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    payload JSON NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Default Grounded Knowledge
INSERT INTO knowledge_documents (id, source_name, authority_tier, title, crop, district, state, content)
VALUES 
('DOC-KVK-LATUR-SOYBEAN-01', 'KVK Latur ICAR Advisory Bulletin', 1, 'Soybean Yellow Mosaic Virus & Whitefly Management', 'Soybean', 'Latur', 'Maharashtra', 'For yellowing in 30 to 45 day old soybean crop caused by Yellow Mosaic Virus transmitted by whiteflies, inspect whitefly population on lower leaves. If whiteflies exceed 5 per plant, spray Thiamethoxam 25% WG at 100g per hectare or Chlorantraniliprole 18.5% SC at 150ml in 500 liters of water per hectare. Ensure adequate soil moisture during spraying. Repeat spray after 12-15 days if infestation persists.'),
('DOC-ICAR-COTTON-BOLLWORM-02', 'ICAR-CICR Cotton Advisory', 1, 'Pink Bollworm & Sucking Pest Management in Kharif Cotton', 'Cotton', 'Nagpur', 'Maharashtra', 'To control Pink Bollworm infestation in 40 to 70 day old cotton crop, install pheromone traps at 5 traps per acre for monitoring. If trap catch exceeds 8 moths per night for 3 consecutive days, spray Emamectin Benzoate 5% SG at 220g per hectare or Spinetoram 11.7% SC at 420ml per hectare. Avoid indiscriminate organophosphate spraying to preserve natural predators.'),
('DOC-KVK-WHEAT-RUST-03', 'KVK Wheat Extension Guide', 1, 'Yellow Rust and Sowing Window Guidance for Wheat', 'Wheat', 'Indore', 'Madhya Pradesh', 'Optimum sowing window for irrigated wheat is November 1 to November 20. If yellow rust appears as bright yellow pustules on wheat leaves, spray Propiconazole 25% EC at 1 ml per liter of water (500 ml/ha) as soon as symptoms appear. Apply first irrigation at Crown Root Initiation (CRI) stage (21 days after sowing).')
ON CONFLICT (id) DO NOTHING;
