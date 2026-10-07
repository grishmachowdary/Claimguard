"""
ClaimGuard ML Infrastructure
Setup for machine learning models, training, and predictions
Includes model versioning, storage, and evaluation
"""
import os
import json
import joblib
from datetime import datetime
from pathlib import Path


class MLModelManager:
    """Manages ML model lifecycle: training, saving, loading, prediction"""
    
    def __init__(self, models_dir='./models', models_metadata_file='./models/registry.json'):
        """
        Initialize ML model manager
        
        Args:
            models_dir: Directory to store serialized models
            models_metadata_file: JSON file to track model versions
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = Path(models_metadata_file)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.registry = self._load_registry()
    
    def _load_registry(self):
        """Load model registry from file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {'models': {}, 'active': {}}
    
    def _save_registry(self):
        """Save model registry to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def register_model(self, model_name, model, metadata=None):
        """
        Save and register a model
        
        Args:
            model_name: Name of the model (e.g., 'approval_predictor')
            model: Trained model object
            metadata: Additional metadata (version, accuracy, training_date, etc.)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = f"{model_name}_v{timestamp}"
        
        # Save model file
        model_path = self.models_dir / f"{version}.joblib"
        joblib.dump(model, model_path)
        
        # Register in metadata
        model_metadata = {
            'name': model_name,
            'version': version,
            'path': str(model_path),
            'saved_at': datetime.now().isoformat(),
            'size_bytes': model_path.stat().st_size,
        }
        
        if metadata:
            model_metadata.update(metadata)
        
        # Track in registry
        if model_name not in self.registry['models']:
            self.registry['models'][model_name] = []
        
        self.registry['models'][model_name].append(model_metadata)
        self.registry['active'][model_name] = version
        self._save_registry()
        
        return {
            'status': 'registered',
            'version': version,
            'path': str(model_path)
        }
    
    def load_model(self, model_name, version=None):
        """
        Load a model
        
        Args:
            model_name: Name of the model
            version: Specific version. If None, load active version.
        """
        if version is None:
            version = self.registry['active'].get(model_name)
            if not version:
                raise ValueError(f"No active version for model: {model_name}")
        
        model_path = self.models_dir / f"{version}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        return joblib.load(model_path)
    
    def get_model_info(self, model_name):
        """Get information about a model and its versions"""
        if model_name not in self.registry['models']:
            return None
        
        versions = self.registry['models'][model_name]
        active = self.registry['active'].get(model_name)
        
        return {
            'name': model_name,
            'active_version': active,
            'versions': versions,
            'total_versions': len(versions)
        }
    
    def list_models(self):
        """List all registered models"""
        return {
            'models': list(self.registry['models'].keys()),
            'active': self.registry['active'],
            'registry': self.registry
        }


class MLPipeline:
    """ML training pipeline for ClaimGuard models"""
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager or MLModelManager()
        self.training_log = []
    
    def log(self, message):
        """Log training step"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.training_log.append(log_entry)
        print(log_entry)
    
    def prepare_training_data(self, claims):
        """
        Prepare training data from claims
        
        Args:
            claims: List of claim objects
        
        Returns:
            X (features), y (labels), feature_names
        """
        self.log(f"Preparing training data from {len(claims)} claims...")
        
        X = []  # Features
        y = []  # Labels (approved/rejected)
        
        for claim in claims:
            # Extract features
            features = self._extract_features(claim)
            X.append(features)
            
            # Extract label (1 = approved, 0 = rejected)
            # This would come from claim.status or claim.insurer_decision
            label = 1 if claim.status == 'approved' else 0
            y.append(label)
        
        self.log(f"✓ Prepared {len(X)} training examples")
        return X, y
    
    def _extract_features(self, claim):
        """Extract features from a claim for ML"""
        import json
        
        features = []
        
        # Document-based features
        uploaded_docs = json.loads(claim.uploaded_docs or '{}')
        features.append(len(uploaded_docs))  # Document count
        
        # Field-based features
        form_data = json.loads(claim.form_data or '{}')
        features.append(len(form_data))  # Filled fields
        
        # Score-based features
        features.append(claim.readiness_score or 0)
        
        # Extract individual scores if available
        breakdown = json.loads(claim.score_breakdown or '{}')
        features.append(breakdown.get('document', 0))
        features.append(breakdown.get('field', 0))
        features.append(breakdown.get('consistency', 0))
        
        # Type-based feature
        features.append(claim.insurance_type_id or 0)
        
        # Customer-based features (if available)
        # features.append(claim.user.claim_count or 0)
        # features.append(claim.user.approval_rate or 0)
        
        return features
    
    def train_approval_model(self, claims):
        """
        Train ML model for approval prediction
        
        Args:
            claims: List of claims with approval status
        """
        self.log("Starting approval prediction model training...")
        
        try:
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # Prepare data
            X, y = self.prepare_training_data(claims)
            
            if len(set(y)) < 2:
                self.log("⚠ Warning: Not enough labeled data (need both approved and rejected claims)")
                return None
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            self.log(f"Training set: {len(X_train)}, Test set: {len(X_test)}")
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                random_state=42,
                n_jobs=-1
            )
            
            self.log("Training Random Forest model...")
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            # Log metrics
            metrics = {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'training_date': datetime.now().isoformat(),
                'training_examples': len(X_train),
                'test_examples': len(X_test),
            }
            
            self.log(f"✓ Model trained successfully")
            self.log(f"  Accuracy:  {accuracy:.3f}")
            self.log(f"  Precision: {precision:.3f}")
            self.log(f"  Recall:    {recall:.3f}")
            self.log(f"  F1-Score:  {f1:.3f}")
            
            # Register model
            result = self.model_manager.register_model(
                'approval_predictor',
                model,
                metadata=metrics
            )
            
            self.log(f"✓ Model registered: {result['version']}")
            return model
            
        except ImportError as e:
            self.log(f"✗ ML libraries not available: {str(e)}")
            self.log("  Install with: pip install scikit-learn")
            return None
        except Exception as e:
            self.log(f"✗ Training failed: {str(e)}")
            return None
    
    def predict_approval(self, claim, model=None):
        """
        Predict approval probability for a claim
        
        Args:
            claim: Claim object
            model: Trained model (uses active if not provided)
        
        Returns:
            Approval probability (0-1)
        """
        if model is None:
            try:
                model = self.model_manager.load_model('approval_predictor')
            except:
                self.log("⚠ No trained model available")
                return None
        
        # Extract features
        features = [self._extract_features(claim)]
        
        # Predict
        approval_prob = model.predict_proba(features)[0][1]
        return approval_prob
    
    def get_training_report(self):
        """Get full training report"""
        return '\n'.join(self.training_log)


class FeatureEngineer:
    """Feature engineering utilities for ML models"""
    
    @staticmethod
    def normalize_features(features, feature_ranges=None):
        """Normalize features to 0-1 range"""
        if feature_ranges is None:
            feature_ranges = [(0, 100)] * len(features)
        
        normalized = []
        for feat, (min_val, max_val) in zip(features, feature_ranges):
            if max_val - min_val == 0:
                normalized.append(0)
            else:
                normalized.append((feat - min_val) / (max_val - min_val))
        
        return normalized
    
    @staticmethod
    def extract_advanced_features(claim):
        """Extract advanced features for better predictions"""
        import json
        
        features = {}
        
        # Document quality
        uploaded_docs = json.loads(claim.uploaded_docs or '[]')
        features['doc_count'] = len(uploaded_docs)
        features['docs_complete'] = 1 if len(uploaded_docs) >= 8 else 0
        
        # Form quality
        form_data = json.loads(claim.form_data or '{}')
        features['fields_filled'] = len(form_data)
        features['fields_complete'] = 1 if len(form_data) >= 8 else 0
        
        # Scores
        breakdown = json.loads(claim.score_breakdown or '{}')
        features['doc_score'] = breakdown.get('document', 0)
        features['field_score'] = breakdown.get('field', 0)
        features['consistency_score'] = breakdown.get('consistency', 0)
        features['total_score'] = claim.readiness_score or 0
        
        # Insurance type
        features['insurance_type'] = claim.insurance_type_id or 0
        
        return features


if __name__ == '__main__':
    # Example usage
    manager = MLModelManager()
    print("✓ ML Infrastructure ready")
    print(f"Models directory: {manager.models_dir}")
    print(f"Registry file: {manager.metadata_file}")
