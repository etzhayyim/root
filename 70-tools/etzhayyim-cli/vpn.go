package main

// `gftd vpn` — WireGuard VPN management via vpn.gftd.ai XRPC (ADR-2605252200)
//
// Subcommands:
//   servers                       list available exit nodes
//   provision [--name] [--server] generate keypair locally, register device, save .conf
//   list                          list registered devices
//   download <device-id>          (re)download .conf for an existing device
//   revoke   <device-id>          remove a device from the VPN
//   connect  <device-id>          sudo wg-quick up   ~/.gftd/vpn/<id>.conf
//   disconnect <device-id>        sudo wg-quick down ~/.gftd/vpn/<id>.conf
//   status                        show active WireGuard interfaces (wg show)
//
// Auth (priority):
//   1. --token flag
//   2. $GFTD_TOKEN env
//   3. ~/.gftd/auth.json -> id_token / access_token
//   4. macOS Keychain service=gftd.auth, account=id_token

import (
	"bytes"
	"crypto/ecdh"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

const (
	vpnBaseURL = "https://vpn.gftd.ai"
	vpnNSID    = "ai.gftd.apps.vpn"
)

func runVPN(args []string) error {
	if len(args) == 0 {
		printVPNUsage()
		return nil
	}
	switch args[0] {
	case "servers":
		return vpnServers(args[1:])
	case "provision":
		return vpnProvision(args[1:])
	case "list":
		return vpnList(args[1:])
	case "download":
		return vpnDownload(args[1:])
	case "revoke":
		return vpnRevoke(args[1:])
	case "connect":
		return vpnConnect(args[1:])
	case "disconnect":
		return vpnDisconnect(args[1:])
	case "status":
		return vpnStatus()
	case "help", "--help", "-h":
		printVPNUsage()
		return nil
	default:
		return fmt.Errorf("unknown vpn subcommand: %s\n\nRun 'gftd vpn help' for usage.", args[0])
	}
}

// ── servers ──────────────────────────────────────────────────────────────────

func vpnServers(args []string) error {
	fs := flag.NewFlagSet("vpn servers", flag.ContinueOnError)
	_ = fs.Parse(args)

	var resp struct {
		Servers []struct {
			ServerID    string `json:"serverId"`
			Region      string `json:"region"`
			City        string `json:"city"`
			CapacityPct int    `json:"capacityPct"`
			Status      string `json:"status"`
			Tier        string `json:"tier"`
		} `json:"servers"`
	}
	if err := vpnGet("getServerList", nil, &resp); err != nil {
		return err
	}
	fmt.Printf("%-10s  %-6s  %-18s  %5s  %-12s  %s\n", "SERVER-ID", "REGION", "CITY", "LOAD%", "TIER", "STATUS")
	for _, s := range resp.Servers {
		fmt.Printf("%-10s  %-6s  %-18s  %4d%%  %-12s  %s\n",
			s.ServerID, s.Region, s.City, s.CapacityPct, s.Tier, s.Status)
	}
	return nil
}

// ── provision ────────────────────────────────────────────────────────────────

func vpnProvision(args []string) error {
	fs := flag.NewFlagSet("vpn provision", flag.ContinueOnError)
	name   := fs.String("name",   "", "device label (default: hostname)")
	server := fs.String("server", "sjc-01", "exit node ID")
	token  := fs.String("token",  "", "auth token (default: auto-detected)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp { return nil }
		return err
	}

	tok, err := vpnLoadToken(*token)
	if err != nil {
		return err
	}

	deviceName := *name
	if deviceName == "" {
		if h, e := os.Hostname(); e == nil {
			deviceName = h
		} else {
			deviceName = "my-device"
		}
	}

	// Generate WireGuard keypair locally (private key never leaves this machine)
	privB64, pubB64, err := generateWGKeyPair()
	if err != nil {
		return fmt.Errorf("key generation failed: %w", err)
	}

	fmt.Fprintf(os.Stderr, "Provisioning device %q on server %s...\n", deviceName, *server)

	var result struct {
		DeviceID       string `json:"deviceId"`
		AssignedIP     string `json:"assignedIp"`
		ServerPublicKey string `json:"serverPublicKey"`
		ServerEndpoint  string `json:"serverEndpoint"`
		ServerDns       string `json:"serverDns"`
		Error           string `json:"error"`
	}
	body := map[string]string{
		"publicKey":  pubB64,
		"deviceName": deviceName,
		"serverId":   *server,
	}
	if err := vpnPost("provisionDevice", tok, body, &result); err != nil {
		return err
	}
	if result.Error != "" {
		return fmt.Errorf("provision failed: %s", result.Error)
	}

	// Build .conf with private key filled in
	conf := buildWGConf(privB64, result.AssignedIP, result.ServerPublicKey, result.ServerEndpoint, result.ServerDns)

	// Save .conf to ~/.gftd/vpn/<device-id>.conf
	confPath, err := saveVPNConf(result.DeviceID, conf)
	if err != nil {
		return err
	}

	fmt.Printf("\n✓ Device registered\n")
	fmt.Printf("  Device ID   : %s\n", result.DeviceID)
	fmt.Printf("  Assigned IP : %s\n", result.AssignedIP)
	fmt.Printf("  Config file : %s\n", confPath)
	fmt.Printf("\nTo connect:\n  gftd vpn connect %s\n", result.DeviceID)
	return nil
}

// ── list ─────────────────────────────────────────────────────────────────────

func vpnList(args []string) error {
	fs := flag.NewFlagSet("vpn list", flag.ContinueOnError)
	token := fs.String("token", "", "auth token (default: auto-detected)")
	_ = fs.Parse(args)

	tok, err := vpnLoadToken(*token)
	if err != nil {
		return err
	}

	var resp struct {
		Devices []struct {
			DeviceID            string `json:"deviceId"`
			DeviceName          string `json:"deviceName"`
			PublicKeyFingerprint string `json:"publicKeyFingerprint"`
			ServerID            string `json:"serverId"`
			AssignedIP          string `json:"assignedIp"`
			CreatedAt           string `json:"createdAt"`
		} `json:"devices"`
		DeviceLimit int    `json:"deviceLimit"`
		Tier        string `json:"tier"`
	}
	if err := vpnPost("listDevices", tok, nil, &resp); err != nil {
		return err
	}

	fmt.Printf("Tier: %s  (devices: %d / %d)\n\n", resp.Tier, len(resp.Devices), resp.DeviceLimit)
	if len(resp.Devices) == 0 {
		fmt.Println("No devices registered. Run: gftd vpn provision")
		return nil
	}
	fmt.Printf("%-14s  %-22s  %-10s  %-16s  %s\n", "DEVICE-ID", "NAME", "SERVER", "ASSIGNED-IP", "CREATED")
	for _, d := range resp.Devices {
		t, _ := time.Parse(time.RFC3339, d.CreatedAt)
		created := t.Format("2006-01-02")
		if t.IsZero() {
			created = d.CreatedAt[:10]
		}
		fmt.Printf("%-14s  %-22s  %-10s  %-16s  %s\n",
			d.DeviceID, d.DeviceName, d.ServerID, d.AssignedIP, created)
	}
	return nil
}

// ── download ─────────────────────────────────────────────────────────────────

func vpnDownload(args []string) error {
	fs := flag.NewFlagSet("vpn download", flag.ContinueOnError)
	token := fs.String("token", "", "auth token")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp { return nil }
		return err
	}
	if fs.NArg() < 1 {
		return fmt.Errorf("usage: gftd vpn download <device-id>")
	}
	deviceID := fs.Arg(0)

	tok, err := vpnLoadToken(*token)
	if err != nil {
		return err
	}

	url := fmt.Sprintf("%s/xrpc/%s.downloadConfig?deviceId=%s", vpnBaseURL, vpnNSID, deviceID)
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", "Bearer "+tok)

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return fmt.Errorf("server error %d: %s", resp.StatusCode, body)
	}

	confPath, err := saveVPNConf(deviceID, string(body))
	if err != nil {
		return err
	}
	fmt.Printf("✓ Config saved: %s\n", confPath)
	fmt.Printf("  Note: fill in PrivateKey before connecting.\n")
	return nil
}

// ── revoke ───────────────────────────────────────────────────────────────────

func vpnRevoke(args []string) error {
	fs := flag.NewFlagSet("vpn revoke", flag.ContinueOnError)
	token := fs.String("token", "", "auth token")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp { return nil }
		return err
	}
	if fs.NArg() < 1 {
		return fmt.Errorf("usage: gftd vpn revoke <device-id>")
	}
	deviceID := fs.Arg(0)

	tok, err := vpnLoadToken(*token)
	if err != nil {
		return err
	}

	var result struct{ OK bool `json:"ok"`; Error string `json:"error"` }
	if err := vpnPost("revokeDevice", tok, map[string]string{"deviceId": deviceID}, &result); err != nil {
		return err
	}
	if result.Error != "" {
		return fmt.Errorf("revoke failed: %s", result.Error)
	}

	// Remove local .conf if present
	home, _ := os.UserHomeDir()
	confPath := filepath.Join(home, ".gftd", "vpn", deviceID+".conf")
	if _, err := os.Stat(confPath); err == nil {
		os.Remove(confPath)
		fmt.Printf("✓ Removed local config: %s\n", confPath)
	}
	fmt.Printf("✓ Device %s revoked\n", deviceID)
	return nil
}

// ── connect / disconnect ─────────────────────────────────────────────────────

func vpnConnect(args []string) error {
	fs := flag.NewFlagSet("vpn connect", flag.ContinueOnError)
	_ = fs.Parse(args)
	if fs.NArg() < 1 {
		return fmt.Errorf("usage: gftd vpn connect <device-id>")
	}
	confPath, err := vpnConfPath(fs.Arg(0))
	if err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "Connecting via: %s\n", confPath)
	cmd := exec.Command("sudo", "wg-quick", "up", confPath)
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	return cmd.Run()
}

func vpnDisconnect(args []string) error {
	fs := flag.NewFlagSet("vpn disconnect", flag.ContinueOnError)
	_ = fs.Parse(args)
	if fs.NArg() < 1 {
		return fmt.Errorf("usage: gftd vpn disconnect <device-id>")
	}
	confPath, err := vpnConfPath(fs.Arg(0))
	if err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "Disconnecting: %s\n", confPath)
	cmd := exec.Command("sudo", "wg-quick", "down", confPath)
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	return cmd.Run()
}

func vpnStatus() error {
	cmd := exec.Command("sudo", "wg", "show")
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	return cmd.Run()
}

// ── helpers ───────────────────────────────────────────────────────────────────

func generateWGKeyPair() (privB64, pubB64 string, err error) {
	curve := ecdh.X25519()
	priv, err := curve.GenerateKey(rand.Reader)
	if err != nil {
		return "", "", err
	}
	privB64 = base64.StdEncoding.EncodeToString(priv.Bytes())
	pubB64 = base64.StdEncoding.EncodeToString(priv.PublicKey().Bytes())
	return
}

func buildWGConf(privKey, assignedIP, serverPubKey, endpoint, dns string) string {
	return fmt.Sprintf(
		"[Interface]\nPrivateKey = %s\nAddress    = %s\nDNS        = %s\n\n"+
			"[Peer]\nPublicKey           = %s\nEndpoint            = %s\n"+
			"AllowedIPs          = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n",
		privKey, assignedIP, dns, serverPubKey, endpoint,
	)
}

func saveVPNConf(deviceID, conf string) (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	dir := filepath.Join(home, ".gftd", "vpn")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return "", err
	}
	path := filepath.Join(dir, deviceID+".conf")
	if err := os.WriteFile(path, []byte(conf), 0o600); err != nil {
		return "", err
	}
	return path, nil
}

func vpnConfPath(deviceID string) (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	path := filepath.Join(home, ".gftd", "vpn", deviceID+".conf")
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return "", fmt.Errorf("config not found: %s\nRun: gftd vpn download %s", path, deviceID)
	}
	return path, nil
}

func vpnLoadToken(explicit string) (string, error) {
	if explicit != "" {
		return explicit, nil
	}
	if t := os.Getenv("GFTD_TOKEN"); t != "" {
		return t, nil
	}
	// ~/.gftd/auth.json
	home, _ := os.UserHomeDir()
	if data, err := os.ReadFile(filepath.Join(home, ".gftd", "auth.json")); err == nil {
		var m map[string]any
		if json.Unmarshal(data, &m) == nil {
			for _, key := range []string{"id_token", "access_token"} {
				if t, ok := m[key].(string); ok && t != "" {
					return t, nil
				}
			}
		}
	}
	// macOS Keychain
	if out, err := exec.Command("security", "find-generic-password", "-s", "gftd.auth", "-a", "id_token", "-w").Output(); err == nil {
		if t := strings.TrimSpace(string(out)); t != "" {
			return t, nil
		}
	}
	return "", fmt.Errorf("no auth token — set GFTD_TOKEN env or run: gftd authn signin")
}

func vpnGet(method string, _ map[string]string, out any) error {
	url := fmt.Sprintf("%s/xrpc/%s.%s", vpnBaseURL, vpnNSID, method)
	req, _ := http.NewRequest("GET", url, nil)
	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return fmt.Errorf("server %d: %s", resp.StatusCode, body)
	}
	return json.Unmarshal(body, out)
}

func vpnPost(method, token string, payload any, out any) error {
	url := fmt.Sprintf("%s/xrpc/%s.%s", vpnBaseURL, vpnNSID, method)
	var buf *bytes.Buffer
	if payload != nil {
		b, err := json.Marshal(payload)
		if err != nil {
			return err
		}
		buf = bytes.NewBuffer(b)
	} else {
		buf = bytes.NewBuffer([]byte("{}"))
	}
	req, _ := http.NewRequest("POST", url, buf)
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return fmt.Errorf("server %d: %s", resp.StatusCode, body)
	}
	if out != nil {
		return json.Unmarshal(body, out)
	}
	return nil
}

// ── usage ─────────────────────────────────────────────────────────────────────

func printVPNUsage() {
	fmt.Print(`gftd vpn — WireGuard VPN management (vpn.gftd.ai)

USAGE:
  gftd vpn <subcommand> [flags]

SUBCOMMANDS:
  servers                       List available exit nodes and capacity
  provision [--name] [--server] Generate WireGuard keypair locally, register device, save .conf
  list                          List your registered devices
  download <device-id>          Re-download .conf for an existing device
  revoke   <device-id>          Remove a device (key revoked on exit node)
  connect  <device-id>          Connect via: sudo wg-quick up ~/.gftd/vpn/<id>.conf
  disconnect <device-id>        Disconnect: sudo wg-quick down
  status                        Show active WireGuard interfaces (sudo wg show)

PROVISION FLAGS:
  --name   <label>   Device label (default: hostname)
  --server <id>      Exit node (default: sjc-01)
  --token  <jwt>     Override auth token

AUTH (auto-detected priority):
  1. --token flag
  2. $GFTD_TOKEN env
  3. ~/.gftd/auth.json → id_token / access_token
  4. macOS Keychain: service=gftd.auth, account=id_token

CONFIG FILES:
  ~/.gftd/vpn/<device-id>.conf  (chmod 600, private key stored here)

EXAMPLES:
  gftd vpn servers
  gftd vpn provision --name "MacBook Pro" --server sjc-01
  gftd vpn connect <device-id>
  gftd vpn list
  gftd vpn revoke <device-id>

REQUIREMENTS:
  connect/disconnect/status require WireGuard tools:
    macOS: brew install wireguard-tools
    Linux: apt install wireguard-tools
`)
}
