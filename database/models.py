# ShiverTone - Database Models
# v0.1 - Initial schema

import sqlite3
import os

# Database file location
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shivertone.db')


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- PEDAL ENCYCLOPEDIA ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manufacturer TEXT,
            year_start INTEGER,
            year_end INTEGER,
            country_of_origin TEXT,
            description TEXT,
            circuit_type TEXT,        -- germanium, silicon, hybrid
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- SOLD LISTINGS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sold_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedal_id INTEGER,         -- links to pedals table
            title TEXT NOT NULL,
            sale_price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            sale_date TIMESTAMP,
            condition TEXT,           -- mint, excellent, good, fair, poor
            platform TEXT NOT NULL,   -- reverb, ebay, yahoo_japan, mercari_japan
            country TEXT,             -- US, UK, JP, DE etc
            listing_url TEXT,
            thumbnail_url TEXT,       -- first photo from listing
            thumbnail_saved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedal_id) REFERENCES pedals(id)
        )
    ''')

    # --- PHOTOS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedal_id INTEGER,
            sold_listing_id INTEGER,  -- if from a listing
            photo_type TEXT,          -- exterior, interior, pcb, detail, listing
            file_path TEXT,           -- local storage path
            source_url TEXT,          -- original URL
            caption TEXT,
            submitted_by TEXT,        -- community contribution
            approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedal_id) REFERENCES pedals(id),
            FOREIGN KEY (sold_listing_id) REFERENCES sold_listings(id)
        )
    ''')

    # --- PRICE ALERTS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedal_name TEXT NOT NULL,  -- search term
            threshold_price REAL,      -- null means notify on any sale
            platform TEXT DEFAULT 'all',
            notify_email TEXT,
            notify_telegram TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_triggered TIMESTAMP
        )
    ''')

    # --- COMMUNITY CONTRIBUTIONS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedal_id INTEGER,
            contribution_type TEXT,   -- photo, info, correction
            content TEXT,
            status TEXT DEFAULT 'pending',  -- pending, approved, rejected
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedal_id) REFERENCES pedals(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("ShiverTone database initialized successfully.")


if __name__ == "__main__":
    init_db()