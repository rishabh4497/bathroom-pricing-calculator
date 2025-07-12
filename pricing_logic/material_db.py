import json
from pathlib import Path

class MaterialDB:
    def __init__(self, db_path: Path = None):
        if db_path is None:
            # Default path relative to this file
            base_path = Path(__file__).parent.parent
            db_path = base_path / 'data' / 'materials.json'
        
        if not db_path.exists():
            raise FileNotFoundError(f"Material database not found at {db_path}")
            
        with open(db_path, 'r') as f:
            self._data = json.load(f)

    def get_material_cost(self, category: str, item: str, quality: str = 'standard') -> float:
        """
        Retrieves the price of a specific material.
        
        Args:
            category (str): The category of the material (e.g., 'tiles').
            item (str): The specific item (e.g., 'ceramic').
            quality (str): The quality level ('budget', 'standard', 'premium').

        Returns:
            float: The price per unit of the material.
        """
        try:
            material = self._data[category][item]
            price_info = material['price_per_unit']
            
            if quality in price_info:
                return price_info[quality]
            # Fallback to standard if the specified quality is not available
            return price_info.get('standard', 0.0)
                
        except KeyError:
            # Handle cases where the material or category doesn't exist
            return 0.0

    def get_material_info(self, category: str, item: str) -> dict:
        """
        Retrieves all information for a specific material.
        
        Args:
            category (str): The category of the material.
            item (str): The specific item.

        Returns:
            dict: A dictionary containing all data for the material, or an empty dict if not found.
        """
        return self._data.get(category, {}).get(item, {})

# Example usage:
if __name__ == '__main__':
    db = MaterialDB()
    
    # Get the cost of budget ceramic tiles
    cost = db.get_material_cost('tiles', 'ceramic', 'budget')
    print(f"Cost of budget ceramic tiles per m²: €{cost}")

    # Get all info for a standard toilet
    info = db.get_material_info('sanitary', 'toilet')
    print(f"Information for a standard toilet: {info}")

    # Get cost for a material with only one quality level
    paint_cost = db.get_material_cost('finishes', 'paint')
    print(f"Cost of standard paint per liter: €{paint_cost}")

    # Get non-existent material
    non_existent_cost = db.get_material_cost('non_existent', 'item')
    print(f"Cost of non-existent item: €{non_existent_cost}") 