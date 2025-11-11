package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

type Node struct {
	Config       *Config
	BlockCounter int
	Mutex        sync.RWMutex
	AIClient     *AIClient
	BlockLogger  *BlockLogger
}

type Config struct {
	NetworkID      string
	RPCPort        int
	P2PPort        int
	DataDir        string
	IsMiner        bool
	IsValidator    bool
	AIValidatorURL string
}

type AIClient struct {
	BaseURL string
	Client  *http.Client
}

type BlockLogger struct {
	LogFile string
	Mutex   sync.Mutex
}

type Block struct {
	Height    int    `json:"height"`
	Hash      string `json:"hash"`
	Timestamp int64  `json:"timestamp"`
	TxCount   int    `json:"tx_count"`
	Miner     string `json:"miner"`
	Size      int    `json:"size"`
}

type AIValidationResult struct {
	Score      float64 `json:"score"`
	Decision   string  `json:"decision"`
	Confidence float64 `json:"confidence"`
	Validator  string  `json:"validator"`
	Block      string  `json:"block"`
	Height     int     `json:"height"`
}

func main() {
	// Parse command line flags
	mine := flag.Bool("mine", false, "Enable mining")
	validator := flag.Bool("validator", false, "Enable validation")
	datadir := flag.String("datadir", "./data", "Data directory")
	rpcport := flag.Int("rpcport", 8545, "RPC server port")
	p2pport := flag.Int("p2pport", 30303, "P2P network port")
	aivalidator := flag.String("aivalidator", "http://ai-validator:5000", "AI Validator URL")

	flag.Parse()

	// Load configuration
	config := &Config{
		NetworkID:      "zytherion-testnet",
		RPCPort:        *rpcport,
		P2PPort:        *p2pport,
		DataDir:        *datadir,
		IsMiner:        *mine,
		IsValidator:    *validator,
		AIValidatorURL: *aivalidator,
	}

	log.Printf("🚀 Starting Zytherion Node...")
	log.Printf("⛏️  Mining: %t", config.IsMiner)
	log.Printf("✅ Validation: %t", config.IsValidator)
	log.Printf("🤖 AI Validator: %s", config.AIValidatorURL)
	log.Printf("📁 Data Directory: %s", config.DataDir)
	log.Printf("🔌 RPC Port: %d", config.RPCPort)
	log.Printf("🌐 P2P Port: %d", config.P2PPort)

	// Initialize node
	node := &Node{
		Config:       config,
		BlockCounter: 0,
		AIClient: &AIClient{
			BaseURL: config.AIValidatorURL,
			Client:  &http.Client{Timeout: 10 * time.Second},
		},
		BlockLogger: &BlockLogger{
			LogFile: config.DataDir + "/blocks.log",
		},
	}

	// Ensure data directory exists
	os.MkdirAll(config.DataDir, 0755)

	// Start node components
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start mining if enabled
	if config.IsMiner {
		go node.startMining(ctx)
	}

	// Start validation if enabled
	if config.IsValidator {
		go node.startValidation(ctx)
	}

	// Start RPC server
	go node.startRPCServer(ctx)

	// Start block monitor
	go node.startBlockMonitor(ctx)

	log.Printf("✅ Node started successfully!")
	log.Printf("📡 RPC endpoint: http://localhost:%d", config.RPCPort)
	log.Printf("🔗 P2P listening on port: %d", config.P2PPort)
	log.Printf("🤖 AI Validator: %s", config.AIValidatorURL)
	log.Printf("💡 Use Ctrl+C to stop the node")

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	log.Println("Shutting down node...")
	cancel()
}

func (n *Node) startMining(ctx context.Context) {
	log.Printf("⛏️  Starting mining module...")
	ticker := time.NewTicker(6 * time.Second)
	defer ticker.Stop()

	blockHeight := 1

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			block := n.generateNewBlock(blockHeight)
			log.Printf("⛏️  MINED BLOCK #%d - Hash: %s...", block.Height, block.Hash[:16])

			// Validate with AI
			if n.Config.IsValidator {
				go n.validateBlockWithAI(block)
			}

			// Log the block
			n.logBlock(block, "MINED")

			blockHeight++
			n.Mutex.Lock()
			n.BlockCounter++
			n.Mutex.Unlock()
		}
	}
}

func (n *Node) startValidation(ctx context.Context) {
	log.Printf("✅ Starting validation module...")
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			log.Printf("✅ Validating network blocks...")
			// Simulate validating received blocks
			if n.BlockCounter > 0 {
				log.Printf("✅ Validated %d blocks in network", n.BlockCounter)
			}
		}
	}
}

func (n *Node) startBlockMonitor(ctx context.Context) {
	log.Printf("📊 Starting block monitor...")
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			n.Mutex.RLock()
			blockCount := n.BlockCounter
			n.Mutex.RUnlock()
			log.Printf("📊 BLOCK STATS - Total Blocks: %d", blockCount)
		}
	}
}

func (n *Node) startRPCServer(ctx context.Context) {
	log.Printf("🔌 Starting RPC server on port %d...", n.Config.RPCPort)

	// Simple HTTP server for RPC
	http.HandleFunc("/", n.handleRPC)
	http.HandleFunc("/blocks", n.handleBlocks)
	http.HandleFunc("/stats", n.handleStats)

	server := &http.Server{
		Addr: fmt.Sprintf(":%d", n.Config.RPCPort),
	}

	go server.ListenAndServe()

	// Shutdown gracefully
	<-ctx.Done()
	server.Shutdown(context.Background())
}

func (n *Node) generateNewBlock(height int) Block {
	return Block{
		Height:    height,
		Hash:      fmt.Sprintf("0x%x", time.Now().UnixNano()), // Simple hash simulation
		Timestamp: time.Now().Unix(),
		TxCount:   height * 2, // Simulate increasing transactions
		Miner:     "zytherion_miner_01",
		Size:      256 + (height * 10),
	}
}

func (n *Node) validateBlockWithAI(block Block) {
	validation, err := n.AIClient.ValidateBlock(block)
	if err != nil {
		log.Printf("❌ AI Validation failed: %v", err)
		return
	}

	log.Printf("🤖 AI VALIDATION - Block #%d - Score: %.3f - Decision: %s",
		block.Height, validation.Score, validation.Decision)

	// Log the validation result
	n.logBlockValidation(block, validation)
}

func (n *Node) logBlock(block Block, source string) {
	n.BlockLogger.Mutex.Lock()
	defer n.BlockLogger.Mutex.Unlock()

	logEntry := map[string]interface{}{
		"timestamp":    time.Now().Format(time.RFC3339),
		"block_height": block.Height,
		"block_hash":   block.Hash,
		"tx_count":     block.TxCount,
		"miner":        block.Miner,
		"source":       source,
		"size":         block.Size,
	}

	file, err := os.OpenFile(n.BlockLogger.LogFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("❌ Failed to log block: %v", err)
		return
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.Encode(logEntry)
}

func (n *Node) logBlockValidation(block Block, validation AIValidationResult) {
	n.BlockLogger.Mutex.Lock()
	defer n.BlockLogger.Mutex.Unlock()

	logEntry := map[string]interface{}{
		"timestamp":    time.Now().Format(time.RFC3339),
		"block_height": block.Height,
		"block_hash":   block.Hash,
		"ai_score":     validation.Score,
		"ai_decision":  validation.Decision,
		"ai_validator": validation.Validator,
		"confidence":   validation.Confidence,
	}

	validationFile := n.Config.DataDir + "/validations.log"
	file, err := os.OpenFile(validationFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("❌ Failed to log validation: %v", err)
		return
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.Encode(logEntry)
}

// AI Client methods
func (ac *AIClient) ValidateBlock(block Block) (AIValidationResult, error) {
	blockData := map[string]interface{}{
		"height":    block.Height,
		"hash":      block.Hash,
		"timestamp": block.Timestamp,
		"tx_count":  block.TxCount,
		"miner":     block.Miner,
		"size":      block.Size,
	}

	jsonData, err := json.Marshal(blockData)
	if err != nil {
		return AIValidationResult{}, err
	}

	resp, err := ac.Client.Post(ac.BaseURL+"/validate/block", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return AIValidationResult{}, err
	}
	defer resp.Body.Close()

	var result AIValidationResult
	err = json.NewDecoder(resp.Body).Decode(&result)
	return result, err
}

// RPC Handlers
func (n *Node) handleRPC(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      1,
		"result": map[string]interface{}{
			"block_height": n.BlockCounter,
			"network":      n.Config.NetworkID,
			"version":      "Zytherion/v1.0",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (n *Node) handleBlocks(w http.ResponseWriter, r *http.Request) {
	n.Mutex.RLock()
	defer n.Mutex.RUnlock()

	response := map[string]interface{}{
		"total_blocks": n.BlockCounter,
		"network":      n.Config.NetworkID,
		"timestamp":    time.Now().Unix(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (n *Node) handleStats(w http.ResponseWriter, r *http.Request) {
	stats := map[string]interface{}{
		"blocks_mined":       n.BlockCounter,
		"mining_enabled":     n.Config.IsMiner,
		"validation_enabled": n.Config.IsValidator,
		"ai_validator_url":   n.Config.AIValidatorURL,
		"data_directory":     n.Config.DataDir,
		"uptime":             time.Now().Format(time.RFC3339),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}
