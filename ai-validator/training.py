import tensorflow as tf
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from model import AIValidator, BlockFeatureEngine
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """Trainer untuk AI Validator model menggunakan TensorFlow"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.validator = AIValidator()
        self.feature_engine = BlockFeatureEngine()
    
    def generate_training_data(self, num_samples: int = 10000) -> tuple:
        """Generate synthetic training data dengan TensorFlow operations"""
        logger.info(f"🏗️ Generating {num_samples} training samples dengan TensorFlow...")
        
        tf.random.set_seed(42)
        np.random.seed(42)
        
        X = []
        y = []
        
        for i in range(num_samples):
            # Generate realistic block features
            features = {
                'tx_count': float(np.random.poisson(150)),
                'total_fee': float(np.random.exponential(1000)),
                'block_size': float(np.random.normal(80000, 20000)),
                'timestamp_drift': float(np.random.exponential(2)),
                'miner_reputation': float(np.random.beta(2, 2)),
                'validator_consensus': float(np.random.beta(8, 2)),
                'gas_used_ratio': float(np.random.beta(5, 5)),
                'uncle_count': float(np.random.poisson(0.1)),
                'difficulty_change': float(np.random.normal(0, 0.1)),
                'network_hashrate_change': float(np.random.normal(0, 0.05)),
                'stake_distribution': float(np.random.beta(2, 5)),
                'voting_participation': float(np.random.beta(7, 3)),
                'ai_confidence_prev': float(np.random.beta(8, 2)),
                'anomaly_score_tx': float(np.random.beta(1, 10)),
                'memory_pool_size': float(np.random.poisson(5000))
            }
            
            # Normalize features
            normalized_features = self.feature_engine.normalize_features(features)
            feature_array = [normalized_features.get(name, 0.0) for name in self.validator.feature_names]
            
            # Determine label - complex validation rules
            is_valid = (
                features['timestamp_drift'] < 10 and
                features['validator_consensus'] > 0.6 and
                features['anomaly_score_tx'] < 0.3 and
                features['miner_reputation'] > 0.3 and
                np.random.random() > 0.1  # 90% valid blocks
            )
            
            X.append(feature_array)
            y.append(1.0 if is_valid else 0.0)
        
        X_array = np.array(X, dtype=np.float32)
        y_array = np.array(y, dtype=np.float32)
        
        logger.info(f"✅ Generated {len(X_array)} samples - Valid blocks: {np.sum(y_array)}")
        return X_array, y_array
    
    def train_model(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> dict:
        """Train the TensorFlow model"""
        logger.info("🚀 Starting TensorFlow model training...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        logger.info(f"📊 Training set: {len(X_train)}, Test set: {len(X_test)}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Convert to TensorFlow datasets for better performance
        train_dataset = tf.data.Dataset.from_tensor_slices((X_train_scaled, y_train))
        test_dataset = tf.data.Dataset.from_tensor_slices((X_test_scaled, y_test))
        
        train_dataset = train_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
        test_dataset = test_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
        
        # Train model
        history = self.validator.model.fit(
            train_dataset,
            epochs=100,
            validation_data=test_dataset,
            verbose=1,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
            ]
        )
        
        # Evaluate model
        test_loss, test_accuracy, test_precision, test_recall = self.validator.model.evaluate(
            test_dataset, verbose=0
        )
        
        # Predictions for additional metrics
        y_pred = self.validator.model.predict(X_test_scaled, verbose=0)
        y_pred_binary = (y_pred > 0.5).astype(int).flatten()
        
        from sklearn.metrics import classification_report, confusion_matrix
        cm = confusion_matrix(y_test, y_pred_binary)
        cr = classification_report(y_test, y_pred_binary, output_dict=True)
        
        metrics = {
            'test_loss': float(test_loss),
            'test_accuracy': float(test_accuracy),
            'test_precision': float(test_precision),
            'test_recall': float(test_recall),
            'confusion_matrix': cm.tolist(),
            'classification_report': cr,
            'training_history': {
                'accuracy': [float(x) for x in history.history['accuracy']],
                'val_accuracy': [float(x) for x in history.history['val_accuracy']],
                'loss': [float(x) for x in history.history['loss']],
                'val_loss': [float(x) for x in history.history['val_loss']]
            }
        }
        
        logger.info(f"✅ Training completed!")
        logger.info(f"📈 Final Test Accuracy: {test_accuracy:.4f}")
        logger.info(f"🎯 Final Test Precision: {test_precision:.4f}")
        logger.info(f"🔍 Final Test Recall: {test_recall:.4f}")
        
        return metrics
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, folds: int = 5) -> dict:
        """Perform cross-validation dengan TensorFlow"""
        from sklearn.model_selection import KFold
        
        logger.info(f"🔄 Starting {folds}-fold cross-validation...")
        
        kfold = KFold(n_splits=folds, shuffle=True, random_state=42)
        fold_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(kfold.split(X)):
            logger.info(f"🔄 Training fold {fold + 1}/{folds}")
            
            # Split data
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Create new model for this fold
            fold_validator = AIValidator()
            fold_validator.build_model()
            
            # Convert to TensorFlow datasets
            train_dataset = tf.data.Dataset.from_tensor_slices((X_train_scaled, y_train))
            val_dataset = tf.data.Dataset.from_tensor_slices((X_val_scaled, y_val))
            
            train_dataset = train_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
            val_dataset = val_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
            
            # Train with early stopping
            fold_validator.model.fit(
                train_dataset,
                epochs=50,
                validation_data=val_dataset,
                verbose=0,
                callbacks=[tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)]
            )
            
            # Evaluate
            val_loss, val_accuracy, val_precision, val_recall = fold_validator.model.evaluate(
                val_dataset, verbose=0
            )
            
            fold_scores.append({
                'fold': fold + 1,
                'accuracy': float(val_accuracy),
                'precision': float(val_precision),
                'recall': float(val_recall),
                'loss': float(val_loss)
            })
            
            logger.info(f"✅ Fold {fold + 1} - Accuracy: {val_accuracy:.4f}")
        
        # Calculate statistics
        accuracies = [s['accuracy'] for s in fold_scores]
        precisions = [s['precision'] for s in fold_scores]
        recalls = [s['recall'] for s in fold_scores]
        
        avg_scores = {
            'mean_accuracy': float(np.mean(accuracies)),
            'std_accuracy': float(np.std(accuracies)),
            'mean_precision': float(np.mean(precisions)),
            'mean_recall': float(np.mean(recalls)),
            'fold_scores': fold_scores
        }
        
        logger.info(f"🎯 Cross-validation completed!")
        logger.info(f"📊 Mean Accuracy: {avg_scores['mean_accuracy']:.4f} ± {avg_scores['std_accuracy']:.4f}")
        
        return avg_scores
    
    def save_training_artifacts(self, model_path: str, scaler_path: str, metrics_path: str) -> None:
        """Save trained model and artifacts"""
        self.validator.save_model(model_path)
        joblib.dump(self.scaler, scaler_path)
        
        # Save training metrics
        metrics = {
            'feature_names': self.validator.feature_names,
            'model_architecture': 'MLP_64_32_16',
            'input_shape': self.validator.model.input_shape,
            'output_shape': self.validator.model.output_shape,
            'total_params': self.validator.model.count_params(),
            'timestamp': tf.timestamp().numpy()
        }
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"💾 Training artifacts saved:")
        logger.info(f"   - Model: {model_path}")
        logger.info(f"   - Scaler: {scaler_path}")
        logger.info(f"   - Metrics: {metrics_path}")

def main():
    """Main training script"""
    logger.info("🎬 Starting AI Validator training process...")
    
    trainer = ModelTrainer()
    
    # Generate training data
    logger.info("📊 Generating training data...")
    X, y = trainer.generate_training_data(5000)  # Smaller for quick testing
    
    # Train model
    logger.info("🏋️ Training model...")
    metrics = trainer.train_model(X, y)
    
    # Cross-validation
    logger.info("🔄 Running cross-validation...")
    cv_scores = trainer.cross_validate(X, y, folds=3)  # Fewer folds for speed
    
    # Save artifacts
    os.makedirs('models', exist_ok=True)
    trainer.save_training_artifacts(
        'models/block_validator.h5',
        'models/scaler.joblib',
        'models/training_metrics.json'
    )
    
    # Print results
    print("\n" + "="*50)
    print("🎯 TRAINING RESULTS SUMMARY")
    print("="*50)
    print(f"📈 Test Accuracy:    {metrics['test_accuracy']:.4f}")
    print(f"🎯 Test Precision:   {metrics['test_precision']:.4f}")
    print(f"🔍 Test Recall:      {metrics['test_recall']:.4f}")
    print(f"🔄 CV Mean Accuracy: {cv_scores['mean_accuracy']:.4f} ± {cv_scores['std_accuracy']:.4f}")
    print("="*50)

if __name__ == '__main__':
    # Configure TensorFlow for better performance
    tf.config.optimizer.set_jit(True)  # Enable XLA compilation
    physical_devices = tf.config.list_physical_devices('GPU')
    if len(physical_devices) > 0:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
        logger.info("🎮 GPU available and configured")
    
    main()