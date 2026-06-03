// murakumo-netd builds the small WireGuard overlay needed by the Mac mini
// k3s GPU fleet. It intentionally does not implement Tailscale-scale NAT
// traversal, ACLs, DNS, or relay behavior; the fleet is LAN-local.
package main

import (
	"bytes"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"golang.org/x/crypto/curve25519"
)

const (
	defaultStateDir            = "/etc/murakumo-netd"
	defaultPrivateKeyFile      = "/etc/murakumo-netd/privatekey"
	defaultInventoryFile       = "/etc/murakumo-netd/nodes.json"
	defaultWireGuardConfigFile = "/etc/wireguard/wg0.conf"
	defaultInterface           = "wg0"
	defaultListenPort          = 51820
	defaultPersistentKeepalive = 25
	defaultOverlayPrefix       = "10.77.0"
	defaultOverlayPrefixLength = 24
	defaultK3sClusterCIDR      = "10.42.0.0/16"
	defaultK3sServiceCIDR      = "10.43.0.0/16"
)

type Node struct {
	Name      string `json:"name"`
	Endpoint  string `json:"endpoint"`
	OverlayIP string `json:"overlay_ip"`
	PodCIDR   string `json:"pod_cidr,omitempty"`
	PublicKey string `json:"public_key,omitempty"`
}

type Inventory struct {
	Nodes []Node `json:"nodes"`
}

type KeyPair struct {
	PrivateKey string `json:"private_key"`
	PublicKey  string `json:"public_key"`
}

var defaultFleet = []Node{
	{Name: "jacob", Endpoint: "192.168.1.37", OverlayIP: "10.77.0.1"},
	{Name: "dan", Endpoint: "192.168.1.52", OverlayIP: "10.77.0.2"},
	{Name: "simeon", Endpoint: "192.168.1.59", OverlayIP: "10.77.0.3"},
	{Name: "naphtali", Endpoint: "192.168.1.64", OverlayIP: "10.77.0.4"},
	{Name: "levi", Endpoint: "192.168.1.65", OverlayIP: "10.77.0.5"},
	{Name: "benjamin", Endpoint: "192.168.1.51", OverlayIP: "10.77.0.6"},
	{Name: "joseph", Endpoint: "192.168.1.49", OverlayIP: "10.77.0.7"},
	{Name: "judah", Endpoint: "192.168.1.61", OverlayIP: "10.77.0.8"},
	{Name: "issachar", Endpoint: "192.168.1.60", OverlayIP: "10.77.0.9"},
	{Name: "zebulun", Endpoint: "192.168.1.67", OverlayIP: "10.77.0.10"},
	{Name: "asher", Endpoint: "192.168.1.54", OverlayIP: "10.77.0.11"},
}

func main() {
	log.SetFlags(0)
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}

	var err error
	switch os.Args[1] {
	case "keygen":
		err = cmdKeygen(os.Args[2:])
	case "ensure-key":
		err = cmdEnsureKey(os.Args[2:])
	case "inventory-template":
		err = cmdInventoryTemplate(os.Args[2:])
	case "render":
		err = cmdRender(os.Args[2:])
	case "apply":
		err = cmdApply(os.Args[2:])
	case "status":
		err = cmdStatus(os.Args[2:])
	case "k3s-args":
		err = cmdK3sArgs(os.Args[2:])
	default:
		usage()
		err = fmt.Errorf("unknown command: %s", os.Args[1])
	}
	if err != nil {
		log.Fatal(err)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, `murakumo-netd manages the murakumo WireGuard overlay.

Commands:
  keygen             Generate a WireGuard-compatible keypair as JSON
  ensure-key         Create a private key file if absent and print the public key
  inventory-template Print the default 11-node murakumo inventory JSON
  render             Render wg0.conf from inventory and local private key
  apply              Install a rendered config and restart wg-quick@iface
  status             Show wg status
  k3s-args           Print k3s flags for this node

`)
}

func cmdKeygen(args []string) error {
	fs := flag.NewFlagSet("keygen", flag.ExitOnError)
	_ = fs.Parse(args)

	kp, err := generateKeyPair()
	if err != nil {
		return err
	}
	return writeJSON(os.Stdout, kp)
}

func cmdEnsureKey(args []string) error {
	fs := flag.NewFlagSet("ensure-key", flag.ExitOnError)
	keyFile := fs.String("private-key-file", defaultPrivateKeyFile, "private key path")
	jsonOut := fs.Bool("json", false, "print keypair as JSON")
	_ = fs.Parse(args)

	priv, err := ensurePrivateKey(*keyFile)
	if err != nil {
		return err
	}
	pub, err := publicKey(priv)
	if err != nil {
		return err
	}
	if *jsonOut {
		return writeJSON(os.Stdout, KeyPair{PrivateKey: priv, PublicKey: pub})
	}
	fmt.Println(pub)
	return nil
}

func cmdInventoryTemplate(args []string) error {
	fs := flag.NewFlagSet("inventory-template", flag.ExitOnError)
	out := fs.String("out", "-", "output path, or - for stdout")
	_ = fs.Parse(args)

	var buf bytes.Buffer
	if err := writeJSON(&buf, Inventory{Nodes: defaultFleet}); err != nil {
		return err
	}
	return writeFileOrStdout(*out, buf.Bytes(), 0644)
}

func cmdRender(args []string) error {
	fs := flag.NewFlagSet("render", flag.ExitOnError)
	nodeName := fs.String("node", "", "local node name")
	inventoryFile := fs.String("inventory", defaultInventoryFile, "nodes JSON path")
	keyFile := fs.String("private-key-file", defaultPrivateKeyFile, "private key path")
	out := fs.String("out", "-", "output path, or - for stdout")
	iface := fs.String("iface", defaultInterface, "WireGuard interface")
	listenPort := fs.Int("listen-port", defaultListenPort, "WireGuard listen port")
	keepalive := fs.Int("persistent-keepalive", defaultPersistentKeepalive, "peer persistent keepalive seconds")
	_ = fs.Parse(args)

	if *nodeName == "" {
		return errors.New("-node is required")
	}
	inv, err := loadInventory(*inventoryFile)
	if err != nil {
		return err
	}
	self, err := inv.find(*nodeName)
	if err != nil {
		return err
	}
	priv, err := readTrimmed(*keyFile)
	if err != nil {
		return err
	}
	if _, err := publicKey(priv); err != nil {
		return fmt.Errorf("invalid private key %s: %w", *keyFile, err)
	}
	rendered, err := renderWGConfig(inv, self, priv, *iface, *listenPort, *keepalive)
	if err != nil {
		return err
	}
	return writeFileOrStdout(*out, []byte(rendered), 0600)
}

func cmdApply(args []string) error {
	fs := flag.NewFlagSet("apply", flag.ExitOnError)
	config := fs.String("config", defaultWireGuardConfigFile, "WireGuard config to apply")
	iface := fs.String("iface", defaultInterface, "WireGuard interface")
	dryRun := fs.Bool("dry-run", false, "print commands without running them")
	_ = fs.Parse(args)

	configInfo, err := os.Stat(*config)
	if err != nil {
		return err
	}
	configDir := filepath.Dir(defaultWireGuardConfigFile)
	target := filepath.Join(configDir, *iface+".conf")
	commands := [][]string{
		{"install", "-d", "-m", "0700", configDir},
		{"systemctl", "enable", "wg-quick@" + *iface},
		{"systemctl", "restart", "wg-quick@" + *iface},
	}
	targetInfo, err := os.Stat(target)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	if targetInfo == nil || !os.SameFile(configInfo, targetInfo) {
		commands = append(commands[:1], append([][]string{
			{"install", "-m", "0600", *config, target},
		}, commands[1:]...)...)
	}
	for _, c := range commands {
		if *dryRun {
			fmt.Println(shellQuote(c))
			continue
		}
		if err := run(c[0], c[1:]...); err != nil {
			return err
		}
	}
	return nil
}

func cmdStatus(args []string) error {
	fs := flag.NewFlagSet("status", flag.ExitOnError)
	iface := fs.String("iface", defaultInterface, "WireGuard interface")
	_ = fs.Parse(args)
	return run("wg", "show", *iface)
}

func cmdK3sArgs(args []string) error {
	fs := flag.NewFlagSet("k3s-args", flag.ExitOnError)
	nodeName := fs.String("node", "", "local node name")
	inventoryFile := fs.String("inventory", defaultInventoryFile, "nodes JSON path")
	server := fs.Bool("server", false, "print server flags instead of agent flags")
	iface := fs.String("iface", defaultInterface, "overlay interface")
	clusterCIDR := fs.String("cluster-cidr", defaultK3sClusterCIDR, "k3s cluster CIDR")
	serviceCIDR := fs.String("service-cidr", defaultK3sServiceCIDR, "k3s service CIDR")
	_ = fs.Parse(args)

	if *nodeName == "" {
		return errors.New("-node is required")
	}
	inv, err := loadInventory(*inventoryFile)
	if err != nil {
		return err
	}
	self, err := inv.find(*nodeName)
	if err != nil {
		return err
	}
	common := []string{
		"--node-name", self.Name,
		"--node-ip", self.OverlayIP,
		"--flannel-iface", *iface,
	}
	if *server {
		common = append(common,
			"--advertise-address", self.OverlayIP,
			"--cluster-cidr", *clusterCIDR,
			"--service-cidr", *serviceCIDR,
			"--write-kubeconfig-mode=644",
			"--disable=traefik",
			"--disable=servicelb",
		)
	}
	fmt.Println(strings.Join(common, " "))
	return nil
}

func generateKeyPair() (KeyPair, error) {
	priv := make([]byte, curve25519.ScalarSize)
	if _, err := rand.Read(priv); err != nil {
		return KeyPair{}, err
	}
	pub, err := curve25519.X25519(priv, curve25519.Basepoint)
	if err != nil {
		return KeyPair{}, err
	}
	return KeyPair{
		PrivateKey: base64.StdEncoding.EncodeToString(priv),
		PublicKey:  base64.StdEncoding.EncodeToString(pub),
	}, nil
}

func publicKey(private string) (string, error) {
	priv, err := base64.StdEncoding.DecodeString(strings.TrimSpace(private))
	if err != nil {
		return "", err
	}
	if len(priv) != curve25519.ScalarSize {
		return "", fmt.Errorf("expected %d private-key bytes, got %d", curve25519.ScalarSize, len(priv))
	}
	pub, err := curve25519.X25519(priv, curve25519.Basepoint)
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(pub), nil
}

func ensurePrivateKey(path string) (string, error) {
	if key, err := readTrimmed(path); err == nil {
		if _, err := publicKey(key); err != nil {
			return "", fmt.Errorf("existing key is invalid: %w", err)
		}
		return key, nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return "", err
	}

	kp, err := generateKeyPair()
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return "", err
	}
	if err := os.WriteFile(path, []byte(kp.PrivateKey+"\n"), 0600); err != nil {
		return "", err
	}
	return kp.PrivateKey, nil
}

func loadInventory(path string) (Inventory, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Inventory{}, err
	}
	var inv Inventory
	if err := json.Unmarshal(data, &inv); err != nil {
		return Inventory{}, err
	}
	if len(inv.Nodes) == 0 {
		return Inventory{}, errors.New("inventory has no nodes")
	}
	seenNames := map[string]bool{}
	seenIPs := map[string]bool{}
	for i, n := range inv.Nodes {
		if n.Name == "" {
			return Inventory{}, fmt.Errorf("nodes[%d].name is required", i)
		}
		if n.Endpoint == "" {
			return Inventory{}, fmt.Errorf("nodes[%d].endpoint is required", i)
		}
		if net.ParseIP(n.OverlayIP) == nil {
			return Inventory{}, fmt.Errorf("nodes[%d].overlay_ip is invalid: %q", i, n.OverlayIP)
		}
		if seenNames[n.Name] {
			return Inventory{}, fmt.Errorf("duplicate node name: %s", n.Name)
		}
		if seenIPs[n.OverlayIP] {
			return Inventory{}, fmt.Errorf("duplicate overlay ip: %s", n.OverlayIP)
		}
		if n.PodCIDR != "" {
			if _, _, err := net.ParseCIDR(n.PodCIDR); err != nil {
				return Inventory{}, fmt.Errorf("nodes[%d].pod_cidr is invalid: %q", i, n.PodCIDR)
			}
		}
		seenNames[n.Name] = true
		seenIPs[n.OverlayIP] = true
	}
	return inv, nil
}

func (inv Inventory) find(name string) (Node, error) {
	for _, n := range inv.Nodes {
		if n.Name == name {
			return n, nil
		}
	}
	return Node{}, fmt.Errorf("node %q not found in inventory", name)
}

func renderWGConfig(inv Inventory, self Node, privateKey, iface string, listenPort, keepalive int) (string, error) {
	var b strings.Builder
	fmt.Fprintf(&b, "# generated by murakumo-netd; iface=%s node=%s\n", iface, self.Name)
	fmt.Fprintln(&b, "[Interface]")
	fmt.Fprintf(&b, "Address = %s/%d\n", self.OverlayIP, defaultOverlayPrefixLength)
	fmt.Fprintf(&b, "ListenPort = %d\n", listenPort)
	fmt.Fprintf(&b, "PrivateKey = %s\n\n", strings.TrimSpace(privateKey))

	for _, peer := range inv.Nodes {
		if peer.Name == self.Name {
			continue
		}
		if peer.PublicKey == "" {
			return "", fmt.Errorf("peer %s is missing public_key", peer.Name)
		}
		if _, err := base64.StdEncoding.DecodeString(peer.PublicKey); err != nil {
			return "", fmt.Errorf("peer %s public_key is invalid: %w", peer.Name, err)
		}
		fmt.Fprintln(&b, "[Peer]")
		fmt.Fprintf(&b, "# %s\n", peer.Name)
		fmt.Fprintf(&b, "PublicKey = %s\n", peer.PublicKey)
		allowedIPs := []string{peer.OverlayIP + "/32"}
		if peer.PodCIDR != "" {
			allowedIPs = append(allowedIPs, peer.PodCIDR)
		}
		fmt.Fprintf(&b, "AllowedIPs = %s\n", strings.Join(allowedIPs, ", "))
		fmt.Fprintf(&b, "Endpoint = %s:%d\n", peer.Endpoint, listenPort)
		fmt.Fprintf(&b, "PersistentKeepalive = %d\n\n", keepalive)
	}
	return b.String(), nil
}

func readTrimmed(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(data)), nil
}

func writeJSON(w io.Writer, v any) error {
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}

func writeFileOrStdout(path string, data []byte, mode os.FileMode) error {
	if path == "-" {
		_, err := os.Stdout.Write(data)
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	return os.WriteFile(path, data, mode)
}

func run(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func shellQuote(args []string) string {
	quoted := make([]string, len(args))
	for i, arg := range args {
		quoted[i] = "'" + strings.ReplaceAll(arg, "'", "'\\''") + "'"
	}
	return strings.Join(quoted, " ")
}
