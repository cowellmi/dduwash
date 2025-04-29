package main

import (
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// App router
func (app *application) routes() http.Handler {
	r := chi.NewRouter()

	fmt.Println(app.config.CorsTrustedOrigins)

	// Middleware
	r.Use(middleware.StripSlashes)
	r.Use(app.recovery)
	r.Use(app.enableCORS)
	r.Use(app.rateLimit)
	r.NotFound(app.handle(app.notFound))
	r.MethodNotAllowed(app.handle(app.methodNotAllowed))

	// API
	r.Route("/v1", func(r chi.Router) {
		r.Get("/healthcheck", app.handle(app.healthcheck))

		r.Route("/bays", func(r chi.Router) {
			r.Get("/status", app.handle(app.baysStatusGet))
			r.Get("/analytics", app.handle(app.baysAnalyticsGet))
		})
	})

	return r
}

func (app *application) notFound(w http.ResponseWriter, r *http.Request) error {
	return app.writeError(w, http.StatusNotFound, nil)
}

func (app *application) methodNotAllowed(w http.ResponseWriter, r *http.Request) error {
	return app.writeError(w, http.StatusMethodNotAllowed, nil)
}

func (app *application) healthcheck(w http.ResponseWriter, r *http.Request) error {
	env := "production"
	if app.config.Dev {
		env = "development"
	}

	data := envelope{
		"status": "available",
		"system_info": map[string]string{
			"environment": env,
			"version":     VERSION,
		},
	}

	return app.writeJSON(w, http.StatusOK, data, nil)
}

func (app *application) baysStatusGet(w http.ResponseWriter, r *http.Request) error {
	bays, last, err := app.models.Bay.GetLatest()
	if err != nil {
		return err
	}

	if !app.config.Dev && time.Since(last) > time.Hour*12 {
		return app.writeError(w, http.StatusUnprocessableEntity,
			"Bay status information is outdated and unavailable")
	}

	data := envelope{
		"bays": bays,
		"time": time.Now(),
	}

	return app.writeJSON(w, http.StatusOK, data, nil)
}

func (app *application) baysAnalyticsGet(w http.ResponseWriter, r *http.Request) error {
	return app.writeJSON(w, http.StatusOK, envelope{"analytics": nil}, nil)
}
