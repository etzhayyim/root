package main

import (
	"context"

	_ "github.com/gftdcojp/spin-tinygo-flight/grpc"
	_ "github.com/gftdcojp/spin-tinygo-flight/grpc/flight"
	flightsql "github.com/gftdcojp/spin-tinygo-flight/grpc/flightsql"
)

func main() {
	_, _ = flightsql.Query(context.Background(), "select 1", flightsql.Options{})
}
