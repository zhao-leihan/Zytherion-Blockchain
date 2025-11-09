pub mod block;
pub mod pow;
pub mod pos;
pub mod contract_engine;
pub mod crypto;
pub mod state;

pub use block::{Block, BlockHeader, Transaction, ValidatorVote, VoteType};
pub use pow::ProofOfWork;
pub use pos::{ProofOfStake, Staker};
pub use contract_engine::{ContractEngine, Contract, ContractState, ContractAction, ContractValue};
pub use crypto::{hash_data, verify_signature, KeyPair, Address};
pub use state::{State, Account};

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Block validation failed: {0}")]
    BlockValidation(String),
    #[error("Contract execution failed: {0}")]
    ContractExecution(String),
    #[error("Cryptographic error: {0}")]
    Crypto(String),
    #[error("Serialization error: {0}")]
    Serialization(String),
    #[error("Database error: {0}")]
    Database(String),
}

pub type Result<T> = std::result::Result<T, Error>;

// Re-export commonly used types
pub use serde;
pub use bincode;

// ... existing code ...

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_crypto_key_generation() {
        let keypair = crypto::KeyPair::generate();
        let msg = b"hello world";
        let sig = keypair.sign(msg);
        let pk = keypair.public_key();

        // This should now pass!
        assert!(crypto::verify_signature(&pk, msg, &sig));
    }
    #[test]
    fn test_block_creation() {
        let block = block::Block::new(
            "0xprevious".to_string(),
            Vec::new(),
            1,
            1,
        );
        
        assert_eq!(block.header.height, 1);
        assert_eq!(block.header.previous_hash, "0xprevious");
        assert!(block.validate());
    }

    #[test]
    fn test_pow_mining() {
        let block = block::Block::new(
            "0xprevious".to_string(),
            Vec::new(),
            1, // Low difficulty
            1,
        );
        
        let pow = pow::ProofOfWork::new(1);
        let mined = pow.mine_block(block);
        
        assert!(mined.is_some(), "Mining should succeed with low difficulty");
        
        // Test with impossible difficulty
        let block2 = block::Block::new(
            "0xprevious".to_string(),
            Vec::new(),
            100, // Very high difficulty
            1,
        );
        
        let pow2 = pow::ProofOfWork::new(100);
        let mined2 = pow2.mine_block(block2);
        assert!(mined2.is_none(), "Mining should fail with very high difficulty");
    }

    #[test]
    fn test_pos_staking() {
        let mut pos = pos::ProofOfStake::new(1000, 259200);
        let address = crypto::Address::from_string("ZYTH_TEST".to_string());
        
        assert!(pos.add_staker(address.clone(), 2000, 1234567890));
        assert!(!pos.add_staker(address.clone(), 500, 1234567890)); // Below minimum
        
        assert_eq!(pos.total_stake, 2000);
        assert_eq!(pos.stakers.len(), 1);
        
        // Test validator selection
        let validators = pos.select_validators(1);
        assert_eq!(validators.len(), 1);
        assert_eq!(validators[0], address);
        
        // Test removing staker before unbonding period
        assert!(!pos.remove_staker(&address, 1234567890 + 1000)); // Too soon
        
        // Test removing staker after unbonding period
        assert!(pos.remove_staker(&address, 1234567890 + 259201)); // After period
        assert_eq!(pos.total_stake, 0);
        assert_eq!(pos.stakers.len(), 0);
    }

    #[test]
    fn test_contract_deployment() {
        let mut engine = contract_engine::ContractEngine::new();
        let owner = crypto::Address::from_string("ZYTH_OWNER".to_string());
        let contract = contract_engine::templates::create_token_template(owner, 1000);
        
        let contract_id = engine.deploy_contract(contract).unwrap();
        assert!(contract_id.starts_with("ZytherionToken"));
        assert!(engine.get_contract(&contract_id).is_some());
    }

    #[test]
    fn test_state_management() {
        let mut state = state::State::new();
        let address = crypto::Address::from_string("ZYTH_TEST".to_string());
        let account = state::Account {
            address: address.clone(),
            balance: 5000,
            nonce: 0,
            staked_amount: 1000,
            is_validator: false,
        };
        
        state.update_account(account);
        
        let retrieved = state.get_account(&address).unwrap();
        assert_eq!(retrieved.balance, 5000);
        assert_eq!(state.get_total_supply(), 5000);
        
        // Test genesis accounts
        state.create_genesis_accounts();
        assert!(state.get_total_supply() > 5000);
    }

    #[test]
    fn test_transaction_processing() {
        let mut state = state::State::new();
        
        let from_addr = crypto::Address::from_string("ZYTH_FROM".to_string());
        let to_addr = crypto::Address::from_string("ZYTH_TO".to_string());
        
        // Create sender account
        state.update_account(state::Account {
            address: from_addr.clone(),
            balance: 1000,
            nonce: 0,
            staked_amount: 0,
            is_validator: false,
        });
        
        // Create transaction
        let tx = block::Transaction {
            from: from_addr.clone(),
            to: to_addr.clone(),
            amount: 100,
            fee: 10,
            nonce: 0,
            signature: vec![],
            timestamp: 1234567890,
            data: None,
        };
        
        // Apply transaction
        assert!(state.apply_transaction(&tx).is_ok());
        
        // Check balances
        let from_account = state.get_account(&from_addr).unwrap();
        let to_account = state.get_account(&to_addr).unwrap();
        
        assert_eq!(from_account.balance, 890); // 1000 - 100 - 10
        assert_eq!(to_account.balance, 100);
        assert_eq!(from_account.nonce, 1);
        
        // Test invalid nonce
        let tx_bad_nonce = block::Transaction {
            from: from_addr.clone(),
            to: to_addr.clone(),
            amount: 100,
            fee: 10,
            nonce: 0, // Should be 1 now
            signature: vec![],
            timestamp: 1234567890,
            data: None,
        };
        
        assert!(state.apply_transaction(&tx_bad_nonce).is_err());
        
        // Test insufficient balance
        let tx_insufficient = block::Transaction {
            from: from_addr.clone(),
            to: to_addr.clone(),
            amount: 1000,
            fee: 10,
            nonce: 1,
            signature: vec![],
            timestamp: 1234567890,
            data: None,
        };
        
        assert!(state.apply_transaction(&tx_insufficient).is_err());
    }

    #[test]
    fn test_contract_execution() {
        let mut engine = contract_engine::ContractEngine::new();
        let owner = crypto::Address::from_string("ZYTH_OWNER".to_string());
        
        // Use the demo contract that has simpler conditions
        let contract = contract_engine::templates::create_demo_template(owner.clone());
        
        let contract_id = engine.deploy_contract(contract).unwrap();
        
        // Try to execute increment action (no parameters needed)
        let params = HashMap::new();
        
        let result = engine.execute_action(&contract_id, "increment", &owner, params);
        assert!(result.is_ok(), "Contract execution should succeed. Error: {:?}", result.err());
        
        // Try to execute get_counter action
        let params2 = HashMap::new();
        let result2 = engine.execute_action(&contract_id, "get_counter", &owner, params2);
        assert!(result2.is_ok(), "Get counter should succeed. Error: {:?}", result2.err());
    }

    #[test]
    fn test_comprehensive_workflow() {
        // Test a complete workflow: keys -> transaction -> block -> mining -> state update
        
        // 1. Generate keys
        let keypair = crypto::KeyPair::generate();
        let from_addr = crypto::Address::from_public_key(&keypair.public_key());
        let to_addr = crypto::Address::from_string("ZYTH_RECIPIENT".to_string());
        
        // 2. Create state and accounts
        let mut state = state::State::new();
        state.update_account(state::Account {
            address: from_addr.clone(),
            balance: 5000,
            nonce: 0,
            staked_amount: 0,
            is_validator: false,
        });
        
        // 3. Create transaction
        let tx = block::Transaction {
            from: from_addr.clone(),
            to: to_addr.clone(),
            amount: 1000,
            fee: 50,
            nonce: 0,
            signature: keypair.sign(b"transaction_data"),
            timestamp: 1234567890,
            data: None,
        };
        
        // 4. Create block with transaction
        let block = block::Block::new(
            "0xgenesis".to_string(),
            vec![tx],
            2, // Medium difficulty
            1,
        );
        
        // 5. Mine the block
        let pow = pow::ProofOfWork::new(2);
        let mined_block = pow.mine_block(block).expect("Should mine successfully");
        
        // 6. Apply block to state
        assert!(state.apply_block(&mined_block).is_ok());
        
        // 7. Verify state changes
        let from_account = state.get_account(&from_addr).unwrap();
        let to_account = state.get_account(&to_addr).unwrap();
        
        assert_eq!(from_account.balance, 3950); // 5000 - 1000 - 50
        assert_eq!(to_account.balance, 1000);
        assert_eq!(from_account.nonce, 1);
        
        println!("Comprehensive workflow test completed successfully!");
    }
}