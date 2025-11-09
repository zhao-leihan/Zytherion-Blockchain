package p2p

import (
	"context"
	"log"
	"time"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p/core/host"
	"github.com/libp2p/go-libp2p/core/network"
	"github.com/libp2p/go-libp2p/core/peer"
	"github.com/libp2p/go-libp2p/core/protocol"
	"github.com/multiformats/go-multiaddr"
)

type Network struct {
	host   host.Host
	peers  map[peer.ID]*peer.AddrInfo
	config *Config
}

type Config struct {
	Port           int
	DataDir        string
	BootstrapPeers []string
}

func NewNetwork(port int, dataDir string) (*Network, error) {
	// Create libp2p host
	h, err := libp2p.New(
		libp2p.ListenAddrStrings(
			format.Sprintf("/ip4/0.0.0.0/tcp/%d", port),
		),
	)
	if err != nil {
		return nil, err
	}

	net := &Network{
		host:  h,
		peers: make(map[peer.ID]*peer.AddrInfo),
		config: &Config{
			Port:    port,
			DataDir: dataDir,
			BootstrapPeers: []string{
				"/ip4/104.131.131.82/tcp/4001/p2p/QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ",
			},
		},
	}

	// Set stream handlers
	h.SetStreamHandler(protocol.ID("/zytherion/1.0.0"), net.handleStream)

	return net, nil
}

func (n *Network) Start(ctx context.Context) {
	log.Printf("P2P node started: %s", n.host.ID())

	// Connect to bootstrap peers
	go n.connectToBootstrapPeers(ctx)

	// Start discovery
	go n.startDiscovery(ctx)

	// Start peer maintenance
	go n.maintainPeers(ctx)
}

func (n *Network) handleStream(s network.Stream) {
	defer s.Close()

	// Handle incoming streams for block propagation, transaction gossip, etc.
	log.Printf("New stream from: %s", s.Conn().RemotePeer())

	// Protocol handling would be implemented here
}

func (n *Network) connectToBootstrapPeers(ctx context.Context) {
	for _, addrStr := range n.config.BootstrapPeers {
		addr, err := multiaddr.NewMultiaddr(addrStr)
		if err != nil {
			continue
		}

		peerInfo, err := peer.AddrInfoFromP2pAddr(addr)
		if err != nil {
			continue
		}

		if err := n.host.Connect(ctx, *peerInfo); err != nil {
			log.Printf("Failed to connect to bootstrap peer: %v", err)
		} else {
			log.Printf("Connected to bootstrap peer: %s", peerInfo.ID)
		}
	}
}

func (n *Network) startDiscovery(ctx context.Context) {
	// Implement peer discovery (MDNS, DHT, etc.)
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// Discovery logic
			n.discoverPeers(ctx)
		}
	}
}

func (n *Network) discoverPeers(ctx context.Context) {
	// Simple discovery - in production, use DHT or MDNS
	currentPeers := n.host.Network().Peers()
	log.Printf("Currently connected to %d peers", len(currentPeers))
}

func (n *Network) maintainPeers(ctx context.Context) {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			n.ensureMinPeers(ctx)
		}
	}
}

func (n *Network) ensureMinPeers(ctx context.Context) {
	minPeers := 5
	currentPeers := len(n.host.Network().Peers())

	if currentPeers < minPeers {
		log.Printf("Low peer count (%d), attempting to discover more", currentPeers)
		n.connectToBootstrapPeers(ctx)
	}
}

func (n *Network) BroadcastBlock(blockData []byte) {
	// Broadcast block to all connected peers
	for _, peerID := range n.host.Network().Peers() {
		if n.host.Network().Connectedness(peerID) == network.Connected {
			go n.sendToPeer(peerID, blockData)
		}
	}
}

func (n *Network) sendToPeer(peerID peer.ID, data []byte) {
	// Send data to specific peer
	stream, err := n.host.NewStream(context.Background(), peerID, protocol.ID("/zytherion/1.0.0"))
	if err != nil {
		return
	}
	defer stream.Close()

	_, err = stream.Write(data)
	if err != nil {
		log.Printf("Failed to send data to peer %s: %v", peerID, err)
	}
}

func (n *Network) GetPeerCount() int {
	return len(n.host.Network().Peers())
}
