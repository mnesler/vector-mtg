-- Drop table if exists
DROP TABLE IF EXISTS cards;

-- Create cards table
CREATE TABLE cards (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mana_cost VARCHAR(100),
    cmc DECIMAL,
    type_line VARCHAR(255),
    oracle_text TEXT,
    colors TEXT[],
    color_identity TEXT[],
    rarity VARCHAR(20),
    set_code VARCHAR(10),
    released_at DATE,
    data JSONB,  -- Full card JSON for flexibility
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes (add after bulk load for better performance)
CREATE INDEX idx_cards_name ON cards(name);
CREATE INDEX idx_cards_type ON cards(type_line);
CREATE INDEX idx_cards_set ON cards(set_code);
CREATE INDEX idx_cards_rarity ON cards(rarity);
CREATE INDEX idx_cards_data_gin ON cards USING GIN(data jsonb_path_ops);
