# pricing_engine.py

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set

from pydantic import BaseModel, Field

from pricing_logic.material_db import MaterialDB
from pricing_logic.labor_calc import calculate_labor_cost
from pricing_logic.vat_rules import get_vat_rate

# --- Pydantic Models for Structured Output ---

class Material(BaseModel):
    name: str
    category: str
    item: str
    quantity: float
    unit: str
    cost_per_unit: float
    total_cost: float

class Labor(BaseModel):
    task_name: str
    estimated_time_hours: float
    cost: float

class QuoteDetail(BaseModel):
    group: str
    task_name: str
    materials: List[Material]
    labor: Labor
    task_subtotal: float

class ClientRequestSummary(BaseModel):
    transcript: str
    parsed_area_sqm: float
    parsed_city: str
    requested_quality: str

class CostSummary(BaseModel):
    total_material_cost: float = 0.0
    total_labor_cost: float = 0.0
    total_estimated_hours: float = 0.0
    subtotal: float = 0.0
    margin_applied: str
    margin_amount: float
    total_before_vat: float
    vat_rate_type: str
    vat_rate: float
    vat_amount: float
    final_total_price: float

class Feedback(BaseModel):
    notes: str
    original_price: float

class Metadata(BaseModel):
    confidence_score: float = 1.0
    error_flags: List[str] = []
    pricing_logic_version: str = "2.0"
    timestamp: datetime = Field(default_factory=datetime.now)
    feedback_applied: Optional[Feedback] = None

class Quote(BaseModel):
    project_id: str = Field(default_factory=lambda: f"PROJ-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    client_request_summary: ClientRequestSummary
    quote_details: List[QuoteDetail]
    cost_summary: CostSummary
    metadata: Metadata

# --- 1. Transcript Parsing (Improved) ---

TASK_KEYWORDS = {
    "demolition.remove_tiles": [r"remove.*tiles"],
    "plumbing.redo_shower_plumbing": [r"redo.*plumbing", r"plumbing.*shower"],
    "plumbing.install_toilet": [r"replace.*toilet", r"install.*toilet"],
    "installation.install_vanity": [r"install.*vanity"],
    "finishing.repaint_walls": [r"repaint.*walls", r"paint.*walls"],
    "installation.lay_floor_tiles": [r"lay.*tiles", r"new.*tiles"],
}

QUALITY_KEYWORDS = {
    "budget": [r"budget-conscious", r"budget conscious", r"cheap"],
    "premium": [r"premium", r"high-end", r"luxury"],
}

def parse_transcript(transcript: str) -> dict:
    """Parses a client transcript using more robust regex matching."""
    details = {
        "bathroom_area": 4.0,
        "tasks": set(),
        "quality_preference": "standard",
        "city": "Marseille",
        "error_flags": [],
    }

    # Extract bathroom area
    if match := re.search(r'(\d+)\s*m²', transcript):
        details["bathroom_area"] = float(match.group(1))
    else:
        details["error_flags"].append("Could not determine bathroom area, using default.")

    # Extract tasks
    for task_id, patterns in TASK_KEYWORDS.items():
        if any(re.search(p, transcript, re.IGNORECASE) for p in patterns):
            details["tasks"].add(task_id)
    if not details["tasks"]:
        details["error_flags"].append("No tasks were identified from the transcript.")

    # Extract quality
    for quality, patterns in QUALITY_KEYWORDS.items():
        if any(re.search(p, transcript, re.IGNORECASE) for p in patterns):
            details["quality_preference"] = quality
            break
            
    # Extract city
    if match := re.search(r'located in (\w+)', transcript, re.IGNORECASE):
        details["city"] = match.group(1).title()

    return details

# --- 2. Main Pricing Logic (Refactored) ---

TASK_MATERIAL_MAPPING = {
    "demolition.remove_tiles": [
        {"category": "demolition", "item": "waste_disposal", "quantity_per_sqm": 0.25}
    ],
    "installation.lay_floor_tiles": [
        {"category": "tiles", "item": "ceramic", "quantity_per_sqm": 1.05}, # 5% extra for cuts
        {"category": "finishes", "item": "grout", "quantity_per_sqm": 0.5},
        {"category": "finishes", "item": "silicone", "quantity_per_sqm": 0.1}
    ],
    "plumbing.redo_shower_plumbing": [
        {"category": "plumbing", "item": "shower_kit", "quantity": 1},
        {"category": "plumbing", "item": "pipes", "quantity": 5} # Assume 5 meters of pipes
    ],
    "plumbing.install_toilet": [
        {"category": "sanitary", "item": "toilet", "quantity": 1}
    ],
    "installation.install_vanity": [
        {"category": "sanitary", "item": "vanity", "quantity": 1}
    ],
    "finishing.repaint_walls": [
        # Assuming wall area is 3x floor area, and 1 liter covers 10m^2
        {"category": "finishes", "item": "paint", "quantity_per_sqm": 0.3}
    ]
}


def _calculate_task_details(task_id: str, parsed_details: dict, material_db: MaterialDB) -> QuoteDetail:
    """Calculates all costs for a single task and returns a QuoteDetail model."""
    task_group, task_name = task_id.split('.')
    quality = parsed_details["quality_preference"]
    bathroom_area = parsed_details["bathroom_area"]

    # Material calculations
    material_costs = []
    task_material_total = 0.0
    for req in TASK_MATERIAL_MAPPING.get(task_id, []):
        cost_per_unit = material_db.get_material_cost(req["category"], req["item"], quality)
        quantity = req.get("quantity", req.get("quantity_per_sqm", 0) * bathroom_area)
        info = material_db.get_material_info(req["category"], req["item"])
        
        material_cost = cost_per_unit * quantity
        task_material_total += material_cost
        material_costs.append(Material(
            name=info.get("name", "Unknown"),
            category=req["category"],
            item=req["item"],
            quantity=round(quantity, 2),
            unit=info.get("unit", ""),
            cost_per_unit=cost_per_unit,
            total_cost=round(material_cost, 2)
        ))

    # Labor calculations
    labor_details = calculate_labor_cost(task_id, bathroom_area, parsed_details["city"])
    labor = Labor(**labor_details) if labor_details else Labor(task_name=task_name, estimated_time_hours=0, cost=0)
    
    return QuoteDetail(
        group=task_group.title(),
        task_name=labor.task_name,
        materials=material_costs,
        labor=labor,
        task_subtotal=round(task_material_total + labor.cost, 2)
    )

def generate_quote(transcript: str) -> dict:
    """Main function to generate a structured quote from a transcript."""
    material_db = MaterialDB()
    parsed_details = parse_transcript(transcript)

    # Create summary and metadata
    summary = ClientRequestSummary(
        transcript=transcript,
        parsed_area_sqm=parsed_details["bathroom_area"],
        parsed_city=parsed_details["city"],
        requested_quality=parsed_details["quality_preference"]
    )
    metadata = Metadata(error_flags=parsed_details["error_flags"])
    
    # Calculate details for each task
    quote_details = [_calculate_task_details(task_id, parsed_details, material_db) for task_id in sorted(list(parsed_details["tasks"]))]
    
    # Aggregate costs
    total_material = sum(m.total_cost for detail in quote_details for m in detail.materials)
    total_labor = sum(d.labor.cost for d in quote_details)
    total_hours = sum(d.labor.estimated_time_hours for d in quote_details)
    subtotal = total_material + total_labor
    
    # Margin and VAT
    margin_rate = 0.20
    margin = subtotal * margin_rate
    total_before_vat = subtotal + margin
    vat_rate = get_vat_rate('reduced')
    vat = total_before_vat * vat_rate
    
    cost_summary = CostSummary(
        total_material_cost=round(total_material, 2),
        total_labor_cost=round(total_labor, 2),
        total_estimated_hours=round(total_hours, 2),
        subtotal=round(subtotal, 2),
        margin_applied=f"{margin_rate:.0%}",
        margin_amount=round(margin, 2),
        total_before_vat=round(total_before_vat, 2),
        vat_rate_type='reduced',
        vat_rate=vat_rate,
        vat_amount=round(vat, 2),
        final_total_price=round(total_before_vat + vat, 2)
    )

    # Adjust confidence score
    metadata.confidence_score -= len(metadata.error_flags) * 0.25
    
    quote = Quote(
        client_request_summary=summary,
        quote_details=quote_details,
        cost_summary=cost_summary,
        metadata=metadata
    )
    
    return quote.model_dump(mode="json")


# --- Main Execution ---
if __name__ == '__main__':
    client_transcript = (
        "Client wants to renovate a small 4m² bathroom. They’ll remove the old tiles, "
        "redo the plumbing for the shower, replace the toilet, install a vanity, "
        "repaint the walls, and lay new ceramic floor tiles. "
        "Budget-conscious. Located in Marseille."
    )

    final_quote = generate_quote(client_transcript)

    output_path = Path(__file__).parent / 'output' / 'sample_quote.json'
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_quote, f, indent=4)
        
    print(f"✅ Quote generated successfully and saved to {output_path}")
    print("\n--- SAMPLE QUOTE ---")
    print(json.dumps(final_quote, indent=4)) 