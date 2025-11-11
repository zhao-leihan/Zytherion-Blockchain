import tensorflow as tf
import numpy as np
import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class AdvancedFeatureEngine:
    """Advanced feature engineering dengan TensorFlow operations"""
    
    def __init__(self):
        self.history_buffer = []
        self.max_history = 50
    
    def compute_advanced_features(self, current_block: Dict, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Compute advanced features menggunakan TensorFlow"""
        features = {}
        
        # Basic features
        features.update(self._compute_basic_features(current_block))
        
        # Statistical features dengan TensorFlow
        features.update(self._compute_statistical_features(current_block, previous_blocks))
        
        # Pattern detection
        features.update(self._compute_pattern_features(current_block, previous_blocks))
        
        # Network health features
        features.update(self._compute_network_features(previous_blocks))
        
        return features
    
    def _compute_basic_features(self, block: Dict) -> Dict[str, float]:
        """Compute basic block features"""
        return {
            'block_size': float(block.get('size', 0)),
            'tx_count': float(len(block.get('transactions', []))),
            'total_value': float(sum(tx.get('amount', 0) for tx in block.get('transactions', []))),
            'avg_tx_value': self._safe_divide(
                sum(tx.get('amount', 0) for tx in block.get('transactions', [])),
                max(len(block.get('transactions', [])), 1)
            ),
            'fee_ratio': self._safe_divide(
                sum(tx.get('fee', 0) for tx in block.get('transactions', [])),
                sum(tx.get('amount', 0) for tx in block.get('transactions', []))
            )
        }
    
    def _compute_statistical_features(self, current_block: Dict, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Compute statistical features menggunakan TensorFlow"""
        if len(previous_blocks) < 5:
            return {
                'block_time_volatility': 0.0,
                'tx_count_trend': 0.0,
                'value_volatility': 0.0
            }
        
        try:
            # Convert to TensorFlow tensors
            recent_blocks = previous_blocks[:10]
            
            # Block time analysis
            block_times = []
            for i in range(1, len(recent_blocks)):
                time_diff = abs(recent_blocks[i-1].get('timestamp', 0) - recent_blocks[i].get('timestamp', 0))
                block_times.append(time_diff)
            
            if block_times:
                block_times_tensor = tf.constant(block_times, dtype=tf.float32)
                time_std = tf.math.reduce_std(block_times_tensor)
                time_mean = tf.reduce_mean(block_times_tensor)
                features = {
                    'block_time_volatility': float(time_std / max(time_mean, 1)),
                    'block_time_anomaly': float(abs(6.0 - time_mean) / 6.0)  # vs target 6 seconds
                }
            else:
                features = {
                    'block_time_volatility': 0.0,
                    'block_time_anomaly': 0.0
                }
            
            # Transaction count trend
            tx_counts = [len(b.get('transactions', [])) for b in recent_blocks]
            if len(tx_counts) > 1:
                tx_tensor = tf.constant(tx_counts, dtype=tf.float32)
                current_tx = len(current_block.get('transactions', []))
                tx_trend = (current_tx - tf.reduce_mean(tx_tensor)) / max(tf.reduce_mean(tx_tensor), 1)
                features['tx_count_trend'] = float(tx_trend)
            else:
                features['tx_count_trend'] = 0.0
            
            return features
            
        except Exception as e:
            logger.error(f"Statistical feature error: {e}")
            return {}
    
    def _compute_pattern_features(self, current_block: Dict, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Detect patterns and anomalies"""
        features = {}
        
        # Transaction pattern analysis
        transactions = current_block.get('transactions', [])
        if transactions:
            values = [tx.get('amount', 0) for tx in transactions]
            fees = [tx.get('fee', 0) for tx in transactions]
            
            # Use TensorFlow for statistical analysis
            values_tensor = tf.constant(values, dtype=tf.float32)
            fees_tensor = tf.constant(fees, dtype=tf.float32)
            
            # Value concentration (Gini-like)
            sorted_values = tf.sort(values_tensor)
            n = tf.cast(tf.shape(sorted_values)[0], tf.float32)
            index = tf.range(1.0, n + 1.0)
            gini = tf.reduce_sum((2 * index - n - 1) * sorted_values) / (n * tf.reduce_sum(sorted_values))
            
            features.update({
                'value_concentration': float(gini),
                'fee_volatility': float(tf.math.reduce_std(fees_tensor) / max(tf.reduce_mean(fees_tensor), 1)),
                'value_skewness': float(self._compute_skewness(values_tensor))
            })
        
        return features
    
    def _compute_network_features(self, previous_blocks: List[Dict]) -> Dict[str, float]:
        """Compute network health features"""
        if len(previous_blocks) < 3:
            return {
                'network_health': 0.5,
                'consensus_stability': 0.5
            }
        
        try:
            # Validator participation stability
            participation_rates = []
            for block in previous_blocks[:10]:
                votes = block.get('validator_votes', [])
                total_validators = block.get('total_validators', 1)
                participation_rates.append(len(votes) / max(total_validators, 1))
            
            if participation_rates:
                participation_tensor = tf.constant(participation_rates, dtype=tf.float32)
                stability = 1.0 - tf.math.reduce_std(participation_tensor)
                
                return {
                    'network_health': float(tf.reduce_mean(participation_tensor)),
                    'consensus_stability': float(stability)
                }
            else:
                return {
                    'network_health': 0.5,
                    'consensus_stability': 0.5
                }
                
        except Exception as e:
            logger.error(f"Network feature error: {e}")
            return {'network_health': 0.5, 'consensus_stability': 0.5}
    
    def _compute_skewness(self, tensor: tf.Tensor) -> tf.Tensor:
        """Compute skewness of a tensor"""
        mean = tf.reduce_mean(tensor)
        std = tf.math.reduce_std(tensor)
        z_scores = (tensor - mean) / std
        return tf.reduce_mean(z_scores ** 3)
    
    def _safe_divide(self, numerator: float, denominator: float) -> float:
        """Safe division with zero check"""
        return numerator / denominator if denominator != 0 else 0.0