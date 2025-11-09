use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use crate::crypto::Address;
use chrono;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contract {
    pub name: String,
    pub version: String,
    pub state: ContractState,
    pub actions: HashMap<String, ContractAction>,
    pub owner: Address,
    pub created_at: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractState {
    pub variables: HashMap<String, ContractValue>,
    pub locked_until: Option<u64>,
    pub balance: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ContractValue {
    String(String),
    Number(u64),
    Boolean(bool),
    Address(Address),
    Array(Vec<ContractValue>),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractAction {
    pub conditions: Vec<String>,
    pub effects: Vec<String>,
    pub description: Option<String>,
}

pub struct ContractEngine {
    contracts: HashMap<String, Contract>,
}

impl ContractEngine {
    pub fn new() -> Self {
        Self {
            contracts: HashMap::new(),
        }
    }
    
    pub fn deploy_contract(&mut self, contract: Contract) -> Result<String, String> {
        let contract_id = format!("{}_{}", contract.name, chrono::Utc::now().timestamp());
        self.contracts.insert(contract_id.clone(), contract);
        Ok(contract_id)
    }
    
    pub fn execute_action(
        &mut self,
        contract_id: &str,
        action_name: &str,
        caller: &Address,
        params: HashMap<String, ContractValue>,
    ) -> Result<Vec<String>, String> {
        let contract = self.contracts.get_mut(contract_id)
            .ok_or_else(|| "Contract not found".to_string())?;
            
        let action = contract.actions.get(action_name)
            .ok_or_else(|| format!("Action {} not found", action_name))?;
        
        // Clone state for evaluation to avoid borrowing issues
        let state_clone = contract.state.clone();
        let caller_clone = caller.clone();
        let params_clone = params.clone();
            
        // Check conditions
        for condition in &action.conditions {
            if !Self::evaluate_condition_static(condition, &state_clone, &caller_clone, &params_clone)? {
                return Err(format!("Condition not satisfied: {}", condition));
            }
        }
        
        // Execute effects
        let mut results = Vec::new();
        for effect in &action.effects {
            let result = Self::execute_effect_static(effect, &mut contract.state, &caller_clone, &params_clone)?;
            results.push(result);
        }
        
        Ok(results)
    }
    
    fn evaluate_condition_static(
        condition: &str,
        state: &ContractState,
        caller: &Address,
        params: &HashMap<String, ContractValue>,
    ) -> Result<bool, String> {
        // Simple condition evaluation
        if condition.contains("now > state.locked_until") {
            if let Some(locked_until) = state.locked_until {
                let now = chrono::Utc::now().timestamp() as u64;
                return Ok(now > locked_until);
            }
            return Ok(false);
        }
        
        if condition.contains("caller == state.owner") {
            if let Some(ContractValue::Address(owner)) = state.variables.get("owner") {
                return Ok(caller == owner);
            }
        }
        
        if condition.contains("balance > 0") {
            return Ok(state.balance > 0);
        }
        
        if condition.contains("params.amount > 0") {
            if let Some(ContractValue::Number(amount)) = params.get("amount") {
                return Ok(*amount > 0);
            }
            return Ok(false);
        }
        
        // Add more condition types as needed
        Ok(true) // Default to true for demo purposes
    }
    
    fn execute_effect_static(
        effect: &str,
        _state: &mut ContractState,
        _caller: &Address,
        _params: &HashMap<String, ContractValue>,
    ) -> Result<String, String> {
        if effect.starts_with("transfer(") {
            // Parse transfer effect: transfer(to, amount)
            let parts: Vec<&str> = effect.trim_start_matches("transfer(")
                .trim_end_matches(')')
                .split(',')
                .collect();
                
            if parts.len() == 2 {
                let to_address = parts[0].trim();
                let amount_str = parts[1].trim();
                
                // In a real implementation, you'd parse the address and amount
                return Ok(format!("Transfer {} to {}", amount_str, to_address));
            }
        }
        
        if effect.starts_with("state.") {
            // State modification
            return Ok(format!("Modified state: {}", effect));
        }
        
        // Default effect execution
        Ok(format!("Executed: {}", effect))
    }
    
    pub fn get_contract(&self, contract_id: &str) -> Option<&Contract> {
        self.contracts.get(contract_id)
    }
}

// Example contract templates
pub mod templates {
    use super::*;
    
    pub fn create_token_template(owner: Address, initial_supply: u64) -> Contract {
        let mut state_variables = HashMap::new();
        state_variables.insert("total_supply".to_string(), ContractValue::Number(initial_supply));
        state_variables.insert("owner".to_string(), ContractValue::Address(owner.clone()));
        
        let mut actions = HashMap::new();
        
        // Transfer action
        actions.insert("transfer".to_string(), ContractAction {
            conditions: vec![
                "caller == state.owner".to_string(),
                "params.amount > 0".to_string(),
            ],
            effects: vec![
                "transfer(params.to, params.amount)".to_string(),
            ],
            description: Some("Transfer tokens to another address".to_string()),
        });
        
        Contract {
            name: "ZytherionToken".to_string(),
            version: "1.0".to_string(),
            state: ContractState {
                variables: state_variables,
                locked_until: None,
                balance: initial_supply,
            },
            actions,
            owner,
            created_at: chrono::Utc::now().timestamp() as u64,
        }
    }
    
    pub fn create_timelock_template(owner: Address, locked_until: u64) -> Contract {
        let mut state_variables = HashMap::new();
        state_variables.insert("owner".to_string(), ContractValue::Address(owner.clone()));
        
        let mut actions = HashMap::new();
        
        actions.insert("withdraw".to_string(), ContractAction {
            conditions: vec![
                "caller == state.owner".to_string(),
                "now > state.locked_until".to_string(),
                "state.balance > 0".to_string(),
            ],
            effects: vec![
                "transfer(state.owner, state.balance)".to_string(),
            ],
            description: Some("Withdraw funds after lock period".to_string()),
        });
        
        Contract {
            name: "TimeLock".to_string(),
            version: "1.0".to_string(),
            state: ContractState {
                variables: state_variables,
                locked_until: Some(locked_until),
                balance: 0,
            },
            actions,
            owner,
            created_at: chrono::Utc::now().timestamp() as u64,
        }
    }
    
    // Simple demo contract that always works
    pub fn create_demo_template(owner: Address) -> Contract {
        let mut state_variables = HashMap::new();
        state_variables.insert("owner".to_string(), ContractValue::Address(owner.clone()));
        state_variables.insert("counter".to_string(), ContractValue::Number(0));
        
        let mut actions = HashMap::new();
        
        actions.insert("increment".to_string(), ContractAction {
            conditions: vec![],
            effects: vec![
                "state.variables.counter = state.variables.counter + 1".to_string(),
            ],
            description: Some("Increment counter".to_string()),
        });
        
        actions.insert("get_counter".to_string(), ContractAction {
            conditions: vec![],
            effects: vec![
                "return state.variables.counter".to_string(),
            ],
            description: Some("Get current counter value".to_string()),
        });
        
        Contract {
            name: "DemoContract".to_string(),
            version: "1.0".to_string(),
            state: ContractState {
                variables: state_variables,
                locked_until: None,
                balance: 0,
            },
            actions,
            owner,
            created_at: chrono::Utc::now().timestamp() as u64,
        }
    }
}