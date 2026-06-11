package main

import (
	"context"

	_ "github.com/etzhayyim/root/50-infra/spin-tinygo-flight/grpc"
	_ "github.com/etzhayyim/root/50-infra/spin-tinygo-flight/grpc/flight"
	flightsql "github.com/etzhayyim/root/50-infra/spin-tinygo-flight/grpc/flightsql"
)

func main() {
	_, _ = flightsql.Query(context.Background(), "select 1", flightsql.Options{})
}
