# Zytherion Protocol Specification

## 1. Block Structure

### 1.1 Block Header
```rust
pub struct BlockHeader {
    pub version: u32,           // Protocol version
    pub previous_hash: String,  // SHA-256 of previous block
    pub merkle_root: String,    // Merkle root of transactions
    pub timestamp: u64,         // Unix timestamp
    pub difficulty: u64,        // PoW difficulty target
    pub nonce: u64,             // PoW nonce
    pub validator_votes: Vec<ValidatorVote>, // PoS votes
    pub height: u64,            // Block number
}