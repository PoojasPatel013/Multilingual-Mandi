-- Initialize database for Multilingual Mandi
-- This script sets up the initial database configuration

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create indexes for full-text search
-- These will be used for product search functionality
CREATE INDEX IF NOT EXISTS idx_products_search 
ON products USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Create indexes for geographic queries
-- These will be used for location-based searches
CREATE INDEX IF NOT EXISTS idx_users_location 
ON users USING btree(country, region, city);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_products_vendor_active 
ON products(vendor_id, is_active, created_at);

CREATE INDEX IF NOT EXISTS idx_negotiations_status_created 
ON negotiations(status, created_at);

CREATE INDEX IF NOT EXISTS idx_transactions_status_created 
ON transactions(status, created_at);

-- Set up initial configuration
INSERT INTO categories (id, name, slug, description, level, sort_order, is_active, created_at, updated_at)
VALUES 
    (uuid_generate_v4(), 'Electronics', 'electronics', 'Electronic devices and accessories', 0, 1, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Clothing', 'clothing', 'Apparel and fashion items', 0, 2, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Food & Beverages', 'food-beverages', 'Food items and drinks', 0, 3, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Home & Garden', 'home-garden', 'Home improvement and gardening supplies', 0, 4, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Books & Media', 'books-media', 'Books, movies, and media content', 0, 5, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Sports & Recreation', 'sports-recreation', 'Sports equipment and recreational items', 0, 6, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Health & Beauty', 'health-beauty', 'Health and beauty products', 0, 7, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Automotive', 'automotive', 'Vehicle parts and accessories', 0, 8, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Arts & Crafts', 'arts-crafts', 'Art supplies and craft materials', 0, 9, true, NOW(), NOW()),
    (uuid_generate_v4(), 'Other', 'other', 'Miscellaneous items', 0, 10, true, NOW(), NOW())
ON CONFLICT DO NOTHING;