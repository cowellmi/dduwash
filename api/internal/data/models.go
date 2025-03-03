package data

import (
	"errors"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

const ctxTimeout = 3 * time.Second

type Models struct {
	Bay BayModel
}

func New(pool *pgxpool.Pool) Models {
	return Models{
		Bay: BayModel{pool},
	}
}

// Sentinel models errors
var (
	ErrRecordNotFound = errors.New("models: no matching record found")
)
