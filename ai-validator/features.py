import numpy as np
import pandas as pd
from typing import Dict, List, Any
import time

class BlockFeatureEngine:
    """Advanced feature engineering for blockchain validation"""
    
    def __init__(self):
        self.history_window = 100  # Number of previous blocks to consider
        self.feature_cache = {}
    
    def compute_advanced_features(self, current_block: Dict, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Compute advanced features using block history"""
        features = {}
        
        # Basic block features
        features.update(self._basic_block_features(current_block))
        
        # Temporal features
        features.update(self._temporal_features(current_block, previous_blocks))
        
        # Network health features
        features.update(self._network_features(previous_blocks))
        
        # Economic features
        features.update(self._economic_features(current_block, previous_blocks))
        
        # Security features
        features.update(self._security_features(current_block, previous_blocks))
        
        return features
    
    def _basic_block_features(self, block: Dict) -> Dict[str, float]:
        """Extract basic block-level features"""
        return {
            'block_size': block.get('size', 0),
            'tx_count': len(block.get('transactions', [])),
            'gas_used': block.get('gas_used', 0),
            'gas_limit': block.get('gas_limit', 0),
            'difficulty': block.get('difficulty', 0),
            'total_difficulty': block.get('total_difficulty', 0),
        }
    
    def _temporal_features(self, current_block: Dict, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Extract time-based features"""
        if not previous_blocks:
            return {
                'block_time_variance': 0.0,
                'timestamp_anomaly': 0.0,
                'mining_rate_change': 0.0
            }
        
        # Block time analysis
        block_times = []
        for i in range(1, min(10, len(previous_blocks))):
            time_diff = previous_blocks[i-1].get('timestamp', 0) - previous_blocks[i].get('timestamp', 0)
            block_times.append(abs(time_diff))
        
        current_time_diff = abs(current_block.get('timestamp', 0) - previous_blocks[0].get('timestamp', 0))
        
        if block_times:
            avg_block_time = np.mean(block_times)
            block_time_std = np.std(block_times)
            features = {
                'block_time_variance': block_time_std / max(avg_block_time, 1),
                'timestamp_anomaly': abs(current_time_diff - avg_block_time) / max(avg_block_time, 1),
                'mining_rate_change': (avg_block_time - 6.0) / 6.0  # Compared to target 6 seconds
            }
        else:
            features = {
                'block_time_variance': 0.0,
                'timestamp_anomaly': 0.0,
                'mining_rate_change': 0.0
            }
        
        return features
    
    def _network_features(self, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Extract network health features"""
        if len(previous_blocks) < 2:
            return {
                'hashrate_trend': 0.0,
                'uncle_rate': 0.0,
                'orphan_rate': 0.0
            }
        
        # Hashrate trend (simplified)
        recent_difficulty = [b.get('difficulty', 0) for b in previous_blocks[:10]]
        if len(recent_difficulty) > 1:
            difficulty_trend = (recent_difficulty[0] - np.mean(recent_difficulty[1:])) / max(np.mean(recent_difficulty[1:]), 1)
        else:
            difficulty_trend = 0.0
        
        # Uncle and orphan rates
        uncle_counts = [b.get('uncle_count', 0) for b in previous_blocks[:50]]
        orphan_events = sum(1 for b in previous_blocks[:100] if b.get('is_orphan', False))
        
        features = {
            'hashrate_trend': difficulty_trend,
            'uncle_rate': np.mean(uncle_counts) if uncle_counts else 0.0,
            'orphan_rate': orphan_events / min(len(previous_blocks), 100)
        }
        
        return features
    
    def _economic_features(self, current_block: Dict, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Extract economic and fee-related features"""
        if not previous_blocks:
            return {
                'fee_volatility': 0.0,
                'value_concentration': 0.0,
                'economic_activity': 0.0
            }
        
        # Fee analysis
        recent_fees = []
        for block in previous_blocks[:20]:
            block_fees = sum(tx.get('fee', 0) for tx in block.get('transactions', []))
            recent_fees.append(block_fees)
        
        current_fees = sum(tx.get('fee', 0) for tx in current_block.get('transactions', []))
        
        if recent_fees:
            avg_fee = np.mean(recent_fees)
            fee_std = np.std(recent_fees)
            features = {
                'fee_volatility': fee_std / max(avg_fee, 1),
                'fee_anomaly': abs(current_fees - avg_fee) / max(avg_fee, 1) if avg_fee > 0 else 0.0,
                'economic_activity': len(current_block.get('transactions', [])) / max(np.mean([len(b.get('transactions', [])) for b in previous_blocks[:10]]), 1)
            }
        else:
            features = {
                'fee_volatility': 0.0,
                'fee_anomaly': 0.0,
                'economic_activity': 1.0
            }
        
        # Value concentration (Gini-like coefficient)
        tx_values = [tx.get('amount', 0) for tx in current_block.get('transactions', [])]
        if tx_values:
            sorted_values = np.sort(tx_values)
            n = len(sorted_values)
            index = np.arange(1, n + 1)
            gini = (np.sum((2 * index - n - 1) * sorted_values)) / (n * np.sum(sorted_values))
            features['value_concentration'] = gini
        else:
            features['value_concentration'] = 0.0
        
        return features
    
    def _security_features(self, current_block: Dict, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Extract security and consensus-related features"""
        features = {}
        
        # Validator participation
        current_votes = current_block.get('validator_votes', [])
        features['validator_participation'] = len(current_votes) / max(current_block.get('total_validators', 1), 1)
        
        # Consensus quality
        approve_votes = sum(1 for vote in current_votes if vote.get('vote') == 'approve')
        features['consensus_quality'] = approve_votes / max(len(current_votes), 1)
        
        # Staking distribution (simplified)
        if previous_blocks:
            recent_stakes = [b.get('total_stake', 0) for b in previous_blocks[:10]]
            features['staking_trend'] = (recent_stakes[0] - np.mean(recent_stakes)) / max(np.mean(recent_stakes), 1) if recent_stakes else 0.0
        else:
            features['staking_trend'] = 0.0
        
        # Double spending detection (simplified)
        features['double_spend_risk'] = self._detect_double_spend_risk(current_block, previous_blocks)
        
        return features
    
    def _detect_double_spend_risk(self, current_block: Dict, previous_blocks: List[Dict]) -> float:
        """Detect potential double spending patterns"""
        # Simplified double spend detection
        current_tx_hashes = set(tx.get('hash', '') for tx in current_block.get('transactions', []))
        
        double_spend_count = 0
        for prev_block in previous_blocks[:5]:  # Check recent blocks
            for prev_tx in prev_block.get('transactions', []):
                if prev_tx.get('hash', '') in current_tx_hashes:
                    double_spend_count += 1
        
        return min(double_spend_count / max(len(current_tx_hashes), 1), 1.0)