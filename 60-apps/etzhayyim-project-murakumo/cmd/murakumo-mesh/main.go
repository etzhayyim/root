// murakumo-mesh — Userspace WireGuard mesh for Nomad fleet.
//
// Creates a WireGuard overlay network using netstack (no root, no kernel TUN).
// Proxies Nomad RPC/HTTP/Serf traffic through the encrypted tunnel.
//
// Usage:
//
//	murakumo-mesh                  # Start mesh + proxy (reads ~/.etzhayyim/mesh/config.json)
//	murakumo-mesh keygen           # Generate keypair and print public key
//	murakumo-mesh init-fleet       # Generate config.json for the full fleet (server side)
//	murakumo-mesh init-client NAME # Generate config.json for a client node
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
)

// Fleet node definitions (physical IP → WireGuard overlay IP).
var fleetNodes = []struct {
	Name       string
	PhysicalIP string
	WGAddr     string
}{
	{"25mini", "192.168.1.37", "10.10.0.1"},
	{"benjamin", "192.168.1.51", "10.10.0.10"},
	{"joseph", "192.168.1.48", "10.10.0.11"},
	{"judah", "192.168.1.56", "10.10.0.12"},
	{"issachar", "192.168.1.57", "10.10.0.13"},
	{"dan", "192.168.1.52", "10.10.0.14"},
	{"simeon", "192.168.1.59", "10.10.0.15"},
	{"zebulun", "192.168.1.62", "10.10.0.16"},
	{"asher", "192.168.1.63", "10.10.0.17"},
	{"naphtali", "192.168.1.64", "10.10.0.18"},
	{"levi", "192.168.1.65", "10.10.0.19"},
}

// Nomad ports to proxy through WireGuard.
var nomadPorts = []int{4646, 4647, 4648}

// WireGuard UDP listen port.
const wgPort = 51820

// serverWGAddr is the Nomad server's WireGuard overlay IP.
const serverWGAddr = "10.10.0.1"

func main() {
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "keygen":
			cmdKeygen()
			return
		case "init-fleet":
			cmdInitFleet()
			return
		case "init-client":
			if len(os.Args) < 3 {
				log.Fatal("usage: murakumo-mesh init-client <node-name>")
			}
			cmdInitClient(os.Args[2])
			return
		}
	}
	cmdRun()
}

// cmdKeygen generates a new keypair and prints the public key.
func cmdKeygen() {
	priv, pub, err := generateKeypair()
	if err != nil {
		log.Fatalf("keygen: %v", err)
	}
	fmt.Printf("private: %s\npublic:  %s\n", priv, pub)
}

// cmdInitFleet generates config.json files for all fleet nodes.
// Outputs a directory of per-node configs with pre-generated keypairs.
func cmdInitFleet() {
	type nodeKey struct {
		Name string
		Priv string
		Pub  string
	}
	var keys []nodeKey
	for _, n := range fleetNodes {
		priv, pub, err := generateKeypair()
		if err != nil {
			log.Fatalf("keygen for %s: %v", n.Name, err)
		}
		keys = append(keys, nodeKey{n.Name, priv, pub})
	}

	for i, n := range fleetNodes {
		var peers []PeerConfig
		for j, p := range fleetNodes {
			if i == j {
				continue
			}
			peers = append(peers, PeerConfig{
				Name:      p.Name,
				PublicKey: keys[j].Pub,
				Endpoint:  fmt.Sprintf("%s:%d", p.PhysicalIP, wgPort),
				WGAddr:    p.WGAddr,
			})
		}
		cfg := Config{
			PrivateKey: keys[i].Priv,
			PublicKey:  keys[i].Pub,
			WGAddr:     n.WGAddr,
			ListenPort: wgPort,
			Peers:      peers,
		}
		data, _ := json.MarshalIndent(cfg, "", "  ")
		filename := fmt.Sprintf("mesh-%s.json", n.Name)
		if err := os.WriteFile(filename, data, 0600); err != nil {
			log.Fatalf("write %s: %v", filename, err)
		}
		fmt.Printf("%s: %s (pub: %s)\n", n.Name, filename, keys[i].Pub)
	}
	fmt.Println("\nDistribute each mesh-<name>.json to ~/.etzhayyim/mesh/config.json on the corresponding node.")
}

// cmdInitClient generates a config.json for a single client node.
// Requires the fleet config to already exist (reads peer public keys).
func cmdInitClient(name string) {
	var found bool
	for _, n := range fleetNodes {
		if n.Name == name {
			found = true
			break
		}
	}
	if !found {
		log.Fatalf("unknown node: %s", name)
	}

	priv, pub, err := generateKeypair()
	if err != nil {
		log.Fatalf("keygen: %v", err)
	}

	fmt.Printf("Generated keypair for %s:\n", name)
	fmt.Printf("  public:  %s\n", pub)
	fmt.Printf("  private: (saved to config)\n")
	fmt.Println("\nAdd this public key to other nodes' peer configs.")
	fmt.Printf("Then create ~/.etzhayyim/mesh/config.json with init-fleet output.\n")

	// Save minimal config (peers need to be filled from fleet config)
	for _, n := range fleetNodes {
		if n.Name == name {
			cfg := Config{
				PrivateKey: priv,
				PublicKey:  pub,
				WGAddr:     n.WGAddr,
				ListenPort: wgPort,
			}
			if err := saveConfig(&cfg); err != nil {
				log.Fatalf("save config: %v", err)
			}
			fmt.Printf("Config saved to %s\n", configPath())
			break
		}
	}
}

// cmdRun starts the mesh and proxy.
func cmdRun() {
	cfg, err := loadConfig()
	if err != nil {
		log.Fatalf("load config: %v\nRun 'murakumo-mesh init-fleet' to generate configs.", err)
	}

	mesh, err := startMesh(cfg)
	if err != nil {
		log.Fatalf("start mesh: %v", err)
	}
	defer mesh.Close()

	// Only start proxy on client nodes (non-server).
	// Server nodes don't need proxy — Nomad binds directly to WG addr.
	if cfg.WGAddr != serverWGAddr {
		_, err := startProxy(mesh.Net, serverWGAddr, nomadPorts)
		if err != nil {
			log.Fatalf("start proxy: %v", err)
		}
	}

	log.Println("mesh: running (ctrl-c to stop)")

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	log.Println("mesh: shutting down")
}
