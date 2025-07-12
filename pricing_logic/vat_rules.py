# pricing_logic/vat_rules.py

def get_vat_rate(vat_type: str = 'standard') -> float:
    """
    Returns the VAT rate based on the type.
    
    In France, renovation work can benefit from a reduced VAT rate.
    - Standard rate: 20%
    - Reduced rate for renovation: 10% or 5.5%
    We will use a simplified model here.
    
    Args:
        vat_type (str): 'standard' or 'reduced'.

    Returns:
        float: The VAT rate as a multiplier (e.g., 0.20 for 20%).
    """
    rates = {
        'standard': 0.20,
        'reduced': 0.10,
        'super_reduced': 0.055,
        'none': 0.0
    }
    return rates.get(vat_type, 0.20) # Default to standard rate

# Example usage:
if __name__ == '__main__':
    standard_rate = get_vat_rate('standard')
    print(f"Standard VAT rate: {standard_rate*100}%")

    reduced_rate = get_vat_rate('reduced')
    print(f"Reduced VAT rate: {reduced_rate*100}%")

    non_existent_rate = get_vat_rate('something_else')
    print(f"Non-existent VAT rate (defaults to standard): {non_existent_rate*100}%") 