#!/usr/bin/env python3
"""
Ingredient Analyzer Module
-------------------------
Analyzes product labels to identify ingredients.
This is a key feature of the Smart Kart for helping users check ingredients.
"""

import os
import time
import logging
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

# Optional imports for OCR/AI capabilities
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class IngredientAnalyzer:
    """
    Class for analyzing product images to identify ingredients.
    Uses OCR to read ingredient lists and NLP for ingredient identification.
    """
    
    def __init__(self, config, simulation_mode=False):
        """
        Initialize the ingredient analyzer.
        
        Args:
            config: Configuration object
            simulation_mode: If True, operate in simulation mode
        """
        self.config = config
        self.simulation_mode = simulation_mode
        
        # Feature settings
        self.enabled = config.get('features.ingredient_verification.enabled', True)
        self.confidence_threshold = config.get('features.ingredient_verification.confidence_threshold', 0.7)
        
        # Path settings
        self.models_path = Path(config.get('paths.models', 'models'))
        self.data_path = Path(config.get('paths.data', 'data'))
        
        # Initialize OCR and NLP if available
        self.ocr_engine = None
        self.nlp_engine = None
        
        # Store common allergens and ingredients of interest
        self.allergens = [
            "peanut", "tree nut", "milk", "egg", "wheat", "soy", "fish", 
            "shellfish", "dairy", "gluten", "lactose", "nuts"
        ]
        
        # Ingredient database (for simulations or augmentation)
        self.ingredient_db = {}
        
        if self.enabled and not self.simulation_mode:
            self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize OCR and NLP engines if available."""
        if TESSERACT_AVAILABLE:
            try:
                # Initialize Tesseract for OCR
                # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # May need adjustment
                test_string = pytesseract.get_tesseract_version()
                self.ocr_engine = pytesseract
                logger.info(f"Tesseract OCR initialized (version: {test_string})")
            except Exception as e:
                logger.error(f"Failed to initialize Tesseract OCR: {e}")
                self.ocr_engine = None
        
        if TRANSFORMERS_AVAILABLE:
            try:
                # Initialize NLP pipeline for named entity recognition
                model_path = os.path.join(self.models_path, "ner-ingredients")
                
                # Check if model exists locally, otherwise use remote
                if os.path.exists(model_path):
                    self.nlp_engine = pipeline("ner", model=model_path)
                else:
                    # Use a default model from Hugging Face (would need to be ingredient-specific in reality)
                    self.nlp_engine = pipeline("ner")
                
                logger.info("NLP engine initialized for ingredient detection")
            except Exception as e:
                logger.error(f"Failed to initialize NLP engine: {e}")
                self.nlp_engine = None
    
    def analyze_image(self, image_path):
        """
        Analyze an image to extract ingredients.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with extracted text and identified ingredients
        """
        if self.simulation_mode:
            logger.info("Simulation mode: Using dummy ingredient analysis")
            return self._simulate_analysis(image_path)
        
        if not self.ocr_engine:
            logger.warning("OCR engine not available. Cannot analyze image.")
            return {
                "success": False,
                "error": "OCR engine not available",
                "text": "",
                "ingredients": []
            }
        
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to load image from {image_path}")
                return {
                    "success": False,
                    "error": "Failed to load image",
                    "text": "",
                    "ingredients": []
                }
            
            # Preprocess image for better OCR
            preprocessed = self._preprocess_image(image)
            
            # Perform OCR
            text = self.ocr_engine.image_to_string(preprocessed)
            
            # Extract ingredients from text
            ingredients = self._extract_ingredients(text)
            
            return {
                "success": True,
                "text": text,
                "ingredients": ingredients
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "ingredients": []
            }
    
    def _preprocess_image(self, image):
        """
        Preprocess image for better OCR results.
        
        Args:
            image: OpenCV image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get black and white image
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Apply some noise reduction
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        return denoised
    
    def _extract_ingredients(self, text):
        """
        Extract ingredients from text.
        
        Args:
            text: Text extracted from image
            
        Returns:
            List of identified ingredients
        """
        # Basic implementation: Find section that mentions "ingredients"
        ingredients = []
        
        if not text:
            return ingredients
            
        # Convert to lowercase for easier matching
        text_lower = text.lower()
        
        # Check if we can find an "ingredients" section
        ingredients_idx = text_lower.find("ingredients")
        if ingredients_idx >= 0:
            # Extract text after "ingredients" and before next section
            section_end = text.find("\n\n", ingredients_idx)
            if section_end < 0:
                section_end = len(text)
            
            ingredients_text = text[ingredients_idx:section_end]
            
            # Split by commas, semicolons, or newlines
            for separator in [",", ";", "\n"]:
                if separator in ingredients_text:
                    raw_ingredients = [i.strip() for i in ingredients_text.split(separator)]
                    ingredients = [i for i in raw_ingredients if i and len(i) > 2]
                    break
        
        # If we couldn't extract ingredients or if we have NLP engine
        if not ingredients and self.nlp_engine:
            try:
                # Use NLP to identify potential ingredients
                entities = self.nlp_engine(text)
                
                # Filter entities that might be ingredients
                # This would need a more sophisticated approach in a real system
                ingredients = [e["word"] for e in entities 
                              if e["score"] > self.confidence_threshold]
                
            except Exception as e:
                logger.error(f"Error in NLP ingredient extraction: {e}")
        
        # If all else fails, at least check for common allergens
        if not ingredients:
            ingredients = [a for a in self.allergens if a in text_lower]
        
        return ingredients
    
    def check_for_ingredient(self, text, target_ingredient):
        """
        Check if a specific ingredient is mentioned in text.
        
        Args:
            text: Text to search in
            target_ingredient: Ingredient to look for
            
        Returns:
            True if ingredient found, False otherwise
        """
        if not text:
            return False
            
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        target_lower = target_ingredient.lower()
        
        # Direct match
        if target_lower in text_lower:
            return True
            
        # Check for common variations or abbreviations (would be more extensive in a real system)
        variations = {
            "msg": ["monosodium glutamate"],
            "peanut": ["ground nut", "arachis"],
            "gluten": ["wheat", "barley", "rye"],
            "milk": ["dairy", "lactose", "whey", "casein"]
        }
        
        if target_lower in variations:
            for var in variations[target_lower]:
                if var in text_lower:
                    return True
        
        return False
    
    def _simulate_analysis(self, image_path):
        """
        Simulate image analysis for testing.
        
        Args:
            image_path: Path to image (just used for logging)
            
        Returns:
            Simulated analysis results
        """
        # Extract filename without extension to use as key
        filename = os.path.basename(image_path)
        name, _ = os.path.splitext(filename)
        
        # Simulate different products based on filename or path
        if "milk" in name.lower():
            return {
                "success": True,
                "text": "Ingredients: Milk, Vitamin D, Vitamin A Palmitate, Salt.",
                "ingredients": ["Milk", "Vitamin D", "Vitamin A Palmitate", "Salt"]
            }
        elif "bread" in name.lower():
            return {
                "success": True,
                "text": "Ingredients: Wheat Flour, Water, Yeast, Salt, Sugar, Vegetable Oil.",
                "ingredients": ["Wheat Flour", "Water", "Yeast", "Salt", "Sugar", "Vegetable Oil"]
            }
        elif "peanut" in name.lower() or "nuts" in name.lower():
            return {
                "success": True,
                "text": "Ingredients: Peanuts, Sugar, Salt, Hydrogenated Vegetable Oil.",
                "ingredients": ["Peanuts", "Sugar", "Salt", "Hydrogenated Vegetable Oil"]
            }
        else:
            # Generic response
            return {
                "success": True,
                "text": "Ingredients: Various ingredients that make up this product.",
                "ingredients": ["Water", "Sugar", "Natural Flavors", "Citric Acid"]
            }
    
    def verify_ingredients(self, product_id, target_ingredients):
        """
        Verify if specific ingredients exist in a product.
        
        Args:
            product_id: Identifier for the product
            target_ingredients: List of ingredients to verify
            
        Returns:
            Dictionary with results for each ingredient
        """
        results = {}
        
        # In simulation mode, use dummy data
        if self.simulation_mode:
            # Dummy product database with known ingredients
            dummy_products = {
                "9780201379624": {  # Design Patterns book (no ingredients)
                    "ingredients": []
                },
                "7501234567890": {  # Apple
                    "ingredients": ["Apple"]
                },
                "5901234123457": {  # Milk
                    "ingredients": ["Milk", "Vitamin D", "Calcium"]
                },
                "4005900123451": {  # Peanut Butter
                    "ingredients": ["Peanuts", "Sugar", "Salt", "Hydrogenated Vegetable Oil"]
                },
                "0614141123456": {  # Bread
                    "ingredients": ["Wheat Flour", "Water", "Yeast", "Salt", "Sugar"]
                }
            }
            
            # Get product ingredients
            product = dummy_products.get(product_id, {"ingredients": []})
            product_ingredients = [i.lower() for i in product["ingredients"]]
            
            # Check each target ingredient
            for ingredient in target_ingredients:
                ingredient_lower = ingredient.lower()
                results[ingredient] = ingredient_lower in product_ingredients
                
            return {
                "success": True,
                "product_id": product_id,
                "ingredients": product["ingredients"],
                "results": results
            }
            
        # For real implementation, we would need to:
        # 1. Retrieve product image (from database or camera)
        # 2. Analyze image to extract ingredients
        # 3. Check if target ingredients are in the extracted list
        
        # This is a placeholder for the real implementation
        logger.warning("Real ingredient verification not implemented yet")
        return {
            "success": False,
            "error": "Real ingredient verification not implemented yet",
            "product_id": product_id,
            "results": {ingredient: False for ingredient in target_ingredients}
        }
    
    def register_product_ingredients(self, product_id, ingredients):
        """
        Register ingredients for a product (for simulation or caching).
        
        Args:
            product_id: Identifier for the product
            ingredients: List of ingredients
            
        Returns:
            True if successful
        """
        self.ingredient_db[product_id] = ingredients
        logger.info(f"Registered ingredients for product {product_id}")
        return True


# Example usage
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Simple config for testing
    from src.utils.config import Config
    config = Config()
    
    # Create ingredient analyzer in simulation mode
    analyzer = IngredientAnalyzer(config, simulation_mode=True)
    
    # Simulate some ingredient verifications
    milk_check = analyzer.verify_ingredients("5901234123457", ["milk", "lactose"])
    peanut_check = analyzer.verify_ingredients("4005900123451", ["peanuts", "gluten"])
    
    print(f"Milk product contains milk? {milk_check['results'].get('milk', False)}")
    print(f"Peanut butter contains peanuts? {peanut_check['results'].get('peanuts', False)}")
    print(f"Peanut butter contains gluten? {peanut_check['results'].get('gluten', False)}") 