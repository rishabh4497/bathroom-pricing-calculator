import pandas as pd
from pathlib import Path

# --- Data Loading ---

def load_task_db():
    """Loads the task database from the CSV file."""
    db_path = Path(__file__).parent.parent / 'data' / 'price_templates.csv'
    if not db_path.exists():
        raise FileNotFoundError(f"Price templates file not found at {db_path}")
    
    # Use task_id as the index for quick lookups
    df = pd.read_csv(db_path)
    return df.set_index('task_id').to_dict('index')

# Load the data once when the module is imported
TASK_LABOR_DB = load_task_db()

# --- Hardcoded Business Logic (Rates & Multipliers) ---

# These could also be moved to a configuration file in a more complex app
HOURLY_RATES = {
    "low": 30,
    "medium": 45,
    "high": 60,
}

CITY_MULTIPLIERS = {
    "Marseille": 1.0,
    "Paris": 1.25,
    "Lyon": 1.1,
}

# --- Calculation Function ---

def calculate_labor_cost(task_id: str, bathroom_area: float, city: str = "Marseille"):
    """
    Calculates the labor cost for a single task using the CSV data.
    """
    task_info = TASK_LABOR_DB.get(task_id)
    if not task_info:
        return None

    # Calculate time
    total_time = task_info.get("base_time", 0) + (task_info.get("time_per_sqm", 0) * bathroom_area)

    # Calculate cost
    hourly_rate = HOURLY_RATES.get(task_info.get("skill_level", "medium"), 45)
    city_multiplier = CITY_MULTIPLIERS.get(city, 1.0)
    total_cost = total_time * hourly_rate * city_multiplier

    # Get the friendly task name from the task_id
    task_name = task_id.split('.')[-1].replace('_', ' ').title()

    return {
        "task_name": task_name,
        "estimated_time_hours": round(total_time, 2),
        "cost": round(total_cost, 2)
    }

# Example usage:
if __name__ == '__main__':
    area = 4  # 4m²
    city = 'Marseille'
    
    # Calculate cost for removing tiles in Marseille
    tile_removal_cost = calculate_labor_cost('demolition.remove_tiles', area, city)
    print(f"Cost to remove tiles in a {area}m² bathroom in {city}: {tile_removal_cost}")

    # Calculate cost for the same task in Paris
    city_paris = 'Paris'
    tile_removal_cost_paris = calculate_labor_cost('demolition.remove_tiles', area, city_paris)
    print(f"Cost to remove tiles in a {area}m² bathroom in {city_paris}: {tile_removal_cost_paris}") 