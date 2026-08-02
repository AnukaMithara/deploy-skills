CREATE TABLE IF NOT EXISTS deployment_probe (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
