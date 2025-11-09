use serde::{Serialize, Deserialize};
use crate::crypto::{Address, KeyPair};
use crate::block::{Block, ValidatorVote, VoteType};
use rand;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Staker {
    pub address: Address,
    pub stake_amount: u64,
    pub bonded_since: u64,
    pub voting_power: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProofOfStake {
    pub stakers: Vec<Staker>,
    pub total_stake: u64,
    pub minimum_stake: u64,
    pub unbonding_period: u64, // in seconds
}

impl ProofOfStake {
    pub fn new(minimum_stake: u64, unbonding_period: u64) -> Self {
        Self {
            stakers: Vec::new(),
            total_stake: 0,
            minimum_stake,
            unbonding_period,
        }
    }
    
    pub fn add_staker(&mut self, address: Address, stake_amount: u64, timestamp: u64) -> bool {
        if stake_amount < self.minimum_stake {
            return false;
        }
        
        let voting_power = self.calculate_voting_power(stake_amount);
        let staker = Staker {
            address,
            stake_amount,
            bonded_since: timestamp,
            voting_power,
        };
        
        self.stakers.push(staker);
        self.total_stake += stake_amount;
        self.update_voting_powers();
        true
    }
    
    pub fn remove_staker(&mut self, address: &Address, current_time: u64) -> bool {
        if let Some(index) = self.stakers.iter().position(|s| &s.address == address) {
            let staker = &self.stakers[index];
            
            // Check unbonding period
            if current_time - staker.bonded_since < self.unbonding_period {
                return false;
            }
            
            self.total_stake -= staker.stake_amount;
            self.stakers.remove(index);
            self.update_voting_powers();
            true
        } else {
            false
        }
    }
    
    fn calculate_voting_power(&self, stake_amount: u64) -> f64 {
        // Quadratic voting to prevent whale dominance
        (stake_amount as f64).sqrt()
    }
    
    fn update_voting_powers(&mut self) {
        let stakers_copy = self.stakers.clone();
        
        for (i, staker) in stakers_copy.iter().enumerate() {
            self.stakers[i].voting_power = self.calculate_voting_power(staker.stake_amount);
        }
    }
    
    pub fn select_validators(&self, count: usize) -> Vec<Address> {
        // Weighted random selection based on voting power
        let total_power: f64 = self.stakers.iter().map(|s| s.voting_power).sum();
        let mut validators = Vec::new();
        
        while validators.len() < count && validators.len() < self.stakers.len() {
            let mut selection = rand::random::<f64>() * total_power;
            
            for staker in &self.stakers {
                selection -= staker.voting_power;
                if selection <= 0.0 {
                    if !validators.contains(&staker.address) {
                        validators.push(staker.address.clone());
                    }
                    break;
                }
            }
        }
        
        validators
    }
    
    pub fn vote_on_block(
        &self,
        block: &Block,
        validator: &Address,
        key_pair: &KeyPair,
        vote: VoteType,
    ) -> Option<ValidatorVote> {
        // Verify this address is a validator
        if !self.stakers.iter().any(|s| &s.address == validator) {
            return None;
        }
        
        let vote_data = format!("{}{:?}", block.hash, vote);
        let signature = key_pair.sign(vote_data.as_bytes());
        
        Some(ValidatorVote {
            validator: validator.clone(),
            signature,
            vote,
        })
    }
    
    pub fn calculate_finality_score(&self, votes: &[ValidatorVote], ai_score: Option<f32>) -> f64 {
        let mut total_voting_power = 0.0;
        let mut approval_power = 0.0;
        
        for vote in votes {
            if let Some(staker) = self.stakers.iter().find(|s| s.address == vote.validator) {
                total_voting_power += staker.voting_power;
                
                if matches!(vote.vote, VoteType::Approve) {
                    approval_power += staker.voting_power;
                }
            }
        }
        
        let pos_score = if total_voting_power > 0.0 {
            approval_power / total_voting_power
        } else {
            0.0
        };
        
        // Combine PoS score with AI validator score (40% weight to AI)
        let ai_weight = 0.4;
        let pos_weight = 0.6;
        
        let ai_contribution = ai_score.unwrap_or(0.5) as f64 * ai_weight;
        let pos_contribution = pos_score * pos_weight;
        
        ai_contribution + pos_contribution
    }
}