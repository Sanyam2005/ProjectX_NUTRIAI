-- NutriAI reference PostgreSQL schema.
-- This file is auto-applied by docker-compose on first DB init.
-- The backend also calls SQLAlchemy `Base.metadata.create_all` on startup,
-- so this is mostly for reference / external tooling / dashboards.

CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(36) PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(1024),
    is_guest        BOOLEAN NOT NULL DEFAULT FALSE,
    entra_oid       VARCHAR(64) UNIQUE,
    password_hash   VARCHAR(255),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goals (
    id                  VARCHAR(36) PRIMARY KEY,
    user_id             VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    weight_kg           DOUBLE PRECISION,
    target_weight_kg    DOUBLE PRECISION,
    height_cm           DOUBLE PRECISION,
    age                 INTEGER,
    gender              VARCHAR(16),
    activity_level      VARCHAR(32) NOT NULL DEFAULT 'moderate',
    target_calories     INTEGER NOT NULL DEFAULT 2000,
    target_protein_g    INTEGER NOT NULL DEFAULT 80,
    target_carbs_g      INTEGER NOT NULL DEFAULT 250,
    target_fat_g        INTEGER NOT NULL DEFAULT 65,
    target_fiber_g      INTEGER NOT NULL DEFAULT 30,
    target_water_ml     INTEGER NOT NULL DEFAULT 2500,
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meals (
    id              VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    meal_type       VARCHAR(32) NOT NULL DEFAULT 'lunch',
    image_url       VARCHAR(1024),
    notes           TEXT,
    consumed_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    calories        DOUBLE PRECISION NOT NULL DEFAULT 0,
    protein_g       DOUBLE PRECISION NOT NULL DEFAULT 0,
    carbs_g         DOUBLE PRECISION NOT NULL DEFAULT 0,
    fat_g           DOUBLE PRECISION NOT NULL DEFAULT 0,
    fiber_g         DOUBLE PRECISION NOT NULL DEFAULT 0,
    sugar_g         DOUBLE PRECISION NOT NULL DEFAULT 0,
    sodium_mg       DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_meals_user_consumed ON meals(user_id, consumed_at DESC);

CREATE TABLE IF NOT EXISTS meal_ingredients (
    id              VARCHAR(36) PRIMARY KEY,
    meal_id         VARCHAR(36) NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    position        INTEGER NOT NULL DEFAULT 0,
    name            VARCHAR(255) NOT NULL,
    weight_g        DOUBLE PRECISION NOT NULL DEFAULT 0,
    unit            VARCHAR(32) NOT NULL DEFAULT 'g',
    confidence      DOUBLE PRECISION NOT NULL DEFAULT 0,
    calories        DOUBLE PRECISION NOT NULL DEFAULT 0,
    protein_g       DOUBLE PRECISION NOT NULL DEFAULT 0,
    carbs_g         DOUBLE PRECISION NOT NULL DEFAULT 0,
    fat_g           DOUBLE PRECISION NOT NULL DEFAULT 0,
    fiber_g         DOUBLE PRECISION NOT NULL DEFAULT 0,
    sugar_g         DOUBLE PRECISION NOT NULL DEFAULT 0,
    sodium_mg       DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ingredients_meal ON meal_ingredients(meal_id);

CREATE TABLE IF NOT EXISTS daily_nutrition (
    id          VARCHAR(36) PRIMARY KEY,
    user_id     VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day         DATE NOT NULL,
    calories    DOUBLE PRECISION NOT NULL DEFAULT 0,
    protein_g   DOUBLE PRECISION NOT NULL DEFAULT 0,
    carbs_g     DOUBLE PRECISION NOT NULL DEFAULT 0,
    fat_g       DOUBLE PRECISION NOT NULL DEFAULT 0,
    fiber_g     DOUBLE PRECISION NOT NULL DEFAULT 0,
    water_ml    DOUBLE PRECISION NOT NULL DEFAULT 0,
    CONSTRAINT uq_daily_user_day UNIQUE (user_id, day)
);

CREATE TABLE IF NOT EXISTS water_logs (
    id              VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_ml       DOUBLE PRECISION NOT NULL,
    recorded_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_water_user_recorded ON water_logs(user_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS weight_history (
    id              VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    weight_kg       DOUBLE PRECISION NOT NULL,
    recorded_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_weight_user_recorded ON weight_history(user_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS achievements (
    id              VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code            VARCHAR(64) NOT NULL,
    title           VARCHAR(128) NOT NULL,
    description     TEXT,
    icon            VARCHAR(64),
    earned_at       TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id);

CREATE TABLE IF NOT EXISTS reminder_settings (
    id                 VARCHAR(36) PRIMARY KEY,
    user_id            VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    breakfast_enabled  BOOLEAN NOT NULL DEFAULT TRUE,
    breakfast_time     VARCHAR(5)  NOT NULL DEFAULT '08:30',
    lunch_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    lunch_time         VARCHAR(5)  NOT NULL DEFAULT '13:00',
    dinner_enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    dinner_time        VARCHAR(5)  NOT NULL DEFAULT '20:00',
    water_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    water_every_min    INTEGER NOT NULL DEFAULT 120,
    log_enabled        BOOLEAN NOT NULL DEFAULT TRUE,
    log_time           VARCHAR(5)  NOT NULL DEFAULT '21:30',
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS challenge_participants (
    id                  VARCHAR(36) PRIMARY KEY,
    user_id             VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_code      VARCHAR(64) NOT NULL,
    joined_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_participant_user_code UNIQUE (user_id, challenge_code)
);
CREATE INDEX IF NOT EXISTS idx_participants_user ON challenge_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_participants_code ON challenge_participants(challenge_code);
