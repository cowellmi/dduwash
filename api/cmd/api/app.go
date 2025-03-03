package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/micahco/dduwash/api/internal/data"
)

type application struct {
	config Config
	logger *slog.Logger
	models data.Models
}

func (app *application) listenAndServe(errLog *log.Logger) error {
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", app.config.Port),
		Handler:      app.routes(),
		ErrorLog:     errLog,
		IdleTimeout:  time.Minute,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	// Graceful shutdown
	shutdownError := make(chan error)
	go func() {
		// Intercept signals
		quit := make(chan os.Signal, 1)
		signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

		// Wait for shutdown signal (blocking)
		s := <-quit

		app.logger.Info("shutting down", slog.String("signal", s.String()))

		// Shutdown server
		app.logger.Info("shutdown server", slog.String("addr", srv.Addr))
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		err := srv.Shutdown(ctx)
		if err != nil {
			shutdownError <- err
		}

		shutdownError <- nil
	}()

	// Start web server
	app.logger.Info("starting server", slog.String("addr", srv.Addr))
	err := srv.ListenAndServe()
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}

	// Check if there were any shutdown errors
	err = <-shutdownError
	if err != nil {
		return err
	}

	app.logger.Info("shutdown complete")

	return nil
}
