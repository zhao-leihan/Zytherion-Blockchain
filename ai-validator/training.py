import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from model import AIValidator, FeatureExtractor
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """Handles training and evaluation of the AI validator model"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.validator = AIValidator()
    
    def load_training_data(self, filepath: str) -> tuple:
        """Load training data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            X = np.array([sample['features'] for sample in data['samples']])
            y = np.array([sample['label'] for sample in data['samples']])
            
            logger.info(f"Loaded {len(X)} training samples")
            return X, y
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            raise
    
    def generate_synthetic_data(self, num_samples: int = 10000) -> tuple:
        """Generate synthetic training data for initial model"""
        logger.info(f"Generating {num_samples} synthetic training samples")
        
        np.random.seed(42)
        
        X = []
        y = []
        
        for i in range(num_samples):
            # Generate realistic blockchain features
            features = {
                'tx_count': np.random.poisson(150),  # Typical block has ~150 tx
                'total_fee': np.random.exponential(1000),
                'block_size': np.random.normal(80000, 20000),
                'timestamp_drift': np.random.exponential(2),
                'miner_reputation': np.random.beta(2, 2),
                'validator_consensus': np.random.beta(8, 2),  # Usually high consensus
                'gas_used_ratio': np.random.beta(5, 5),
                'uncle_count': np.random.poisson(0.1),  # Rare uncles
                'difficulty_change': np.random.normal(0, 0.1),
                'network_hashrate_change': np.random.normal(0, 0.05),
                'stake_distribution': np.random.beta(2, 5),  # Usually somewhat unequal
                'voting_participation': np.random.beta(7, 3),  # Usually high participation
                'ai_confidence_prev': np.random.beta(8, 2),
                'anomaly_score_tx': np.random.beta(1, 10),  # Usually low anomaly
                'memory_pool_size': np.random.poisson(5000)
            }
            
            # Normalize features
            normalized_features = FeatureExtractor.normalize_features(features)
            feature_array = [normalized_features.get(name, 0.0) for name in self.validator.feature_names]
            
            # Determine label (1 = valid, 0 = invalid)
            # Rules for synthetic valid blocks:
            is_valid = (
                features['timestamp_drift'] < 10 and
                features['validator_consensus'] > 0.6 and
                features['anomaly_score_tx'] < 0.3 and
                features['miner_reputation'] > 0.3 and
                np.random.random() > 0.1  # 90% of blocks are valid
            )
            
            X.append(feature_array)
            y.append(1.0 if is_valid else 0.0)
        
        return np.array(X), np.array(y)
    
    def train_model(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> dict:
        """Train the model and return performance metrics"""
        logger.info("Starting model training...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        history = self.validator.model.fit(
            X_train_scaled, y_train,
            epochs=100,
            batch_size=32,
            validation_data=(X_test_scaled, y_test),
            verbose=1
        )
        
        # Evaluate model
        test_loss, test_accuracy, test_precision, test_recall = self.validator.model.evaluate(
            X_test_scaled, y_test, verbose=0
        )
        
        metrics = {
            'test_loss': test_loss,
            'test_accuracy': test_accuracy,
            'test_precision': test_precision,
            'test_recall': test_recall,
            'training_history': history.history
        }
        
        logger.info(f"Training completed. Test accuracy: {test_accuracy:.4f}")
        
        return metrics
    
    def save_training_artifacts(self, model_path: str, scaler_path: str) -> None:
        """Save trained model and scaler"""
        self.validator.save_model(model_path)
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Training artifacts saved: {model_path}, {scaler_path}")
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, folds: int = 5) -> dict:
        """Perform cross-validation"""
        from sklearn.model_selection import KFold
        from tensorflow.keras.models import clone_model
        
        kfold = KFold(n_splits=folds, shuffle=True, random_state=42)
        fold_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(kfold.split(X)):
            logger.info(f"Training fold {fold + 1}/{folds}")
            
            # Split data
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Create new model for this fold
            fold_model = AIValidator()
            fold_model.build_model()
            
            # Train
            fold_model.model.fit(
                X_train_scaled, y_train,
                epochs=50,
                batch_size=32,
                verbose=0
            )
            
            # Evaluate
            val_loss, val_accuracy, val_precision, val_recall = fold_model.model.evaluate(
                X_val_scaled, y_val, verbose=0
            )
            
            fold_scores.append({
                'fold': fold + 1,
                'accuracy': val_accuracy,
                'precision': val_precision,
                'recall': val_recall,
                'loss': val_loss
            })
        
        # Calculate average scores
        avg_scores = {
            'mean_accuracy': np.mean([s['accuracy'] for s in fold_scores]),
            'std_accuracy': np.std([s['accuracy'] for s in fold_scores]),
            'mean_precision': np.mean([s['precision'] for s in fold_scores]),
            'mean_recall': np.mean([s['recall'] for s in fold_scores]),
            'fold_scores': fold_scores
        }
        
        logger.info(f"Cross-validation completed. Mean accuracy: {avg_scores['mean_accuracy']:.4f}")
        return avg_scores

def main():
    """Main training script"""
    trainer = ModelTrainer()
    
    # Generate synthetic data (in real scenario, use historical data)
    logger.info("Generating synthetic training data...")
    X, y = trainer.generate_synthetic_data(10000)
    
    # Train model
    metrics = trainer.train_model(X, y)
    
    # Perform cross-validation
    cv_scores = trainer.cross_validate(X, y, folds=5)
    
    # Save model and artifacts
    trainer.save_training_artifacts(
        'models/block_validator.h5',
        'models/scaler.joblib'
    )
    
    # Print results
    print("\n=== Training Results ===")
    print(f"Test Accuracy: {metrics['test_accuracy']:.4f}")
    print(f"Test Precision: {metrics['test_precision']:.4f}")
    print(f"Test Recall: {metrics['test_recall']:.4f}")
    print(f"Cross-val Mean Accuracy: {cv_scores['mean_accuracy']:.4f} ± {cv_scores['std_accuracy']:.4f}")

if __name__ == '__main__':
    main()