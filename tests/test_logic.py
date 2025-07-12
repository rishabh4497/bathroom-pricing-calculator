import unittest
from pathlib import Path
import sys

# Adjust the path to import from the parent directory
sys.path.append(str(Path(__file__).parent.parent))

from pricing_logic.material_db import MaterialDB
from pricing_logic.labor_calc import calculate_labor_cost
from pricing_logic.vat_rules import get_vat_rate
from pricing_engine import parse_transcript, generate_quote

class TestPricingLogic(unittest.TestCase):
    """Tests for individual logic components."""

    def setUp(self):
        """Set up a material database for tests."""
        test_db_path = Path(__file__).parent.parent / 'data' / 'materials.json'
        self.material_db = MaterialDB(db_path=test_db_path)

    def test_get_material_cost(self):
        """Test retrieving material costs, including fallbacks."""
        self.assertEqual(self.material_db.get_material_cost('tiles', 'ceramic', 'budget'), 20)
        self.assertEqual(self.material_db.get_material_cost('tiles', 'ceramic', 'standard'), 40)
        self.assertEqual(self.material_db.get_material_cost('sanitary', 'toilet', 'premium'), 600)
        self.assertEqual(self.material_db.get_material_cost('finishes', 'paint', 'premium'), 15, "Should fall back to standard price")
        self.assertEqual(self.material_db.get_material_cost('non_existent', 'item'), 0, "Should return 0 for non-existent items")

    def test_calculate_labor_cost(self):
        """Test labor cost calculation for different cities and tasks."""
        # Test a task with a per-sqm component in Marseille
        cost_marseille = calculate_labor_cost('demolition.remove_tiles', bathroom_area=4, city='Marseille')
        self.assertEqual(cost_marseille['estimated_time_hours'], 10)
        self.assertEqual(cost_marseille['cost'], 450)

        # Test the same task in Paris (higher multiplier)
        cost_paris = calculate_labor_cost('demolition.remove_tiles', bathroom_area=4, city='Paris')
        self.assertEqual(cost_paris['cost'], 562.5)
        
        # Test with a city not in the DB (should use default multiplier 1.0)
        cost_unknown_city = calculate_labor_cost('demolition.remove_tiles', bathroom_area=4, city='Bordeaux')
        self.assertEqual(cost_unknown_city['cost'], 450)

        # Test a fixed-time task
        cost_fixed = calculate_labor_cost('plumbing.install_toilet', bathroom_area=10, city='Lyon')
        self.assertEqual(cost_fixed['estimated_time_hours'], 3)
        self.assertEqual(cost_fixed['cost'], 148.5)
        
        # Test with zero area
        cost_zero_area = calculate_labor_cost('demolition.remove_tiles', bathroom_area=0, city='Marseille')
        self.assertEqual(cost_zero_area['estimated_time_hours'], 4) # Should only have base time
        self.assertEqual(cost_zero_area['cost'], 180)

    def test_get_vat_rate(self):
        """Test VAT rate retrieval."""
        self.assertEqual(get_vat_rate('standard'), 0.20)
        self.assertEqual(get_vat_rate('reduced'), 0.10)
        self.assertEqual(get_vat_rate('unknown_rate'), 0.20, "Should default to standard rate")

class TestPricingEngine(unittest.TestCase):
    """Integration-style tests for the main pricing engine."""

    def test_parse_transcript(self):
        """Test the transcript parser with various inputs."""
        # Standard case
        transcript_std = "Client wants to renovate a small 4m² bathroom. They’ll remove the old tiles. Budget-conscious. Located in Marseille."
        details_std = parse_transcript(transcript_std)
        self.assertEqual(details_std['bathroom_area'], 4.0)
        self.assertEqual(details_std['quality_preference'], 'budget')
        self.assertEqual(details_std['city'], 'Marseille')
        self.assertIn('demolition.remove_tiles', details_std['tasks'])
        self.assertEqual(len(details_std['error_flags']), 0)

        # Premium Paris case
        transcript_premium = "High-end 10m² renovation. Redo the plumbing for the shower. Located in Paris."
        details_premium = parse_transcript(transcript_premium)
        self.assertEqual(details_premium['bathroom_area'], 10.0)
        self.assertEqual(details_premium['quality_preference'], 'premium')
        self.assertEqual(details_premium['city'], 'Paris')
        self.assertIn('plumbing.redo_shower_plumbing', details_premium['tasks'])

        # Case with missing info
        transcript_missing = "Client wants to replace the toilet."
        details_missing = parse_transcript(transcript_missing)
        self.assertEqual(details_missing['bathroom_area'], 4.0) # Default
        self.assertEqual(details_missing['city'], 'Marseille') # Default
        self.assertEqual(details_missing['quality_preference'], 'standard') # Default
        self.assertIn('Could not determine bathroom area, using default.', details_missing['error_flags'])

    def test_generate_quote_integration(self):
        """Test the full quote generation process."""
        # Budget quote in Marseille
        transcript_budget = "A 4m² bathroom. Remove the old tiles. Budget-conscious. Located in Marseille."
        quote_budget = generate_quote(transcript_budget)
        self.assertEqual(quote_budget['client_request_summary']['requested_quality'], 'budget')
        # Calculation: Subtotal(500) + Margin(100) = 600.
        # Contingency(90) + Permit(250) = 340.
        # Before VAT = 600 + 340 = 940. VAT(94) = 1034.
        self.assertAlmostEqual(quote_budget['cost_summary']['final_total_price'], 1034.00, places=2)
        self.assertEqual(quote_budget['metadata']['confidence_score'], 1.0)
        
        # Premium quote in Paris
        transcript_premium = "A 4m² bathroom. Remove the old tiles. Premium quality. Located in Paris."
        quote_premium = generate_quote(transcript_premium)
        self.assertEqual(quote_premium['client_request_summary']['requested_quality'], 'premium')
        # Calculation: Subtotal(612.5) + Margin(122.5) = 735.
        # Contingency(110.25) + Permit(250) = 360.25.
        # Before VAT = 735 + 360.25 = 1095.25. VAT(109.53) = 1204.78
        self.assertAlmostEqual(quote_premium['cost_summary']['final_total_price'], 1204.78, places=2)
        
        # Test confidence score
        transcript_errors = "Just a renovation."
        quote_errors = generate_quote(transcript_errors)
        self.assertEqual(len(quote_errors['metadata']['error_flags']), 2) # No area, no tasks
        self.assertEqual(quote_errors['metadata']['confidence_score'], 0.5)

if __name__ == '__main__':
    unittest.main() 