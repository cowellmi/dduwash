package main

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
)

const (
	RateLimitExceededMessage = "rate limit exceeded"
)

type envelope map[string]any

type withError func(w http.ResponseWriter, r *http.Request) error

// Wraps handleWithError as http.HandlerFunc, with error handling
func (app *application) handle(h withError) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if err := h(w, r); err != nil {
			app.serverErrorResponse(w, "handled unexpected error", err)
		}
	}
}

func (app *application) writeJSON(w http.ResponseWriter, statusCode int, data envelope, headers http.Header) error {
	js, err := json.MarshalIndent(data, "", "\t")
	if err != nil {
		return err
	}

	js = append(js, '\n')

	for key, value := range headers {
		w.Header()[key] = value
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	w.Write(js)

	return nil
}

func (app *application) writeError(w http.ResponseWriter, statusCode int, message any) error {
	if message == nil {
		message = http.StatusText(statusCode)
	}

	data := envelope{"error": message}

	return app.writeJSON(w, statusCode, data, nil)
}

func (app *application) errorResponse(w http.ResponseWriter, statusCode int, message any) {
	if message == nil {
		message = http.StatusText(statusCode)
	}

	data := envelope{"error": message}

	err := app.writeJSON(w, statusCode, data, nil)
	if err != nil {
		app.logger.Error("unable to write error response", slog.Any("err", err))
		w.WriteHeader(http.StatusInternalServerError)
	}
}

func (app *application) serverErrorResponse(w http.ResponseWriter, logMsg string, err error) {
	app.logger.Error(logMsg, slog.Any("err", err), slog.String("type", fmt.Sprintf("%T", err)))

	app.errorResponse(w, http.StatusInternalServerError, http.StatusText(http.StatusInternalServerError))
}
