import joblib
from django.conf import settings
import os

class PostureAnalyzer:
    def __init__(self):
        self.posture_model = None
        self.fall_model = None
        self.load_models()
    
    def load_models(self):
        try:
            posture_model_path = os.path.join(settings.ML_MODELS_DIR, 'posture_model.pkl')
            fall_model_path = os.path.join(settings.ML_MODELS_DIR, 'fall_detection_model.pkl')
            
            if os.path.exists(posture_model_path):
                self.posture_model = joblib.load(posture_model_path)
            if os.path.exists(fall_model_path):
                self.fall_model = joblib.load(fall_model_path)
                
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def predict_posture(self, tilt_x, tilt_y):
        """
        Predict if posture is correct based on tilt sensor data
        Returns: True if correct posture, False if incorrect
        """
        if not self.posture_model:
            return None
        
        try:
            # Create a list of lists instead of numpy array
            features = [[tilt_x, tilt_y]]
            prediction = self.posture_model.predict(features)[0]
            probability = self.posture_model.predict_proba(features)[0]
            
            return {
                'is_correct': bool(prediction),
                'confidence': float(max(probability))
            }
        except Exception as e:
            print(f"Error predicting posture: {e}")
            return None
    
    def predict_fall(self, gyro_x, gyro_y, gyro_z):
        """
        Predict if a fall has occurred based on gyroscope data
        Returns: True if fall detected, False otherwise
        """
        if not self.fall_model:
            return None
        
        try:
            # Create a list of lists instead of numpy array
            features = [[gyro_x, gyro_y, gyro_z]]
            prediction = self.fall_model.predict(features)[0]
            probability = self.fall_model.predict_proba(features)[0]
            
            return {
                'is_fall': bool(prediction),
                'confidence': float(max(probability))
            }
        except Exception as e:
            print(f"Error predicting fall: {e}")
            return None
    
    def analyze_batch_data(self, data_list):
        """
        Analyze batch data for offline mode
        data_list: list of dictionaries with tilt_x, tilt_y values
        """
        results = []
        correct_count = 0
        
        for data in data_list:
            posture_result = self.predict_posture(data['tilt_x'], data['tilt_y'])
            if posture_result and posture_result['is_correct']:
                correct_count += 1
            results.append(posture_result)
        
        # Calculate percentage using basic arithmetic
        total_samples = len(data_list)
        correctness_percentage = (correct_count / total_samples) * 100 if total_samples > 0 else 0
        
        return {
            'results': results,
            'correctness_percentage': correctness_percentage,
            'total_samples': total_samples,
            'correct_samples': correct_count
        }

# Alternative implementation if joblib models don't work with Python lists
class SimplePostureAnalyzer:
    def __init__(self):
        self.posture_model = None
        self.fall_model = None
        self.load_models()
    
    def load_models(self):
        try:
            posture_model_path = os.path.join(settings.ML_MODELS_DIR, 'posture_model.pkl')
            fall_model_path = os.path.join(settings.ML_MODELS_DIR, 'fall_detection_model.pkl')
            
            if os.path.exists(posture_model_path):
                self.posture_model = joblib.load(posture_model_path)
            if os.path.exists(fall_model_path):
                self.fall_model = joblib.load(fall_model_path)
                
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def _convert_to_model_input(self, data):
        """Convert Python list to format expected by the model"""
        try:
            # If the model was trained with numpy, we might need to use array-like structure
            # Most scikit-learn models accept list of lists
            return data
        except Exception:
            # If that fails, you might need a different approach
            return data
    
    def predict_posture(self, tilt_x, tilt_y):
        """
        Predict if posture is correct based on tilt sensor data
        Returns: True if correct posture, False if incorrect
        """
        if not self.posture_model:
            return None
        
        try:
            features = self._convert_to_model_input([[float(tilt_x), float(tilt_y)]])
            prediction = self.posture_model.predict(features)[0]
            
            # Handle probability prediction
            try:
                probability = self.posture_model.predict_proba(features)[0]
                confidence = float(max(probability))
            except AttributeError:
                # Model doesn't have predict_proba method
                confidence = 1.0 if prediction else 0.0
            
            return {
                'is_correct': bool(prediction),
                'confidence': confidence
            }
        except Exception as e:
            print(f"Error predicting posture: {e}")
            return None
    
    def predict_fall(self, gyro_x, gyro_y, gyro_z):
        """
        Predict if a fall has occurred based on gyroscope data
        Returns: True if fall detected, False otherwise
        """
        if not self.fall_model:
            return None
        
        try:
            features = self._convert_to_model_input([[float(gyro_x), float(gyro_y), float(gyro_z)]])
            prediction = self.fall_model.predict(features)[0]
            
            # Handle probability prediction
            try:
                probability = self.fall_model.predict_proba(features)[0]
                confidence = float(max(probability))
            except AttributeError:
                # Model doesn't have predict_proba method
                confidence = 1.0 if prediction else 0.0
            
            return {
                'is_fall': bool(prediction),
                'confidence': confidence
            }
        except Exception as e:
            print(f"Error predicting fall: {e}")
            return None
    
    def analyze_batch_data(self, data_list):
        """
        Analyze batch data for offline mode
        data_list: list of dictionaries with tilt_x, tilt_y values
        """
        results = []
        correct_count = 0
        
        for data in data_list:
            posture_result = self.predict_posture(data['tilt_x'], data['tilt_y'])
            if posture_result and posture_result['is_correct']:
                correct_count += 1
            results.append(posture_result)
        
        total_samples = len(data_list)
        correctness_percentage = (correct_count / total_samples) * 100 if total_samples > 0 else 0
        
        return {
            'results': results,
            'correctness_percentage': correctness_percentage,
            'total_samples': total_samples,
            'correct_samples': correct_count
        }

# Global analyzer instance
posture_analyzer = PostureAnalyzer()