package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"zytherion-node/cli"
)

type Node struct {
	Config *Config
}

type Config struct {
	NetworkID   string
	RPCPort     int
	P2PPort     int
	DataDir     string
	IsMiner     bool
	IsValidator bool
	StakeAmount uint64
}

func main() {
	// Load configuration
	config := &Config{
		NetworkID:   "zytherion-mainnet",
		RPCPort:     8545,
		P2PPort:     30303,
		DataDir:     "./data",
		IsMiner:     false,
		IsValidator: false,
		StakeAmount: 1000,
	}

	// Initialize node
	node := &Node{
		Config: config,
	}

	// Handle CLI commands
	if err := cli.Execute(node); err != nil {
		log.Fatalf("CLI error: %v", err)
	}

	// If no command provided, start the node
	if len(os.Args) == 1 {
		startNode(node)
	}
}

func startNode(node *Node) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start node components here
	log.Println("Starting Zytherion node...")

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	select {
	case <-sigCh:
		log.Println("Shutting down node...")
	case <-ctx.Done():
	}
}
