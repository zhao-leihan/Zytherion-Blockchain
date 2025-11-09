from flask import Flask, request, jsonify
import json
import logging
import time
import threading
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class SimpleAIValidator:
    """Simplified AI validator for demonstration"""
    
    def __init__(self):
        self.feature_names = [
            'tx_count', 'total_fee', 'block_size', 'timestamp_drift',
            'miner_reputation', 'validator_consensus'
        ]
    
    def predict(self, features):
        """Simple rule-based validation for demo"""
        score = 0.5
        
        # Simple rules
        if features.get('tx_count', 0) > 10000:
            score -= 0.2
        if features.get('timestamp_drift', 0) > 30:
            score -= 0.3
        if features.get('validator_consensus', 0) > 0.8:
            score += 0.2
            
        score = max(0.0, min(1.0, score))
        
        decision = "accept" if score > 0.7 else "reject" if score < 0.4 else "review"
        
        return {
            'score': score,
            'decision': decision,
            'confidence': abs(score - 0.5) * 2
        }

# Global AI validator instance
ai_validator = SimpleAIValidator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'zytherion-ai-validator',
        'timestamp': time.time()
    })

@app.route('/validate/block', methods=['POST'])
def validate_block():
    """
    Validate a block using AI model
    Expects JSON with block data
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        logger.info(f"Validating block: {data.get('hash', 'unknown')}")
        
        # Extract simple features
        features = {
            'tx_count': len(data.get('transactions', [])),
            'total_fee': sum(tx.get('fee', 0) for tx in data.get('transactions', [])),
            'block_size': data.get('size', 0),
            'timestamp_drift': abs(data.get('timestamp', 0) - time.time()),
            'miner_reputation': 0.5,  # Default
            'validator_consensus': len(data.get('validator_votes', [])) / max(1, data.get('total_validators', 1))
        }
        
        # Get AI prediction
        prediction = ai_validator.predict(features)
        
        # Add block identifier to response
        prediction['block'] = data.get('hash', 'unknown')
        prediction['height'] = data.get('height', 0)
        
        logger.info(f"Block validation result: {prediction}")
        
        return jsonify(prediction)
        
    except Exception as e:
        logger.error(f"Error validating block: {e}")
        return jsonify({
            'error': str(e),
            'score': 0.5,
            'decision': 'error'
        }), 500

def start_server(host='0.0.0.0', port=5000):
    """Start the AI validator server"""
    logger.info(f"Starting AI Validator server on {host}:{port}")
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    start_server()