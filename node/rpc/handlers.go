package rpc

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
)

type Server struct {
	port   int
	node   interface{} // Reference to main node
	server *http.Server
}

type JSONRPCRequest struct {
	JSONRPC string        `json:"jsonrpc"`
	Method  string        `json:"method"`
	Params  []interface{} `json:"params"`
	ID      interface{}   `json:"id"`
}

type JSONRPCResponse struct {
	JSONRPC string      `json:"jsonrpc"`
	Result  interface{} `json:"result,omitempty"`
	Error   *RPCError   `json:"error,omitempty"`
	ID      interface{} `json:"id"`
}

type RPCError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

func NewServer(port int, node interface{}) *Server {
	return &Server{
		port: port,
		node: node,
	}
}

func (s *Server) Start() {
	mux := http.NewServeMux()
	mux.HandleFunc("/", s.handleRPC)

	s.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", s.port),
		Handler: mux,
	}

	log.Printf("RPC server starting on :%d", s.port)
	if err := s.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("RPC server failed: %v", err)
	}
}

func (s *Server) Stop() {
	if s.server != nil {
		s.server.Close()
	}
}

func (s *Server) handleRPC(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req JSONRPCRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.sendError(w, nil, -32700, "Parse error")
		return
	}

	// Set response headers
	w.Header().Set("Content-Type", "application/json")

	// Route method
	result, err := s.routeMethod(req.Method, req.Params)
	if err != nil {
		s.sendError(w, req.ID, -32601, err.Error())
		return
	}

	response := JSONRPCResponse{
		JSONRPC: "2.0",
		Result:  result,
		ID:      req.ID,
	}

	json.NewEncoder(w).Encode(response)
}

func (s *Server) routeMethod(method string, params []interface{}) (interface{}, error) {
	switch method {
	case "eth_blockNumber":
		return "0x1", nil // Mock response
	case "eth_getBalance":
		if len(params) < 2 {
			return nil, fmt.Errorf("missing parameters")
		}
		return "0x0", nil // Mock response
	case "zytherion_getStakingInfo":
		return s.getStakingInfo()
	case "zytherion_getValidatorStatus":
		return s.getValidatorStatus()
	case "zytherion_sendTransaction":
		return s.sendTransaction(params)
	default:
		return nil, fmt.Errorf("method not found")
	}
}

func (s *Server) getStakingInfo() (map[string]interface{}, error) {
	// Mock staking info
	return map[string]interface{}{
		"totalStaked":    "1000000",
		"validatorCount": 25,
		"minimumStake":   "1000",
		"apy":            "5.2",
	}, nil
}

func (s *Server) getValidatorStatus() (map[string]interface{}, error) {
	return map[string]interface{}{
		"isValidator":  true,
		"stakedAmount": "5000",
		"votingPower":  "70.71",
		"active":       true,
	}, nil
}

func (s *Server) sendTransaction(params []interface{}) (string, error) {
	if len(params) < 1 {
		return "", fmt.Errorf("missing transaction data")
	}

	// In real implementation, you'd validate and broadcast the transaction
	return "0xtransactionhash", nil
}

func (s *Server) sendError(w http.ResponseWriter, id interface{}, code int, message string) {
	response := JSONRPCResponse{
		JSONRPC: "2.0",
		Error: &RPCError{
			Code:    code,
			Message: message,
		},
		ID: id,
	}
	json.NewEncoder(w).Encode(response)
}
