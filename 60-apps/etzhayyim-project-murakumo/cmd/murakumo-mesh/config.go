package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// PeerConfig represents a WireGuard peer in the mesh.
type PeerConfig struct {
	Name      string `json:"name"`
	PublicKey string `json:"publicKey"` // base64
	Endpoint  string `json:"endpoint"`  // physical IP:port (e.g. 192.168.1.51:51820)
	WGAddr    string `json:"wgAddr"`    // overlay IP (e.g. 10.10.0.10)
}

// Config represents the local mesh configuration.
type Config struct {
	PrivateKey string       `json:"privateKey"` // base64
	PublicKey  string       `json:"publicKey"`  // base64 (derived, for display)
	WGAddr     string       `json:"wgAddr"`     // own overlay IP (e.g. 10.10.0.1)
	ListenPort int          `json:"listenPort"` // UDP port (default 51820)
	Peers      []PeerConfig `json:"peers"`
}

// configDir returns ~/.etzhayyim/mesh/.
func configDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".etzhayyim", "mesh")
}

// configPath returns ~/.etzhayyim/mesh/config.json.
func configPath() string {
	return filepath.Join(configDir(), "config.json")
}

// loadConfig reads config from disk.
func loadConfig() (*Config, error) {
	data, err := os.ReadFile(configPath())
	if err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}
	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("parse config: %w", err)
	}
	if cfg.ListenPort == 0 {
		cfg.ListenPort = 51820
	}
	return &cfg, nil
}

// saveConfig writes config to disk.
func saveConfig(cfg *Config) error {
	if err := os.MkdirAll(configDir(), 0700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(configPath(), data, 0600)
}
