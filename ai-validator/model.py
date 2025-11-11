import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIValidator:
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = [
            'tx_count', 'total_fee', 'block_size', 'timestamp_drift',
            'miner_reputation', 'validator_consensus', 'gas_used_ratio',
            'uncle_count', 'difficulty_change', 'network_hashrate_change',
            'stake_distribution', 'voting_participation', 'ai_confidence_prev',
            'anomaly_score_tx', 'memory_pool_size'
        ]
        
        if model_path:
            self.load_model(model_path)
        else:
            self.build_model()
    
    def build_model(self) -> None:
        """Build the neural network model for block validation menggunakan TensorFlow"""
        logger.info("🔧 Building TensorFlow model for block validation...")
        
        self.model = keras.Sequential([
            layers.Dense(64, activation='relu', input_shape=(len(self.feature_names),)),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(1, activation='sigmoid')  # Output: 0-1 confidence score
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        logger.info("✅ TensorFlow model built successfully")
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100) -> tf.keras.callbacks.History:
        """Train the model on historical block data"""
        if self.model is None:
            self.build_model()
        
        logger.info(f"🏋️ Training model with {len(X)} samples for {epochs} epochs...")
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )
        
        final_accuracy = history.history['accuracy'][-1]
        logger.info(f"✅ Model training completed - Final Accuracy: {final_accuracy:.4f}")
        return history
    
    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """Predict block validity score using TensorFlow model"""
        if self.model is None:
            logger.warning("❌ Model not loaded, using fallback prediction")
            return {'score': 0.5, 'decision': 'UNKNOWN', 'confidence': 0.0}
        
        try:
            # Convert features to array in correct order
            feature_array = np.array([[features.get(name, 0.0) for name in self.feature_names]])
            
            # Make prediction dengan TensorFlow
            score = float(self.model.predict(feature_array, verbose=0)[0][0])
            
            # Make decision based on score
            if score > 0.85:
                decision = "ACCEPT"
                emoji = "✅"
            elif score > 0.60:
                decision = "REVIEW"
                emoji = "⚠️"
            else:
                decision = "REJECT"
                emoji = "❌"
            
            logger.info(f"{emoji} AI PREDICTION - Score: {score:.3f} - Decision: {decision}")
            
            return {
                'score': score,
                'decision': decision,
                'confidence': abs(score - 0.5) * 2,
                'model': 'TensorFlow_MLP_v1.0'
            }
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            return {'score': 0.5, 'decision': 'ERROR', 'error': str(e)}
    
    def save_model(self, path: str) -> None:
        """Save the trained TensorFlow model"""
        if self.model:
            self.model.save(path)
            logger.info(f"💾 Model saved to {path}")
    
    def load_model(self, path: str) -> None:
        """Load a pre-trained TensorFlow model"""
        try:
            self.model = keras.models.load_model(path)
            logger.info(f"📂 Model loaded from {path}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            logger.info("🆕 Building new model instead...")
            self.build_model()

class BlockFeatureEngine:
    """Feature engineering untuk blockchain validation"""
    
    def __init__(self):
        self.history_window = 100
        self.feature_cache = {}
    
    def extract_features(self, block_data: Dict) -> Dict[str, float]:
        """Extract features from block data untuk model TensorFlow"""
        features = {}
        
        # Basic block features
        features['tx_count'] = len(block_data.get('transactions', []))
        features['total_fee'] = sum(tx.get('fee', 0) for tx in block_data.get('transactions', []))
        features['block_size'] = block_data.get('size', 0)
        
        # Temporal features
        current_time = tf.timestamp() if hasattr(tf, 'timestamp') else 0
        features['timestamp_drift'] = abs(block_data.get('timestamp', 0) - current_time)
        
        # Network features
        features['miner_reputation'] = block_data.get('miner_reputation', 0.5)
        features['validator_consensus'] = len(block_data.get('validator_votes', [])) / max(1, block_data.get('total_validators', 1))
        features['gas_used_ratio'] = block_data.get('gas_used', 0) / max(1, block_data.get('gas_limit', 1))
        features['uncle_count'] = len(block_data.get('uncles', []))
        
        # Economic features
        features['difficulty_change'] = block_data.get('difficulty_change', 0.0)
        features['network_hashrate_change'] = block_data.get('hashrate_change', 0.0)
        features['stake_distribution'] = block_data.get('stake_distribution_gini', 0.5)
        features['voting_participation'] = block_data.get('voting_participation', 0.0)
        
        # Historical features
        features['ai_confidence_prev'] = block_data.get('prev_ai_confidence', 0.5)
        features['anomaly_score_tx'] = self.calculate_tx_anomaly(block_data.get('transactions', []))
        features['memory_pool_size'] = block_data.get('mempool_size', 0)
        
        # Normalize features
        features = self.normalize_features(features)
        
        return features
    
    def calculate_tx_anomaly(self, transactions: List[Dict]) -> float:
        """Calculate transaction anomaly score menggunakan TensorFlow operations"""
        if not transactions:
            return 0.0
        
        try:
            # Extract transaction values
            values = [tx.get('amount', 0) for tx in transactions]
            values_tensor = tf.constant(values, dtype=tf.float32)
            
            # Calculate statistics dengan TensorFlow
            mean_val = tf.reduce_mean(values_tensor)
            std_val = tf.math.reduce_std(values_tensor)
            
            if std_val == 0:
                return 0.0
            
            # Calculate z-scores
            z_scores = tf.abs((values_tensor - mean_val) / std_val)
            anomaly_count = tf.reduce_sum(tf.cast(z_scores > 2.0, tf.float32))
            
            return float(anomaly_count / len(transactions))
            
        except Exception as e:
            logger.error(f"Anomaly calculation error: {e}")
            return 0.0
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalize features to 0-1 range"""
        normalized = {}
        
        # Define normalization ranges
        ranges = {
            'tx_count': (0, 10000),
            'total_fee': (0, 1000000),
            'block_size': (0, 8000000),
            'timestamp_drift': (0, 300),
            'miner_reputation': (0, 1),
            'validator_consensus': (0, 1),
            'gas_used_ratio': (0, 1),
            'uncle_count': (0, 10),
            'difficulty_change': (-0.5, 0.5),
            'network_hashrate_change': (-0.5, 0.5),
            'stake_distribution': (0, 1),
            'voting_participation': (0, 1),
            'ai_confidence_prev': (0, 1),
            'anomaly_score_tx': (0, 1),
            'memory_pool_size': (0, 10000)
        }
        
        for feature, value in features.items():
            if feature in ranges:
                min_val, max_val = ranges[feature]
                # Scale to 0-1
                normalized_val = (value - min_val) / (max_val - min_val)
                # Clip to [0, 1]
                normalized[feature] = max(0.0, min(1.0, normalized_val))
            else:
                normalized[feature] = value
        
        return normalized