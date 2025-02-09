-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Table 1: Investors
CREATE TABLE investors (
    id bigserial primary key,
    name text NOT NULL,
    website text,
    description text,
    location text,
    contact_email text,
    crawl_date timestamptz,
    created_at timestamptz DEFAULT now(),
    content_hash text,
    contact_phone text,
    contact_form_url text,
    investment_stages text[],
    check_size jsonb,
    industries text[],
    geographies text[],
    team jsonb,
    portfolio jsonb,
    preferred_contact_methods text[],
    investment_thesis text,
    status varchar NOT NULL,
    contact_name text,
    identified_email text
);

-- Table 2: Team Members
CREATE TABLE team_members (
    id bigserial primary key,
    investor_id bigint references investors(id) on delete cascade,
    name text NOT NULL,
    role text,
    linkedin_url text,
    focus_areas text[],
    created_at timestamptz DEFAULT now()
);

-- Table 3: Portfolio Companies
CREATE TABLE portfolio_companies (
    id bigserial primary key,
    investor_id bigint references investors(id) on delete cascade,
    name text NOT NULL,
    website text,
    industry text,
    description text,
    created_at timestamptz DEFAULT now(),
    investment_year varchar
);

-- Table 4: Investor Chunks
CREATE TABLE investor_chunks (
    id bigserial primary key,
    investor_id bigint references investors(id) on delete cascade,
    chunk_type text,
    chunk_text text NOT NULL,
    embedding vector(1536),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz DEFAULT now(),
    chunk_hash varchar
);

DROP INDEX IF EXISTS investor_chunks_embedding_idx;
SET maintenance_work_mem = '128MB';
-- Create indices
CREATE INDEX investor_chunks_embedding_idx
ON investor_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX investors_active_status_idx
ON investors (id) WHERE status = 'active';

-- Create similarity search function
CREATE OR REPLACE FUNCTION get_investor_leads(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
) RETURNS TABLE (
    investor_id bigint,
    name text,
    website text,
    description text,
    location text,
    contact_email text,
    contact_phone text,
    contact_name text,
    contact_form_url text,
    investment_stages text[],
    check_size jsonb,
    industries text[],
    geographies text[],
    investment_thesis text,
    similarity float
) LANGUAGE sql STABLE AS $$
    WITH top_chunks AS (
        SELECT DISTINCT ON (investor_id)
            investor_id,
            (1 - (embedding <=> query_embedding)) AS similarity
        FROM investor_chunks
        WHERE (1 - (embedding <=> query_embedding)) > match_threshold
        ORDER BY investor_id, similarity DESC
    )
    SELECT
        i.id AS investor_id,
        i.name,
        i.website,
        i.description,
        i.location,
        i.contact_email,
        i.contact_phone,
        i.contact_name,
        i.contact_form_url,
        i.investment_stages,
        i.check_size,
        i.industries,
        i.geographies,
        i.investment_thesis,
        tc.similarity
    FROM top_chunks tc
    JOIN investors i ON i.id = tc.investor_id
    WHERE i.status = 'active'
    ORDER BY tc.similarity DESC
    LIMIT match_count;
$$;
