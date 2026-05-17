package main

import (
	"context"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
	"github.com/jackc/pgx/v5/pgxpool"
)

var (
	rawQuery = db.RawQuery
	dbPool   = db.Pool
)

type rawQueryFunc func(context.Context, string, ...any) (*db.RawResult, error)
type dbPoolFunc func(context.Context) (*pgxpool.Pool, error)
