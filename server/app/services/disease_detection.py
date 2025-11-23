import os
import base64
import numpy as np
from PIL import Image
import io
from typing import Dict, List, Optional
import torch
from torchvision import transforms
import pandas as pd
from app.core.config import settings

class DiseaseDetectionService:
    def __init__(self):
        self.model_dir = settings.MODEL_DIR
        self.model = None
        self.disease_info = None
        self.supplement_info = None
        self.load_model()
        self.load_data()
    
    def load_model(self):
        """Load the PyTorch disease detection model."""
        print(f"Loading model from directory: {self.model_dir}")
        
        # Look for PyTorch model file
        model_files = []
        if os.path.exists(self.model_dir):
            for file in os.listdir(self.model_dir):
                if file.endswith('.pt'):
                    model_files.append(file)
        
        if not model_files:
            print("No PyTorch model files found in the models directory")
            return
        
        # Use the first available model
        model_file = model_files[0]
        model_path = os.path.join(self.model_dir, model_file)
        print(f"Loading model: {model_path}")
        
        try:
            # Import the CNN class
            import sys
            sys.path.append(self.model_dir)
            from CNN import CNN
            
            # Load PyTorch model
            self.model = CNN(39)  # 39 classes
            self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
            self.model.eval()
            print(f"Successfully loaded model: {model_file}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def load_data(self):
        """Load disease and supplement information from CSV files."""
        try:
            disease_info_path = os.path.join(self.model_dir, 'disease_info.csv')
            supplement_info_path = os.path.join(self.model_dir, 'supplement_info.csv')
            
            if os.path.exists(disease_info_path):
                self.disease_info = pd.read_csv(disease_info_path, encoding='cp1252')
                print(f"Loaded disease info: {len(self.disease_info)} diseases")
            else:
                print("Disease info CSV not found")
                
            if os.path.exists(supplement_info_path):
                self.supplement_info = pd.read_csv(supplement_info_path, encoding='cp1252')
                print(f"Loaded supplement info: {len(self.supplement_info)} supplements")
            else:
                print("Supplement info CSV not found")
                
        except Exception as e:
            print(f"Error loading data files: {e}")
    
    def preprocess_image(self, image_base64: str) -> torch.Tensor:
        """Preprocess image for PyTorch model input."""
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to 224x224 (required by the model)
            image = image.resize((224, 224))
            
            # Convert to tensor using torchvision transforms
            transform = transforms.ToTensor()
            input_data = transform(image)
            input_data = input_data.view((-1, 3, 224, 224))
            
            return input_data
        except Exception as e:
            raise ValueError(f"Error preprocessing image: {e}")
    
    def predict_disease(self, image_base64: str) -> Dict:
        """Predict disease from image."""
        if self.model is None:
            print("ERROR: No model available for disease detection")
            raise ValueError("No model available for disease detection")
        
        try:
            print("Starting disease prediction...")
            
            # Preprocess image
            processed_image = self.preprocess_image(image_base64)
            print(f"Image preprocessed, shape: {processed_image.shape}")
            
            # Make prediction
            with torch.no_grad():
                output = self.model(processed_image)
                print(f"Model output shape: {output.shape}")
                print(f"Raw output range: [{output.min().item():.4f}, {output.max().item():.4f}]")
                
                # Apply softmax to convert logits to probabilities
                probabilities = torch.softmax(output, dim=1)
                probabilities = probabilities.detach().numpy()
                print(f"Probabilities shape: {probabilities.shape}")
                print(f"Probabilities sum: {probabilities[0].sum():.6f}")
            
            # Get class with highest probability
            class_index = np.argmax(probabilities[0])
            confidence = float(probabilities[0][class_index])
            
            # Debug information
            print(f"Raw probabilities shape: {probabilities.shape}")
            print(f"Top 5 probabilities: {np.sort(probabilities[0])[-5:][::-1]}")
            print(f"Selected class index: {class_index}")
            print(f"Confidence for selected class: {confidence:.6f}")
            
            # Check for model overfitting indicators
            probability_std = np.std(probabilities[0])
            second_highest = np.sort(probabilities[0])[-2]
            
            print(f"Probability distribution spread: {probability_std:.6f}")
            print(f"Second highest probability: {second_highest:.6f}")
            
            # Model quality checks
            is_overfitted = confidence > 0.99 and probability_std < 0.2
            is_low_confidence = confidence < 0.3
            is_uniform_distribution = probability_std < 0.1
            
            if is_overfitted:
                print("WARNING: Model appears overfitted - very high confidence with low distribution spread")
                # Apply more aggressive confidence adjustment
                confidence = min(confidence, 0.75)
                print(f"Adjusted confidence due to overfitting: {confidence:.6f}")
            elif is_low_confidence:
                print("WARNING: Very low confidence - model uncertain about prediction")
                # Don't adjust low confidence, it might be legitimate uncertainty
            elif is_uniform_distribution:
                print("WARNING: Uniform probability distribution - model may not be working properly")
                confidence = 0.5  # Set to moderate confidence
                print(f"Set confidence to moderate due to uniform distribution: {confidence:.6f}")
            
            # Ensure confidence is between 0 and 1
            confidence = min(max(confidence, 0.0), 1.0)
            
            print(f"Final confidence: {confidence:.6f}")
            
            # Map class index to disease name
            disease_name = self.get_disease_name(class_index)
            print(f"Disease name: {disease_name}")
            
            # Check if this is a background without leaves (not a disease)
            if "background without leaves" in disease_name.lower():
                print("Detected background without leaves - not a disease")
                return {
                    "disease_name": "Background Without Leaves",
                    "confidence_score": confidence,
                    "severity": "none",
                    "symptoms": ["There is no leaf in the given image"],
                    "treatment": ["Please reupload image with leaf"],
                    "prevention": [
                        "Use certified disease-free seeds",
                        "Practice crop rotation", 
                        "Maintain proper plant spacing",
                        "Monitor plants regularly"
                    ],
                    "description": "No plant or leaf detected in the uploaded image. Please upload an image containing a plant leaf for disease analysis."
                }
            
            # Additional validation for suspicious predictions
            if confidence < 0.4:
                print("WARNING: Low confidence prediction - consider manual verification")
                # For low confidence, suggest manual verification
                disease_name = f"{disease_name} (Low Confidence - Manual Verification Recommended)"
            
            # Determine severity based on confidence
            severity = self.determine_severity(confidence)
            print(f"Severity: {severity}")
            
            # Get treatment and prevention recommendations
            treatment = self.get_treatment_recommendations(disease_name)
            prevention = self.get_prevention_recommendations(disease_name)
            symptoms = self.get_disease_symptoms(disease_name)
            
            result = {
                "disease_name": disease_name,
                "confidence_score": confidence,
                "severity": severity,
                "symptoms": symptoms,
                "treatment": treatment,
                "prevention": prevention
            }
            
            print(f"Final result: {result}")
            return result
            
        except Exception as e:
            print(f"ERROR during disease prediction: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Error during disease prediction: {e}")
    
    def get_disease_name(self, class_index: int) -> str:
        """Map class index to disease name using CSV data."""
        if self.disease_info is not None and class_index < len(self.disease_info):
            return self.disease_info.iloc[class_index]['disease_name']
        else:
            # Fallback to hardcoded mappings if CSV is not available
            disease_mappings = {
                0: 'Apple : Scab', 1: 'Apple : Black rot', 2: 'Apple : Cedar apple rust', 3: 'Apple : healthy',
                4: 'Background without leaves', 5: 'Blueberry : healthy', 6: 'Cherry : Powdery mildew', 7: 'Cherry : healthy',
                8: 'Corn : Cercospora leaf spot Gray leaf spot', 9: 'Corn : Common rust', 10: 'Corn : Northern Leaf Blight', 11: 'Corn : healthy',
                12: 'Grape : Black rot', 13: 'Grape : Esca (Black Measles)', 14: 'Grape : Leaf blight (Isariopsis Leaf Spot)', 15: 'Grape : healthy',
                16: 'Orange : Haunglongbing (Citrus greening)', 17: 'Peach : Bacterial spot', 18: 'Peach : healthy', 19: 'Pepper, bell : Bacterial spot',
                20: 'Pepper, bell : healthy', 21: 'Potato : Early blight', 22: 'Potato : Late blight', 23: 'Potato : healthy',
                24: 'Raspberry : healthy', 25: 'Soybean : healthy', 26: 'Squash : Powdery mildew', 27: 'Strawberry : Leaf scorch',
                28: 'Strawberry : healthy', 29: 'Tomato : Bacterial spot', 30: 'Tomato : Early blight', 31: 'Tomato : Late blight',
                32: 'Tomato : Leaf Mold', 33: 'Tomato : Septoria leaf spot', 34: 'Tomato : Spider mites Two-spotted spider mite',
                35: 'Tomato : Target Spot', 36: 'Tomato : Tomato Yellow Leaf Curl Virus', 37: 'Tomato : Tomato mosaic virus', 38: 'Tomato : healthy'
            }
            return disease_mappings.get(class_index, f"Unknown Disease (Class {class_index})")
    
    def determine_severity(self, confidence: float) -> str:
        """Determine disease severity based on confidence score."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def get_treatment_recommendations(self, disease_name: str) -> List[str]:
        """Get treatment recommendations for a specific disease."""
        # Check if this is a healthy crop
        if "healthy" in disease_name.lower():
            return self.get_healthy_crop_recommendations(disease_name)
        
        if self.disease_info is not None:
            # Find the disease in the CSV
            disease_row = self.disease_info[self.disease_info['disease_name'] == disease_name]
            if not disease_row.empty:
                possible_steps = disease_row.iloc[0]['Possible Steps']
                if pd.notna(possible_steps):
                    # Split by periods and clean up
                    steps = [step.strip() for step in str(possible_steps).split('.') if step.strip()]
                    return steps[:5]  # Return first 5 steps
        
        # Fallback to generic recommendations
        treatments = {
            # Tomato diseases
            "Bacterial Spot": [
                "Apply copper-based fungicides",
                "Remove infected plant parts",
                "Improve air circulation",
                "Avoid overhead watering"
            ],
            "Early Blight": [
                "Apply fungicides containing chlorothalonil or mancozeb",
                "Remove infected leaves",
                "Ensure proper spacing between plants",
                "Water at soil level"
            ],
            "Late Blight": [
                "Apply fungicides immediately",
                "Remove and destroy infected plants",
                "Improve drainage",
                "Avoid working in wet conditions"
            ],
            "Leaf Mold": [
                "Apply fungicides with copper or sulfur",
                "Improve air circulation",
                "Reduce humidity levels",
                "Remove infected leaves"
            ],
            "Septoria Leaf Spot": [
                "Apply fungicides with copper or chlorothalonil",
                "Remove infected plant debris",
                "Avoid overhead watering",
                "Improve air circulation"
            ],
            "Spider Mites": [
                "Apply miticides or insecticidal soap",
                "Increase humidity levels",
                "Remove heavily infested leaves",
                "Use predatory mites"
            ],
            "Target Spot": [
                "Apply fungicides with copper or mancozeb",
                "Remove infected plant parts",
                "Improve air circulation",
                "Avoid overhead watering"
            ],
            "Yellow Leaf Curl Virus": [
                "Control whitefly populations",
                "Remove infected plants",
                "Use resistant varieties",
                "Apply systemic insecticides"
            ],
            "Mosaic Virus": [
                "Remove infected plants immediately",
                "Control aphid populations",
                "Use virus-free seeds",
                "Disinfect tools between plants"
            ],
            
            # Paddy diseases
            "Brown Spot": [
                "Apply fungicides with propiconazole",
                "Remove infected plant debris",
                "Improve field drainage",
                "Use resistant varieties"
            ],
            "Hispa": [
                "Apply insecticides like imidacloprid",
                "Remove and destroy infected leaves",
                "Maintain proper field hygiene",
                "Use resistant varieties"
            ],
            "Leaf Blast": [
                "Apply fungicides with tricyclazole",
                "Improve field drainage",
                "Avoid excessive nitrogen",
                "Use resistant varieties"
            ],
            
            # Sugarcane diseases
            "Mosaic": [
                "Remove infected plants",
                "Control aphid vectors",
                "Use virus-free planting material",
                "Apply systemic insecticides"
            ],
            "Red Rot": [
                "Remove infected stalks",
                "Improve field drainage",
                "Use resistant varieties",
                "Apply fungicides with carbendazim"
            ],
            "Rust": [
                "Apply fungicides with propiconazole",
                "Remove infected leaves",
                "Improve air circulation",
                "Use resistant varieties"
            ],
            
            # Mango diseases
            "Anthracnose": [
                "Apply fungicides with copper or sulfur",
                "Remove infected plant parts",
                "Improve air circulation",
                "Avoid overhead watering"
            ],
            "Bacterial Black Spot": [
                "Apply copper-based fungicides",
                "Remove infected plant parts",
                "Improve air circulation",
                "Use resistant varieties"
            ],
            "Powdery Mildew": [
                "Apply fungicides with sulfur or potassium bicarbonate",
                "Improve air circulation",
                "Reduce humidity",
                "Remove infected plant parts"
            ],
            
            # Banana diseases
            "Black Sigatoka": [
                "Apply fungicides with propiconazole",
                "Remove infected leaves",
                "Improve air circulation",
                "Use resistant varieties"
            ],
            "Panama Disease": [
                "Remove infected plants immediately",
                "Improve soil drainage",
                "Use resistant varieties",
                "Practice crop rotation"
            ],
            
            # Chilli diseases
            "Leaf Curl": [
                "Control whitefly populations",
                "Remove infected plants",
                "Use resistant varieties",
                "Apply systemic insecticides"
            ],
            
            # Corn diseases
            "Common Rust": [
                "Apply fungicides with propiconazole",
                "Remove infected plant debris",
                "Use resistant varieties",
                "Improve air circulation"
            ],
            "Gray Leaf Spot": [
                "Apply fungicides with azoxystrobin",
                "Remove infected plant debris",
                "Use resistant varieties",
                "Improve air circulation"
            ],
            "Northern Leaf Blight": [
                "Apply fungicides with azoxystrobin",
                "Remove infected plant debris",
                "Use resistant varieties",
                "Improve air circulation"
            ],
            
            # Cotton diseases
            "Bacterial Blight": [
                "Apply copper-based fungicides",
                "Remove infected plant parts",
                "Improve air circulation",
                "Use resistant varieties"
            ],
            
            # Grape diseases
            "Black Rot": [
                "Apply fungicides with copper or sulfur",
                "Remove infected plant parts",
                "Improve air circulation",
                "Avoid overhead watering"
            ],
            "Esca": [
                "Remove infected wood",
                "Improve air circulation",
                "Apply fungicides to wounds",
                "Use resistant varieties"
            ],
            "Leaf Blight": [
                "Apply fungicides with copper or sulfur",
                "Remove infected leaves",
                "Improve air circulation",
                "Avoid overhead watering"
            ],
            
            # Orange diseases
            "Black Spot": [
                "Apply fungicides with copper or sulfur",
                "Remove infected plant parts",
                "Improve air circulation",
                "Use resistant varieties"
            ],
            "Canker": [
                "Apply copper-based fungicides",
                "Remove infected plant parts",
                "Improve air circulation",
                "Use resistant varieties"
            ],
            "Greening": [
                "Remove infected trees immediately",
                "Control psyllid vectors",
                "Use disease-free planting material",
                "Apply systemic insecticides"
            ],
            
            # Cauliflower diseases
            "Bacterial Soft Rot": [
                "Apply copper-based fungicides",
                "Remove infected plant parts",
                "Improve air circulation",
                "Avoid overhead watering"
            ],
            "Black Rot": [
                "Apply copper-based fungicides",
                "Remove infected plant parts",
                "Improve air circulation",
                "Use resistant varieties"
            ]
        }
        
        return treatments.get(disease_name, [
            "Consult with agricultural expert",
            "Apply appropriate fungicide",
            "Remove infected plant parts",
            "Improve growing conditions"
        ])
    
    def get_prevention_recommendations(self, disease_name: str) -> List[str]:
        """Get prevention recommendations for a specific disease."""
        # Check if this is a healthy crop
        if "healthy" in disease_name.lower():
            return self.get_healthy_crop_prevention(disease_name)
        
        preventions = {
            # Tomato diseases
            "Bacterial Spot": [
                "Use disease-free seeds",
                "Practice crop rotation",
                "Maintain proper plant spacing",
                "Avoid overhead irrigation"
            ],
            "Early Blight": [
                "Plant resistant varieties",
                "Practice crop rotation",
                "Maintain good air circulation",
                "Remove plant debris"
            ],
            "Late Blight": [
                "Plant resistant varieties",
                "Avoid overhead watering",
                "Ensure good drainage",
                "Monitor weather conditions"
            ],
            "Leaf Mold": [
                "Use resistant varieties",
                "Improve air circulation",
                "Avoid overhead watering",
                "Remove plant debris"
            ],
            "Septoria Leaf Spot": [
                "Use disease-free seeds",
                "Practice crop rotation",
                "Remove plant debris",
                "Avoid overhead watering"
            ],
            "Spider Mites": [
                "Maintain adequate humidity",
                "Remove weeds and debris",
                "Use beneficial insects",
                "Avoid over-fertilization"
            ],
            "Target Spot": [
                "Use resistant varieties",
                "Practice crop rotation",
                "Remove plant debris",
                "Avoid overhead watering"
            ],
            "Yellow Leaf Curl Virus": [
                "Use resistant varieties",
                "Control whitefly populations",
                "Use virus-free seeds",
                "Remove weeds"
            ],
            "Mosaic Virus": [
                "Use virus-free seeds",
                "Control aphid populations",
                "Remove weeds",
                "Disinfect tools"
            ],
            
            # Paddy diseases
            "Brown Spot": [
                "Use resistant varieties",
                "Practice crop rotation",
                "Maintain proper field drainage",
                "Avoid excessive nitrogen"
            ],
            "Hispa": [
                "Use resistant varieties",
                "Maintain field hygiene",
                "Remove infected plant debris",
                "Practice crop rotation"
            ],
            "Leaf Blast": [
                "Use resistant varieties",
                "Improve field drainage",
                "Avoid excessive nitrogen",
                "Practice crop rotation"
            ],
            
            # Sugarcane diseases
            "Mosaic": [
                "Use virus-free planting material",
                "Control aphid vectors",
                "Remove infected plants",
                "Practice crop rotation"
            ],
            "Red Rot": [
                "Use resistant varieties",
                "Improve field drainage",
                "Practice crop rotation",
                "Remove infected stalks"
            ],
            "Rust": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant debris",
                "Practice crop rotation"
            ],
            
            # Mango diseases
            "Anthracnose": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant parts",
                "Avoid overhead watering"
            ],
            "Bacterial Black Spot": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant parts",
                "Practice proper pruning"
            ],
            "Powdery Mildew": [
                "Use resistant varieties",
                "Improve air circulation",
                "Reduce humidity",
                "Remove infected plant parts"
            ],
            
            # Banana diseases
            "Black Sigatoka": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected leaves",
                "Practice proper spacing"
            ],
            "Panama Disease": [
                "Use resistant varieties",
                "Improve soil drainage",
                "Practice crop rotation",
                "Use disease-free planting material"
            ],
            
            # Chilli diseases
            "Leaf Curl": [
                "Use resistant varieties",
                "Control whitefly populations",
                "Use virus-free seeds",
                "Remove weeds"
            ],
            
            # Corn diseases
            "Common Rust": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant debris",
                "Practice crop rotation"
            ],
            "Gray Leaf Spot": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant debris",
                "Practice crop rotation"
            ],
            "Northern Leaf Blight": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant debris",
                "Practice crop rotation"
            ],
            
            # Cotton diseases
            "Bacterial Blight": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant parts",
                "Practice crop rotation"
            ],
            
            # Grape diseases
            "Black Rot": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant parts",
                "Avoid overhead watering"
            ],
            "Esca": [
                "Use resistant varieties",
                "Improve air circulation",
                "Practice proper pruning",
                "Remove infected wood"
            ],
            "Leaf Blight": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected leaves",
                "Avoid overhead watering"
            ],
            
            # Orange diseases
            "Black Spot": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant parts",
                "Practice proper pruning"
            ],
            "Canker": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant parts",
                "Practice proper pruning"
            ],
            "Greening": [
                "Use disease-free planting material",
                "Control psyllid vectors",
                "Remove infected trees",
                "Practice proper field hygiene"
            ],
            
            # Cauliflower diseases
            "Bacterial Soft Rot": [
                "Use disease-free seeds",
                "Improve air circulation",
                "Remove infected plant parts",
                "Avoid overhead watering"
            ],
            "Black Rot": [
                "Use resistant varieties",
                "Improve air circulation",
                "Remove infected plant parts",
                "Practice crop rotation"
            ]
        }
        
        return preventions.get(disease_name, [
            "Use certified disease-free seeds",
            "Practice crop rotation",
            "Maintain proper plant spacing",
            "Monitor plants regularly"
        ])
    
    def get_disease_symptoms(self, disease_name: str) -> List[str]:
        """Get symptoms for a specific disease."""
        # Check if this is a healthy crop
        if "healthy" in disease_name.lower():
            return self.get_healthy_crop_symptoms(disease_name)
        
        if self.disease_info is not None:
            # Find the disease in the CSV
            disease_row = self.disease_info[self.disease_info['disease_name'] == disease_name]
            if not disease_row.empty:
                description = disease_row.iloc[0]['description']
                if pd.notna(description):
                    # Extract symptoms from description (first few sentences)
                    sentences = [s.strip() for s in str(description).split('.') if s.strip()]
                    return sentences[:4]  # Return first 4 sentences as symptoms
        
        # Fallback to generic symptoms
        symptoms = {
            # Tomato diseases
            "Bacterial Spot": [
                "Small, dark spots on leaves",
                "Yellowing around spots",
                "Spots may have a water-soaked appearance",
                "Leaves may drop prematurely"
            ],
            "Early Blight": [
                "Dark brown spots with concentric rings",
                "Yellowing of leaves",
                "Spots on stems and fruits",
                "Defoliation in severe cases"
            ],
            "Late Blight": [
                "Large, irregular brown spots",
                "White mold on underside of leaves",
                "Rapid plant death",
                "Dark lesions on stems"
            ],
            "Leaf Mold": [
                "Yellow spots on upper leaf surface",
                "Grayish mold on underside of leaves",
                "Leaves may curl and drop",
                "Poor fruit development"
            ],
            "Septoria Leaf Spot": [
                "Small, circular spots with dark borders",
                "Yellowing of affected leaves",
                "Spots may coalesce",
                "Defoliation in severe cases"
            ],
            "Spider Mites": [
                "Fine webbing on leaves",
                "Yellow or brown stippling",
                "Leaves may appear dusty",
                "Stunted growth"
            ],
            "Target Spot": [
                "Circular spots with concentric rings",
                "Yellowing around spots",
                "Spots may have dark centers",
                "Leaves may drop"
            ],
            "Yellow Leaf Curl Virus": [
                "Yellowing and curling of leaves",
                "Stunted plant growth",
                "Reduced fruit production",
                "Upward curling of leaf edges"
            ],
            "Mosaic Virus": [
                "Mottled yellow and green leaves",
                "Distorted leaf growth",
                "Stunted plant development",
                "Reduced fruit yield"
            ],
            
            # Paddy diseases
            "Brown Spot": [
                "Brown, oval spots on leaves",
                "Yellowing of affected areas",
                "Spots may have dark borders",
                "Reduced grain quality"
            ],
            "Hispa": [
                "White streaks on leaves",
                "Scraping marks on leaf surface",
                "Reduced photosynthesis",
                "Stunted plant growth"
            ],
            "Leaf Blast": [
                "Spindle-shaped spots on leaves",
                "Gray centers with dark borders",
                "Rapid leaf death",
                "Reduced grain production"
            ],
            
            # Sugarcane diseases
            "Mosaic": [
                "Mottled yellow and green leaves",
                "Stunted growth",
                "Reduced sugar content",
                "Distorted leaf development"
            ],
            "Red Rot": [
                "Red discoloration in stalks",
                "Hollow stalks with red tissue",
                "Stunted growth",
                "Poor sugar quality"
            ],
            "Rust": [
                "Orange to brown pustules on leaves",
                "Yellowing of affected areas",
                "Premature leaf drop",
                "Reduced sugar content"
            ],
            
            # Mango diseases
            "Anthracnose": [
                "Dark, sunken spots on fruits",
                "Black spots on leaves",
                "Flower blight",
                "Fruit rot"
            ],
            "Bacterial Black Spot": [
                "Black, raised spots on fruits",
                "Cracked fruit surface",
                "Reduced fruit quality",
                "Leaf spots"
            ],
            "Powdery Mildew": [
                "White, powdery coating on leaves",
                "Distorted leaf growth",
                "Reduced fruit set",
                "Stunted shoot growth"
            ],
            
            # Banana diseases
            "Black Sigatoka": [
                "Dark streaks on leaves",
                "Yellowing of leaf margins",
                "Premature leaf death",
                "Reduced fruit production"
            ],
            "Panama Disease": [
                "Yellowing and wilting of leaves",
                "Brown discoloration in stems",
                "Plant death",
                "No fruit production"
            ],
            
            # Chilli diseases
            "Leaf Curl": [
                "Upward curling of leaves",
                "Yellowing of leaves",
                "Stunted plant growth",
                "Reduced fruit production"
            ],
            
            # Corn diseases
            "Common Rust": [
                "Orange to brown pustules on leaves",
                "Yellowing of affected areas",
                "Premature leaf death",
                "Reduced grain yield"
            ],
            "Gray Leaf Spot": [
                "Gray, rectangular spots on leaves",
                "Yellowing around spots",
                "Premature leaf death",
                "Reduced grain quality"
            ],
            "Northern Leaf Blight": [
                "Large, elliptical spots on leaves",
                "Gray centers with dark borders",
                "Premature leaf death",
                "Reduced grain yield"
            ],
            
            # Cotton diseases
            "Bacterial Blight": [
                "Water-soaked spots on leaves",
                "Black spots on bolls",
                "Stunted plant growth",
                "Reduced fiber quality"
            ],
            
            # Grape diseases
            "Black Rot": [
                "Dark, circular spots on leaves",
                "Black spots on fruits",
                "Fruit rot and shriveling",
                "Reduced grape quality"
            ],
            "Esca": [
                "Yellowing and browning of leaves",
                "Wood decay in vines",
                "Reduced fruit production",
                "Vine death in severe cases"
            ],
            "Leaf Blight": [
                "Brown spots on leaves",
                "Yellowing of affected areas",
                "Premature leaf drop",
                "Reduced grape yield"
            ],
            
            # Orange diseases
            "Black Spot": [
                "Dark spots on fruits and leaves",
                "Fruit drop",
                "Reduced fruit quality",
                "Leaf yellowing"
            ],
            "Canker": [
                "Raised, corky lesions on fruits",
                "Yellow halos around spots",
                "Fruit drop",
                "Reduced fruit quality"
            ],
            "Greening": [
                "Yellowing of leaves",
                "Small, misshapen fruits",
                "Bitter taste in fruits",
                "Tree decline"
            ],
            
            # Cauliflower diseases
            "Bacterial Soft Rot": [
                "Water-soaked spots on heads",
                "Foul odor",
                "Soft, mushy tissue",
                "Head rot"
            ],
            "Black Rot": [
                "Yellow, V-shaped lesions on leaves",
                "Black veins in leaves",
                "Head rot",
                "Stunted plant growth"
            ]
        }
        
        return symptoms.get(disease_name, [
            "Abnormal leaf discoloration",
            "Spots or lesions on leaves",
            "Stunted growth",
            "Premature leaf drop"
        ])
    
    def get_healthy_crop_recommendations(self, disease_name: str) -> List[str]:
        """Get recommendations for maintaining healthy crops."""
        # Extract crop type from disease name (e.g., "Blueberry : healthy" -> "Blueberry")
        crop_type = disease_name.split(" : ")[0] if " : " in disease_name else "Plant"
        
        healthy_recommendations = {
            "Apple": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Blueberry": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Cherry": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Corn": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Grape": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Orange": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Peach": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Pepper": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Potato": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Raspberry": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Soybean": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Squash": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Strawberry": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ],
            "Tomato": [
                "Maintain consistent temperature between 18-25°C",
                "Ensure adequate sunlight exposure (6-8 hours daily)",
                "Monitor humidity levels (40-60% ideal)",
                "Provide proper air circulation around plants",
                "Protect from extreme weather conditions"
            ]
        }
        
        return healthy_recommendations.get(crop_type, [
            "Maintain consistent temperature between 18-25°C",
            "Ensure adequate sunlight exposure (6-8 hours daily)",
            "Monitor humidity levels (40-60% ideal)",
            "Provide proper air circulation around plants",
            "Protect from extreme weather conditions"
        ])
    
    def get_healthy_crop_prevention(self, disease_name: str) -> List[str]:
        """Get prevention recommendations for maintaining healthy crops."""
        # Extract crop type from disease name (e.g., "Blueberry : healthy" -> "Blueberry")
        crop_type = disease_name.split(" : ")[0] if " : " in disease_name else "Plant"
        
        healthy_prevention = {
            "Apple": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Blueberry": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Cherry": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Corn": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Grape": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Orange": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Peach": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Pepper": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Potato": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Raspberry": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Soybean": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Squash": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Strawberry": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ],
            "Tomato": [
                "Test soil pH regularly (6.0-7.0 optimal)",
                "Apply balanced NPK fertilizer as needed",
                "Add organic compost for soil health",
                "Ensure proper drainage to prevent waterlogging",
                "Monitor micronutrient levels (iron, zinc, magnesium)"
            ]
        }
        
        return healthy_prevention.get(crop_type, [
            "Test soil pH regularly (6.0-7.0 optimal)",
            "Apply balanced NPK fertilizer as needed",
            "Add organic compost for soil health",
            "Ensure proper drainage to prevent waterlogging",
            "Monitor micronutrient levels (iron, zinc, magnesium)"
        ])
    
    def get_healthy_crop_symptoms(self, disease_name: str) -> List[str]:
        """Get growth monitoring recommendations for healthy crops."""
        # Extract crop type from disease name (e.g., "Blueberry : healthy" -> "Blueberry")
        crop_type = disease_name.split(" : ")[0] if " : " in disease_name else "Plant"
        
        healthy_symptoms = {
            "Apple": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Blueberry": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Cherry": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Corn": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Grape": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Orange": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Peach": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Pepper": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Potato": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Raspberry": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Soybean": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Squash": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Strawberry": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ],
            "Tomato": [
                "Track growth patterns and development stages",
                "Monitor flowering and fruiting cycles",
                "Record yield data for future optimization",
                "Observe leaf color and texture changes",
                "Document any seasonal variations in growth"
            ]
        }
        
        return healthy_symptoms.get(crop_type, [
            "Track growth patterns and development stages",
            "Monitor flowering and fruiting cycles",
            "Record yield data for future optimization",
            "Observe leaf color and texture changes",
            "Document any seasonal variations in growth"
        ])

# Global instance
disease_detection_service = DiseaseDetectionService()
