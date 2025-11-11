from flask import Flask, request, jsonify
import json
import logging
import time
from threading import Thread
import os
import numpy as np

# TensorFlow imports
from model import AIValidator, BlockFeatureEngine
from features import AdvancedFeatureEngine
import tensorflow as tf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class AIService:
    def __init__(self):
        self.validator = AIValidator()
        self.feature_engine = BlockFeatureEngine()
        self.advanced_engine = AdvancedFeatureEngine()
        self.blocks_processed = 0
        self.anomalies_detected = 0
        
        # Load pre-trained model jika ada
        self.load_model()
    
    def load_model(self):
        """Load pre-trained TensorFlow model"""
        model_path = "models/block_validator.h5"
        if os.path.exists(model_path):
            logger.info("📂 Loading pre-trained TensorFlow model...")
            self.validator.load_model(model_path)
        else:
            logger.warning("❌ No pre-trained model found. Using untrained model.")
    
    def validate_block(self, block_data):
        """Validate block menggunakan TensorFlow model"""
        try:
            logger.info(f"🔍 Validating block #{block_data.get('height', '?')} dengan TensorFlow...")
            
            # Extract features
            basic_features = self.feature_engine.extract_features(block_data)
            
            # Add advanced features
            advanced_features = self.advanced_engine.compute_advanced_features(
                block_data, 
                []  # In real scenario, pass previous blocks
            )
            
            # Combine features
            all_features = {**basic_features, **advanced_features}
            
            # AI Validation dengan TensorFlow
            validation_result = self.validator.predict(all_features)
            
            # Update statistics
            self.blocks_processed += 1
            if validation_result['decision'] == 'REJECT':
                self.anomalies_detected += 1
            
            # Add processing info
            validation_result.update({
                'blocks_processed': self.blocks_processed,
                'anomalies_detected': self.anomalies_detected,
                'success_rate': (self.blocks_processed - self.anomalies_detected) / max(self.blocks_processed, 1),
                'feature_count': len(all_features),
                'tensorflow_version': tf.__version__
            })
            
            logger.info(f"🤖 TensorFlow Validation Complete - "
                       f"Block: #{block_data.get('height', '?')}, "
                       f"Score: {validation_result['score']:.3f}, "
                       f"Decision: {validation_result['decision']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ TensorFlow validation error: {e}")
            return {
                'score': 0.5, 
                'decision': 'ERROR', 
                'error': str(e),
                'model': 'TensorFlow_Error'
            }
    
    def get_stats(self):
        """Get service statistics"""
        return {
            "blocks_processed": self.blocks_processed,
            "anomalies_detected": self.anomalies_detected,
            "success_rate": (self.blocks_processed - self.anomalies_detected) / max(self.blocks_processed, 1),
            "tensorflow_loaded": self.validator.model is not None,
            "service_uptime": time.time() - self.start_time
        }

# Initialize AI Service
ai_service = AIService()
ai_service.start_time = time.time()

class BlockLogger:
    """Logging system untuk blocks"""
    def __init__(self):
        self.log_dir = "data"
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log_validation(self, block_data, validation_result):
        """Log validation results"""
        try:
            log_entry = {
                "timestamp": time.time(),
                "block_height": block_data.get('height', 0),
                "block_hash": block_data.get('hash', 'unknown'),
                "tx_count": block_data.get('tx_count', 0),
                "miner": block_data.get('miner', 'unknown'),
                "ai_score": validation_result['score'],
                "ai_decision": validation_result['decision'],
                "ai_confidence": validation_result['confidence'],
                "validator_model": validation_result.get('model', 'unknown'),
                "tensorflow_version": tf.__version__
            }
            
            log_file = os.path.join(self.log_dir, "block_validations.jsonl")
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.info(f"📝 Logged validation - Height: {log_entry['block_height']}, "
                       f"Score: {validation_result['score']:.3f}")
                       
        except Exception as e:
            logger.error(f"❌ Logging error: {e}")

# Initialize logger
block_logger = BlockLogger()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stats = ai_service.get_stats()
    return jsonify({
        'status': 'healthy',
        'service': 'zytherion-ai-validator-tensorflow',
        'tensorflow_version': tf.__version__,
        'timestamp': time.time(),
        'statistics': stats
    })

@app.route('/validate/block', methods=['POST'])
def validate_block():
    """
    Validate a block menggunakan TensorFlow model
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # AI Validation dengan TensorFlow
        validation_result = ai_service.validate_block(data)
        
        # Log the validation
        block_logger.log_validation(data, validation_result)
        
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"❌ Validation endpoint error: {e}")
        return jsonify({
            'error': str(e),
            'score': 0.5,
            'decision': 'ERROR',
            'tensorflow_version': tf.__version__
        }), 500

@app.route('/model/info', methods=['GET'])
def model_info():
    """Get TensorFlow model information"""
    if ai_service.validator.model is None:
        return jsonify({'error': 'Model not loaded'}), 400
    
    try:
        model = ai_service.validator.model
        info = {
            'model_loaded': True,
            'input_shape': model.input_shape,
            'output_shape': model.output_shape,
            'layers': len(model.layers),
            'total_params': model.count_params(),
            'feature_names': ai_service.validator.feature_names,
            'tensorflow_version': tf.__version__
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/train/generate', methods=['POST'])
def generate_training_data():
    """Generate training data"""
    try:
        from training import ModelTrainer
        trainer = ModelTrainer()
        X, y = trainer.generate_training_data(1000)  # Generate 1000 samples
        
        return jsonify({
            'samples_generated': len(X),
            'positive_samples': int(np.sum(y)),
            'negative_samples': int(len(y) - np.sum(y)),
            'data_shape': X.shape
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def simulate_block_validation():
    """Simulate block validation for testing TensorFlow model"""
    logger.info("🎮 Starting TensorFlow block validation simulator...")
    
    block_id = 1
    while True:
        time.sleep(8)  # Validate block every 8 seconds
        
        # Generate test block
        test_block = {
            'height': block_id,
            'hash': f"0x{os.urandom(16).hex()}",
            'timestamp': int(time.time()),
            'tx_count': np.random.randint(10, 200),
            'miner': f"miner_{np.random.randint(1, 5)}",
            'size': np.random.randint(50000, 1000000),
            'transactions': [{'amount': np.random.randint(1, 1000), 'fee': np.random.randint(1, 10)} 
                           for _ in range(np.random.randint(5, 50))]
        }
        
        # Validate with TensorFlow AI
        validation = ai_service.validate_block(test_block)
        
        block_id += 1

def start_server(host='0.0.0.0', port=5000):
    """Start the TensorFlow AI validator server"""
    # Start simulation in background
    simulator_thread = Thread(target=simulate_block_validation, daemon=True)
    simulator_thread.start()
    
    logger.info(f"🤖 TensorFlow AI Validator starting on {host}:{port}")
    logger.info(f"🔧 TensorFlow Version: {tf.__version__}")
    logger.info(f"📊 Available devices: {tf.config.list_physical_devices()}")
    
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    # Configure TensorFlow
    tf.config.optimizer.set_jit(True)  # Enable XLA for better performance
    
    start_server()