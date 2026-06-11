# Build stage
FROM golang:1.25-alpine AS build
WORKDIR /src
RUN apk add --no-cache git ca-certificates
COPY go.mod go.sum* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags='-s -w' \
    -o /out/murakumo-kubelet ./cmd/murakumo-kubelet

# Runtime stage
FROM gcr.io/distroless/static:nonroot
COPY --from=build /out/murakumo-kubelet /murakumo-kubelet
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
USER nonroot
ENTRYPOINT ["/murakumo-kubelet"]
