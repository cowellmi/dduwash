package data

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type BayModel struct {
	pool *pgxpool.Pool
}

type Bay struct {
	BayID  string `json:"bay_id"`
	Status string `json:"status"`
}

// Map datbase values to human readable
var StatusMap = map[int]string{
	0: "Empty",
	1: "Occupied",
	2: "Down",
}

var BayIDMap = map[string]string{
	"washbay1": "Washbay 1",
	"washbay2": "Washbay 2",
	"washbay3": "Washbay 3",
	"washbay4": "Washbay 4",
	"washbay5": "Washbay 5",
	"washbay6": "Washbay 6",
}

// Latest bay status for all bays plus the last updated time
func (m BayModel) GetLatest() ([]*Bay, time.Time, error) {
	sql := `
		SELECT DISTINCT ON (bay_id) time, bay_id, status_code
		FROM bay_status
		ORDER BY bay_id, time DESC;`

	ctx, cancel := context.WithTimeout(context.Background(), ctxTimeout)
	defer cancel()

	rows, err := m.pool.Query(ctx, sql)
	if err != nil {
		return nil, time.Time{}, err
	}
	defer rows.Close()

	var times []time.Time
	var results []*Bay
	for rows.Next() {
		var t time.Time
		var bayID string
		var statusCode int

		err := rows.Scan(&t, &bayID, &statusCode)
		if err != nil {
			return nil, time.Time{}, err
		}

		var b Bay
		var ok bool

		b.BayID, ok = BayIDMap[bayID]
		if !ok {
			return nil, time.Time{}, fmt.Errorf("invalid bay_id: %d", statusCode)
		}

		b.Status, ok = StatusMap[statusCode]
		if !ok {
			return nil, time.Time{}, fmt.Errorf("invalid status_code: %d", statusCode)
		}

		times = append(times, t)
		results = append(results, &b)
	}

	var last time.Time
	for i, t := range times {
		if i == 0 || t.After(last) {
			last = t
		}
	}

	return results, last, nil
}
