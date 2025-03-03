CREATE TABLE IF NOT EXISTS bay_status (
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bay_id TEXT NOT NULL,
    status_code INT NOT NULL,
	PRIMARY KEY (time, bay_id)
);

CREATE EXTENSION IF NOT EXISTS timescaledb;

SELECT create_hypertable('bay_status', by_range('time'));

ALTER TABLE bay_status SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'bay_id'
);

CREATE INDEX status_idx
    ON bay_status (status_code);

CREATE INDEX bay_id_idx
    ON bay_status (bay_id);

CREATE UNIQUE INDEX time_bay_id_idx
    ON bay_status (time, bay_id);

-- TODO: created analytics continuous aggregate
