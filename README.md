# bathroom-pricing-calculator
# Bathroom Renovation Pricing Engine

This project is a smart pricing engine for bathroom renovations, built for the Donizo Founding Data Engineer Test Case. It takes a natural language description of a renovation project and outputs a structured JSON quote.

## How to Run the Code

1.  **Clone the repository (or download the files).**
2.  **Navigate to the project's root directory (`bathroom-pricing-engine`).**
3.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Run the main engine script:**
    ```bash
    python pricing_engine.py
    ```
6.  **The script will:**
    *   Parse the sample transcript provided in the script.
    *   Generate a detailed quote based on the logic in the `pricing_logic` modules.
    *   Save the output to `output/sample_quote.json`.
    *   Print the generated JSON to the console.
7.  **(Optional) Run the tests:**
    ```bash
    python tests/test_logic.py
    ```

## Schema of Output JSON

The output `sample_quote.json` is structured as follows:

```json
{
  "project_id": "string",
  "client_request_summary": {
    "transcript": "string",
    "parsed_area_sqm": "float",
    "parsed_city": "string",
    "requested_quality": "string (budget/standard/premium)"
  },
  "quote_details": [
    {
      "group": "string (e.g., Demolition, Plumbing)",
      "task_name": "string",
      "materials": [
        {
          "name": "string",
          "category": "string",
          "item": "string",
          "quantity": "float",
          "unit": "string",
          "cost_per_unit": "float",
          "total_cost": "float"
        }
      ],
      "labor": {
        "task_name": "string",
        "estimated_time_hours": "float",
        "cost": "float"
      },
      "task_subtotal": "float"
    }
  ],
  "cost_summary": {
    "total_material_cost": "float",
    "total_labor_cost": "float",
    "total_estimated_hours": "float",
    "subtotal": "float",
    "margin_applied": "string",
    "margin_amount": "float",
    "total_before_vat": "float",
    "vat_rate_type": "string",
    "vat_rate": "float",
    "vat_amount": "float",
    "final_total_price": "float"
  },
  "metadata": {
    "confidence_score": "float",
    "error_flags": ["string"],
    "pricing_logic_version": "string",
    "timestamp": "isoformat_string",
    "feedback_applied": "object (optional)"
  }
}
```

## Explanation of Pricing Logic

The pricing is determined by a combination of factors:

1.  **Transcript Parsing**: The `pricing_engine.py` script uses regular expressions and keyword matching to parse the input transcript for:
    *   **Bathroom Area**: Extracts size in m².
    *   **Tasks**: Identifies renovation tasks (e.g., "remove tiles", "install vanity").
    *   **Quality Preference**: Determines if the client is "budget-conscious", "standard", or "premium".
    *   **Location**: Extracts the city to apply regional cost multipliers.

2.  **Material Costs**:
    *   Material costs are stored in `data/materials.json`.
    *   This JSON database includes prices for different quality levels (`budget`, `standard`, `premium`).
    *   The `pricing_logic/material_db.py` module loads and provides access to this data.

3.  **Labor Costs**:
    *   Labor calculations are handled by `pricing_logic/labor_calc.py`.
    *   It uses a `TASK_LABOR_DB` to estimate the time required for each task, which can be a combination of a fixed base time and a variable time per square meter.
    *   Hourly rates are defined based on the skill level required for the task (`low`, `medium`, `high`).
    *   A city-based multiplier (`CITY_MULTIPLIERS`) adjusts labor costs for different regions (e.g., Paris is more expensive than Marseille).

4.  **Margin**:
    *   A fixed margin (currently 20%) is applied to the subtotal of materials and labor to ensure business profitability.

5.  **VAT (Value-Added Tax)**:
    *   VAT rules are defined in `pricing_logic/vat_rules.py`.
    *   A reduced VAT rate (10%) is applied, as is common for renovation work in many countries.

6.  **Confidence Score**:
    *   A simple confidence score is calculated. It starts at 1.0 and is reduced for each piece of information that could not be successfully parsed from the transcript (e.g., if the bathroom area is not mentioned).

7.  **Feedback Loop (Simulated)**:
    *   The engine includes a simulated feedback mechanism (`apply_feedback` function). This demonstrates how a quote could be adjusted based on external factors, like a competitor's price.

## Assumptions & Edge Cases

*   **Default Values**: If the parser cannot determine the bathroom area or city, it falls back to default values (4m² and Marseille, respectively). An error flag is raised in the output metadata.
*   **Wall Area**: The area for wall-related tasks (like painting) is estimated as a multiple of the floor area. This is a simplification.
*   **Task-Material Mapping**: The `TASK_MATERIAL_MAPPING` in `pricing_engine.py` contains a fixed list of materials required for each task. This could be made more dynamic in a future version.
*   **Language**: The parser is designed for English transcripts and the specific keywords used in the test case. It is not a generic NLP model.
*   **Material Availability**: The system assumes all materials are available. A real-world system would need to check inventory or connect to supplier APIs. 