use crate::block::Block;

pub struct ProofOfWork {
    pub difficulty: u64,
    pub max_nonce: u64,
}

impl ProofOfWork {
    pub fn new(difficulty: u64) -> Self {
        Self {
            difficulty,
            max_nonce: u64::MAX,
        }
    }
    
    pub fn mine_block(&self, mut block: Block) -> Option<Block> {
        let target = self.get_target();
        
        for nonce in 0..self.max_nonce {
            block.header.nonce = nonce;
            let hash = block.calculate_hash();
            
            if self.is_valid_hash(&hash, &target) {
                block.hash = hash;
                return Some(block);
            }
        }
        
        None
    }
    
    fn get_target(&self) -> String {
        // More leading zeros = higher difficulty
        let zeros = "0".repeat(self.difficulty as usize);
        format!("{}f", zeros) // Ensure it's a valid hex
    }
    
    fn is_valid_hash(&self, hash: &str, target: &str) -> bool {
        hash.starts_with(target)
    }
    
    pub fn calculate_difficulty(
        current_height: u64,
        last_block_time: u64,
        target_block_time: u64,
        current_difficulty: u64,
    ) -> u64 {
        // Simple difficulty adjustment algorithm
        if current_height % 2016 == 0 { // Adjust every 2016 blocks
            let time_diff = (last_block_time as i64 - target_block_time as i64).abs() as u64;
            
            if time_diff > target_block_time * 2 {
                // Block time too slow, decrease difficulty
                current_difficulty.saturating_sub(1)
            } else if time_diff < target_block_time / 2 {
                // Block time too fast, increase difficulty
                current_difficulty.saturating_add(1)
            } else {
                current_difficulty
            }
        } else {
            current_difficulty
        }
    }
}