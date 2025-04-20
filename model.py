# import pandas as pd
# import numpy as np
# from sklearn.preprocessing import StandardScaler
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense
# from tensorflow.keras.optimizers import Adam
# from joblib import dump

# class AINetworkMonitor:
#     def __init__(self):
#         self.scaler = StandardScaler()
#         # Updated to include 'none' and match your dataset
#         self.classes = ['none', 'normal', 'high_cpu', 'high_memory', 'high_latency',
#                        'packet_loss', 'bandwidth_saturation', 'high_errors', 'multiple_issues']
        
#     def verify_dataset(self, df):
#         required_columns = {
#             'cpu_usage': 'float64',
#             'memory_usage': 'float64',
#             'bandwidth_mbps': 'float64',
#             'latency_ms': 'float64',
#             'packet_loss_percent': 'float64',
#             'error_rate_percent': 'float64',
#             'issue_detected': 'object'
#         }
        
#         for col, dtype in required_columns.items():
#             if col not in df.columns:
#                 raise ValueError(f"Missing column: {col}")
#             if df[col].dtype != dtype:
#                 raise ValueError(f"Column {col} has wrong dtype. Expected {dtype}, got {df[col].dtype}")
        
#         # Additional check for labels
#         unique_labels = df['issue_detected'].unique()
#         for label in unique_labels:
#             if label not in self.classes:
#                 raise ValueError(f"Label '{label}' not in model's classes list")
        
#         print("Dataset validation passed!")

#     def build_model(self):
#         model = Sequential([
#             Dense(64, activation='relu', input_dim=6),
#             Dense(32, activation='relu'),
#             Dense(len(self.classes), activation='softmax')  # Now matches all possible labels
#         ])
#         model.compile(optimizer=Adam(0.001),
#                     loss='sparse_categorical_crossentropy',
#                     metrics=['accuracy'])
#         return model

#     def train(self, data_path='network_performance_dataset.csv'):
#         df = pd.read_csv(data_path)
#         self.verify_dataset(df)
        
#         X = df[['cpu_usage', 'memory_usage', 'bandwidth_mbps',
#                 'latency_ms', 'packet_loss_percent', 'error_rate_percent']]
#         y = df['issue_detected'].apply(lambda x: self.classes.index(x))
        
#         X = self.scaler.fit_transform(X)
#         self.model = self.build_model()
#         self.model.fit(X, y, epochs=20, batch_size=32, validation_split=0.2)
        
#         dump({'model': self.model, 'scaler': self.scaler, 'classes': self.classes}, 
#              'network_ai.joblib')
#         print(f"Model trained and saved! Classes: {self.classes}")

# if __name__ == "__main__":
#     monitor = AINetworkMonitor()
#     monitor.train()


import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Lambda
from tensorflow.keras.optimizers import Adam
from joblib import dump
import tensorflow as tf

class QuantumInspiredMonitor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.classes = ['none', 'normal', 'high_cpu', 'high_memory', 'high_latency', 
                        'packet_loss', 'bandwidth_saturation', 'high_errors', 'multiple_issues']
    
    def _quantum_inspired_layer(self, x):
        """Classical approximation of quantum operations"""
        # Quantum-inspired rotation (using classical trigonometry)
        sin_trans = tf.math.sin(x * np.pi)  # Simulates quantum rotations
        cos_trans = tf.math.cos(x * np.pi)
        
        # Entanglement simulation (non-linear mixing)
        entangled = tf.multiply(sin_trans, cos_trans)
        return entangled
    
    def build_model(self):
        model = Sequential([
            # Classical input
            Dense(64, activation='relu', input_dim=6),
            
            # Quantum-inspired transformations
            Lambda(self._quantum_inspired_layer),
            Dense(32, activation='relu'),
            
            # Output with quantum-inspired interference
            Dense(len(self.classes), 
                  activation=lambda x: tf.math.abs(x)  # Probability-like output
            )
        ])
        
        model.compile(
            optimizer=Adam(0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        return model

    def train(self, data_path):
        df = pd.read_csv(data_path)
        X = df[['cpu_usage', 'memory_usage', 'bandwidth_mbps',
                'latency_ms', 'packet_loss_percent', 'error_rate_percent']]
        y = df['issue_detected'].apply(lambda x: self.classes.index(x))
        
        X = self.scaler.fit_transform(X)
        self.model = self.build_model()
        
        self.model.fit(X, y, epochs=50, batch_size=32, validation_split=0.2)
        
        dump({
            'model': self.model,
            'scaler': self.scaler,
            'classes': self.classes
        }, 'quantum_inspired_network.joblib')
        
        print("Quantum-inspired (classical) model trained and saved!")

if __name__ == "__main__":
    monitor = QuantumInspiredMonitor()
    monitor.train('network_performance_dataset.csv')