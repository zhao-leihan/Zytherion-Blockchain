use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use crate::block::{Block, Transaction};
use crate::crypto::Address;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    pub address: Address,
    pub balance: u64,
    pub nonce: u64,
    pub staked_amount: u64,
    pub is_validator: bool,
}

pub struct State {
    accounts: HashMap<Address, Account>,
}

impl State {
    pub fn new() -> Self {
        Self {
            accounts: HashMap::new(),
        }
    }
    
    pub fn update_account(&mut self, account: Account) {
        self.accounts.insert(account.address.clone(), account);
    }
    
    pub fn get_account(&self, address: &Address) -> Option<&Account> {
        self.accounts.get(address)
    }
    
    pub fn get_account_mut(&mut self, address: &Address) -> Option<&mut Account> {
        self.accounts.get_mut(address)
    }
    
    pub fn apply_block(&mut self, block: &Block) -> Result<(), String> {
        for tx in &block.transactions {
            self.apply_transaction(tx)?;
        }
        Ok(())
    }
    
    pub fn apply_transaction(&mut self, tx: &Transaction) -> Result<(), String> {
        // First, check if we can process the transaction without modifying state
        let from_account = self.get_account(&tx.from)
            .ok_or_else(|| "Sender account not found".to_string())?;
            
        // Check nonce
        if from_account.nonce != tx.nonce {
            return Err("Invalid nonce".to_string());
        }
        
        // Check balance
        let total_cost = tx.amount + tx.fee;
        if from_account.balance < total_cost {
            return Err("Insufficient balance".to_string());
        }
        
        // Now perform the actual updates
        if let Some(from_account) = self.get_account_mut(&tx.from) {
            from_account.balance -= total_cost;
            from_account.nonce += 1;
        }
        
        let to_account = self.accounts.entry(tx.to.clone()).or_insert(Account {
            address: tx.to.clone(),
            balance: 0,
            nonce: 0,
            staked_amount: 0,
            is_validator: false,
        });
        
        to_account.balance += tx.amount;
            
        Ok(())
    }
    
    pub fn get_total_supply(&self) -> u64 {
        self.accounts.values().map(|acc| acc.balance).sum()
    }
    
    pub fn get_all_accounts(&self) -> Vec<&Account> {
        self.accounts.values().collect()
    }
    
    pub fn create_genesis_accounts(&mut self) {
        // Create some demo accounts for testing
        let accounts = vec![
            Account {
                address: Address::from_string("ZYTH_GENESIS_00000000000000000000".to_string()),
                balance: 1_000_000,
                nonce: 0,
                staked_amount: 0,
                is_validator: false,
            },
            Account {
                address: Address::from_string("ZYTH_DEVELOPER_000000000000000000".to_string()),
                balance: 100_000,
                nonce: 0,
                staked_amount: 10_000,
                is_validator: true,
            },
            Account {
                address: Address::from_string("ZYTH_USER_0000000000000000000000".to_string()),
                balance: 50_000,
                nonce: 0,
                staked_amount: 5_000,
                is_validator: false,
            },
        ];
        
        for account in accounts {
            self.update_account(account);
        }
    }
}