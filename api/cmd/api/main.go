package main

import (
	"context"
	"log/slog"
	"os"
	"time"

	"github.com/caarlos0/env/v10"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/lmittmann/tint"
	"github.com/micahco/dduwash/api/internal/data"
)

var (
	BUILD_TIME string
	VERSION    string
)

type Config struct {
	DatabaseUrl        string   `env:"DATABASE_URL"`
	Port               int      `env:"API_PORT"`
	Dev                bool     `env:"API_DEV"`
	RateLimitRps       int      `env:"API_RL_RPS"`
	RateLimitMaxBurst  int      `env:"API_RL_BURST"`
	CorsTrustedOrigins []string `env:"API_CORS" envSeparator:","`
}

func main() {
	var config Config

	if err := env.Parse(&config); err != nil {
		slog.Error("err parsing config", "err", err)
		return
	}

	// Logger
	h := newSlogHandler(config)
	logger := slog.New(h)
	// Create error log for http.Server
	errLog := slog.NewLogLogger(h, slog.LevelError)

	// PostgreSQL
	pool, err := openPool(config.DatabaseUrl)
	if err != nil {
		logFatal(logger, err)
	}
	defer pool.Close()

	app := &application{
		config: config,
		logger: logger,
		models: data.New(pool),
	}

	err = app.listenAndServe(errLog)
	if err != nil {
		logFatal(logger, err)
	}
}

func openPool(dsn string) (*pgxpool.Pool, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, err
	}

	dbpool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, err
	}

	err = dbpool.Ping(ctx)
	if err != nil {
		return nil, err
	}

	return dbpool, err
}

func newSlogHandler(config Config) slog.Handler {
	if config.Dev {
		// Development text hanlder
		return tint.NewHandler(os.Stdout, &tint.Options{
			AddSource:  true,
			Level:      slog.LevelDebug,
			TimeFormat: time.Kitchen,
		})
	}

	// Production use JSON handler with default options
	return slog.NewJSONHandler(os.Stdout, nil)
}

func logFatal(logger *slog.Logger, err error) {
	logger.Error("fatal", slog.Any("err", err))
	os.Exit(1)
}
