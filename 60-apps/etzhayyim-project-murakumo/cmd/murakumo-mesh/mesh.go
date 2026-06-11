package main

import (
	"fmt"
	"log"
	"net/netip"
	"strings"

	"golang.zx2c4.com/wireguard/conn"
	"golang.zx2c4.com/wireguard/device"
	"golang.zx2c4.com/wireguard/tun/netstack"
)

// MeshNet holds the WireGuard device and the userspace network stack.
type MeshNet struct {
	Device *device.Device
	Net    *netstack.Net
}

// startMesh creates a userspace WireGuard tunnel with netstack.
func startMesh(cfg *Config) (*MeshNet, error) {
	wgAddr, err := netip.ParseAddr(cfg.WGAddr)
	if err != nil {
		return nil, fmt.Errorf("parse wg addr %q: %w", cfg.WGAddr, err)
	}

	// Create userspace TUN + network stack (no root, no kernel TUN)
	tun, wgNet, err := netstack.CreateNetTUN(
		[]netip.Addr{wgAddr},
		nil,  // DNS (not needed)
		1420, // MTU
	)
	if err != nil {
		return nil, fmt.Errorf("create netstack tun: %w", err)
	}

	logger := device.NewLogger(device.LogLevelError, "mesh: ")

	dev := device.NewDevice(tun, conn.NewDefaultBind(), logger)

	// Build IPC config string
	ipcConf, err := buildIPC(cfg)
	if err != nil {
		tun.Close()
		return nil, fmt.Errorf("build ipc config: %w", err)
	}

	if err := dev.IpcSetOperation(strings.NewReader(ipcConf)); err != nil {
		tun.Close()
		return nil, fmt.Errorf("ipc set: %w", err)
	}

	if err := dev.Up(); err != nil {
		tun.Close()
		return nil, fmt.Errorf("device up: %w", err)
	}

	log.Printf("mesh: wireguard up on %s (port %d, %d peers)", cfg.WGAddr, cfg.ListenPort, len(cfg.Peers))

	return &MeshNet{Device: dev, Net: wgNet}, nil
}

// buildIPC constructs the IPC config string for wireguard-go.
// Keys must be hex-encoded, not base64.
func buildIPC(cfg *Config) (string, error) {
	privHex, err := b64ToHex(cfg.PrivateKey)
	if err != nil {
		return "", fmt.Errorf("private key: %w", err)
	}

	var b strings.Builder
	fmt.Fprintf(&b, "private_key=%s\n", privHex)
	fmt.Fprintf(&b, "listen_port=%d\n", cfg.ListenPort)

	for _, p := range cfg.Peers {
		pubHex, err := b64ToHex(p.PublicKey)
		if err != nil {
			return "", fmt.Errorf("peer %s public key: %w", p.Name, err)
		}
		fmt.Fprintf(&b, "public_key=%s\n", pubHex)
		fmt.Fprintf(&b, "endpoint=%s\n", p.Endpoint)
		fmt.Fprintf(&b, "allowed_ip=%s/32\n", p.WGAddr)
		fmt.Fprintf(&b, "persistent_keepalive_interval=25\n")
	}

	return b.String(), nil
}

// Close shuts down the WireGuard device.
func (m *MeshNet) Close() {
	m.Device.Close()
}
