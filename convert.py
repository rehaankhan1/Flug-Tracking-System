def icao24_to_icao(icao24):
    # Check if the ICAO24 code is valid
    if len(icao24) != 6 or not all(c in '0123456789ABCDEF' for c in icao24.upper()):
        raise ValueError("ICAO24 must be a 6-character hexadecimal string.")

    # Convert the ICAO24 hex code to binary
    binary_value = bin(int(icao24, 16))[2:].zfill(24)  # Fill to ensure it's 24 bits

    # Parse the binary string to form the ICAO code
    # Assuming a simple mapping, typically the structure is defined
    # This example simply converts it; you may need specific mappings based on ICAO
    # This would typically involve defining how the ICAO code is structured
    # The first 4 bits are usually the region, followed by specific codes.

    # For this example, we'll take a naive approach:
    # First character (4 bits) will define the first letter of the ICAO code
    # The next characters will define the rest.
    # This example uses a simplified mapping:
    
    # Get first character (1st character)
    icao_code = chr((int(binary_value[:5], 2) + 65))  # Convert to alphabet (A=65)

    # Get next characters (2nd to 4th)
    for i in range(1, 4):
        icao_code += chr((int(binary_value[5 + (i - 1) * 5:5 + i * 5], 2) + 65))  # Convert to alphabet
    
    return icao_code

# Example usage
icao24_code = '4bc8c8'  # Replace with your ICAO24 code
try:
    icao_code = icao24_to_icao(icao24_code)
    print(f"The alphabetic ICAO code for ICAO24 {icao24_code} is: {icao_code}")
except ValueError as e:
    print(e)
