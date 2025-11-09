use serde::{Serialize, Deserialize};
use crate::crypto::{hash_data, Address};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockHeader {
    pub version: u32,
    pub previous_hash: String,
    pub merkle_root: String,
    pub timestamp: u64,
    pub difficulty: u64,
    pub nonce: u64,
    pub validator_votes: Vec<ValidatorVote>,
    pub height: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidatorVote {
    pub validator: Address,
    pub signature: Vec<u8>,
    pub vote: VoteType,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum VoteType {
    Approve,
    Reject,
    Abstain,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub from: Address,
    pub to: Address,
    pub amount: u64,
    pub fee: u64,
    pub nonce: u64,
    pub signature: Vec<u8>,
    pub timestamp: u64,
    pub data: Option<Vec<u8>>, // For contract calls
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Block {
    pub header: BlockHeader,
    pub transactions: Vec<Transaction>,
    pub hash: String,
    pub ai_validator_score: Option<f32>, // AI validation score 0.0-1.0
}

impl Block {
    pub fn new(
        previous_hash: String,
        transactions: Vec<Transaction>,
        difficulty: u64,
        height: u64,
    ) -> Self {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
            
        let merkle_root = Self::calculate_merkle_root(&transactions);
        
        let header = BlockHeader {
            version: 1,
            previous_hash,
            merkle_root,
            timestamp,
            difficulty,
            nonce: 0,
            validator_votes: Vec::new(),
            height,
        };
        
        let mut block = Self {
            header,
            transactions,
            hash: String::new(),
            ai_validator_score: None,
        };
        
        block.hash = block.calculate_hash();
        block
    }
    
    pub fn calculate_hash(&self) -> String {
        let header_data = bincode::serialize(&self.header).unwrap();
        hash_data(&header_data)
    }
    
    fn calculate_merkle_root(transactions: &[Transaction]) -> String {
        if transactions.is_empty() {
            return hash_data(&[]);
        }
        
        let mut hashes: Vec<String> = transactions
            .iter()
            .map(|tx| {
                let tx_data = bincode::serialize(tx).unwrap();
                hash_data(&tx_data)
            })
            .collect();
            
        while hashes.len() > 1 {
            let mut new_hashes = Vec::new();
            for chunk in hashes.chunks(2) {
                let combined = if chunk.len() == 2 {
                    format!("{}{}", chunk[0], chunk[1])
                } else {
                    format!("{}{}", chunk[0], chunk[0])
                };
                new_hashes.push(hash_data(combined.as_bytes()));
            }
            hashes = new_hashes;
        }
        
        hashes.remove(0)
    }
    
    pub fn validate(&self) -> bool {
        // Basic validation checks
        if self.hash != self.calculate_hash() {
            return false;
        }
        
        if self.transactions.len() > 10000 { // Arbitrary limit
            return false;
        }
        
        true
    }
}