"""JSON to Pydantic validation for LLM responses."""

from typing import Type, TypeVar, Dict, Any
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)

class JSONValidator:
    """Validate and parse JSON responses into Pydantic models."""
    
    @staticmethod
    def validate(json_data: Dict[str, Any], model_class: Type[T]) -> T:
        """
        Validate JSON data against a Pydantic model.
        
        Args:
            json_data: Dictionary from JSON response
            model_class: Target Pydantic model class
            
        Returns:
            Instantiated model object
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            return model_class(**json_data)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")
    
    @staticmethod
    def safe_validate(json_data: Dict[str, Any], model_class: Type[T], default: T = None) -> T:
        """
        Safely validate with fallback to default.
        
        Args:
            json_data: Dictionary from JSON response
            model_class: Target Pydantic model class
            default: Default value if validation fails
            
        Returns:
            Validated model or default
        """
        try:
            return JSONValidator.validate(json_data, model_class)
        except Exception:
            return default
