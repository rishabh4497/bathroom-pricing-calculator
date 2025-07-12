# pricing_logic/labor_calc.py

# This database defines the estimated time for various tasks.
# Time is in hours. 'base_time' is a fixed time, while 'time_per_sqm' is per square meter.
TASK_LABOR_DB = {
    "demolition": {
        "remove_tiles": {"base_time": 4, "time_per_sqm": 1.5, "skill_level": "medium"},
        "remove_toilet": {"base_time": 1, "time_per_sqm": 0, "skill_level": "low"},
        "remove_vanity": {"base_time": 1, "time_per_sqm": 0, "skill_level": "low"},
    },
    "plumbing": {
        "redo_shower_plumbing": {"base_time": 8, "time_per_sqm": 0, "skill_level": "high"},
        "install_toilet": {"base_time": 3, "time_per_sqm": 0, "skill_level": "medium"},
    },
    "installation": {
        "lay_floor_tiles": {"base_time": 4, "time_per_sqm": 2, "skill_level": "high"},
        "install_vanity": {"base_time": 3, "time_per_sqm": 0, "skill_level": "medium"},
    },
    "finishing": {
        "repaint_walls": {"base_time": 2, "time_per_sqm": 1, "skill_level": "low"},
    }
}

# Hourly rates based on skill level
HOURLY_RATES = {
    "low": 30,
    "medium": 45,
    "high": 60,
}

# City-based cost multiplier
CITY_MULTIPLIERS = {
    "Marseille": 1.0,
    "Paris": 1.25,
    "Lyon": 1.1,
}

def calculate_labor_cost(task_key: str, bathroom_area: float, city: str = "Marseille"):
    """
    Calculates the labor cost for a single task.

    Args:
        task_key (str): A key like "demolition.remove_tiles".
        bathroom_area (float): The area of the bathroom in m².
        city (str): The city where the work is being done.

    Returns:
        dict: A dictionary with 'time' and 'cost', or None if task not found.
    """
    category, task_name = task_key.split('.')
    
    task_info = TASK_LABOR_DB.get(category, {}).get(task_name)
    if not task_info:
        return None

    # Calculate time
    base_time = task_info.get("base_time", 0)
    time_per_sqm = task_info.get("time_per_sqm", 0)
    total_time = base_time + (time_per_sqm * bathroom_area)

    # Calculate cost
    skill_level = task_info.get("skill_level", "medium")
    hourly_rate = HOURLY_RATES.get(skill_level, 45)
    
    city_multiplier = CITY_MULTIPLIERS.get(city, 1.0)
    
    total_cost = total_time * hourly_rate * city_multiplier

    return {
        "task_name": task_name.replace('_', ' ').title(),
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

    # Calculate cost for a fixed-time task
    toilet_install_cost = calculate_labor_cost('plumbing.install_toilet', area, city)
    print(f"Cost to install a toilet in {city}: {toilet_install_cost}") 