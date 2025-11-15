CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS videos (
    id                SERIAL PRIMARY KEY,
    user_id           INT NOT NULL REFERENCES users(id),
    s3_key            TEXT NOT NULL,
    video_title       TEXT,
    video_description TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
