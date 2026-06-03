package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"net/netip"
	"sync"

	"golang.zx2c4.com/wireguard/tun/netstack"
)

// proxyPort forwards local TCP connections through the WireGuard tunnel.
// Listens on 127.0.0.1:<localPort> and dials <targetWGAddr>:<remotePort> via wgNet.
type proxyPort struct {
	localPort  int
	remotePort int
	targetAddr netip.Addr
	wgNet      *netstack.Net
	listener   net.Listener
}

// startProxy starts TCP proxies for Nomad ports (4646, 4647, 4648).
// targetWGAddr is the WireGuard overlay IP of the Nomad server.
func startProxy(wgNet *netstack.Net, targetWGAddr string, ports []int) ([]*proxyPort, error) {
	target, err := netip.ParseAddr(targetWGAddr)
	if err != nil {
		return nil, fmt.Errorf("parse target addr %q: %w", targetWGAddr, err)
	}

	var proxies []*proxyPort
	for _, port := range ports {
		p := &proxyPort{
			localPort:  port,
			remotePort: port,
			targetAddr: target,
			wgNet:      wgNet,
		}
		if err := p.start(); err != nil {
			// Cleanup already started
			for _, pp := range proxies {
				pp.stop()
			}
			return nil, fmt.Errorf("start proxy port %d: %w", port, err)
		}
		proxies = append(proxies, p)
	}
	return proxies, nil
}

func (p *proxyPort) start() error {
	ln, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", p.localPort))
	if err != nil {
		return err
	}
	p.listener = ln
	log.Printf("proxy: 127.0.0.1:%d → wg(%s:%d)", p.localPort, p.targetAddr, p.remotePort)

	go p.acceptLoop()
	return nil
}

func (p *proxyPort) acceptLoop() {
	for {
		clientConn, err := p.listener.Accept()
		if err != nil {
			return // listener closed
		}
		go p.handleConn(clientConn)
	}
}

func (p *proxyPort) handleConn(client net.Conn) {
	defer client.Close()

	target := netip.AddrPortFrom(p.targetAddr, uint16(p.remotePort))
	remote, err := p.wgNet.DialContextTCPAddrPort(context.Background(), target)
	if err != nil {
		log.Printf("proxy: dial %s failed: %v", target, err)
		return
	}
	defer remote.Close()

	var wg sync.WaitGroup
	wg.Add(2)
	go func() { defer wg.Done(); io.Copy(remote, client) }()
	go func() { defer wg.Done(); io.Copy(client, remote) }()
	wg.Wait()
}

func (p *proxyPort) stop() {
	if p.listener != nil {
		p.listener.Close()
	}
}
