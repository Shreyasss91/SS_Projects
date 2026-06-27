import os
import base64
import urllib.parse
from PIL import Image
from pyzbar.pyzbar import decode

# 1. Update your image path here
# (Supports .png, .jpg, .jpeg, etc.)
image_path = r"E:\Downloads\AI Codes\openalgo\strategies\SS_Projects\fyers_token\secret_key\QR_Image.jpg"
print(f"\nUsing QR code image at: {image_path}")
print("Ensure the image is clear and unblurred for accurate scanning.")
print("If you encounter issues, consider using a different image or checking the QR code quality.")
print("Note: This script is designed to extract migration strings from QR codes, specifically for Google Authenticator exports.")
print("--- Instructions ---")
print("1. Ensure you have the required libraries installed: Pillow and pyzbar.\n")


def base32_encode(raw_bytes):
    """Encodes raw binary bytes into a standard 32-character Base32 string."""
    return base64.b32encode(raw_bytes).decode('utf-8').replace('=', '')

def parse_protobuf_manually(data_bytes):
    accounts = []
    i = 0
    length = len(data_bytes)
    
    # Mapping dictionaries for Protobuf enum values
    ALGO_MAP = {1: "SHA1", 2: "SHA256", 3: "SHA512", 4: "MD5"}
    DIGITS_MAP = {0: "6", 1: "6", 2: "8"} # Google Auth defaults to 6 digits if unspecified
    TYPE_MAP = {1: "HOTP", 2: "TOTP"}
    
    while i < length:
        tag = data_bytes[i]
        i += 1
        wire_type = tag & 0x07
        field_number = tag >> 3
        
        if field_number == 1 and wire_type == 2:
            # Read varint length of the inner account payload
            inner_len = 0
            shift = 0
            while True:
                b = data_bytes[i]
                i += 1
                inner_len |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
                
            end_of_payload = i + inner_len
            
            # Initialise all 7 fields with standard defaults
            secret = None   # Field 1
            name = "Unknown" # Field 2
            issuer = "Unknown" # Field 3
            algo = "SHA1"   # Field 4
            digits = "6"    # Field 5
            otp_type = "TOTP" # Field 6
            counter = 0     # Field 7
            
            while i < end_of_payload:
                inner_tag = data_bytes[i]
                i += 1
                inner_wire = inner_tag & 0x07
                inner_field = inner_tag >> 3
                
                # --- CASE 1: LENGTH-DELIMITED FIELDS (Wire Type 2) ---
                if inner_wire == 2:
                    # Read length indicator
                    field_len = 0
                    shift = 0
                    while True:
                        b = data_bytes[i]
                        i += 1
                        field_len |= (b & 0x7F) << shift
                        if not (b & 0x80): break
                        shift += 7
                    
                    if inner_field == 1:       # 1. Secret Key
                        secret_bytes = data_bytes[i:i+field_len]
                        secret = base32_encode(secret_bytes)
                        i += field_len
                    elif inner_field == 2:     # 2. Account Name
                        name = data_bytes[i:i+field_len].decode('utf-8', errors='ignore')
                        i += field_len
                    elif inner_field == 3:     # 3. Issuer
                        issuer = data_bytes[i:i+field_len].decode('utf-8', errors='ignore')
                        i += field_len
                    else:
                        i += field_len         # Skip unknown length-delimited fields
                        
                # --- CASE 2: VARINT FIELDS (Wire Type 0) ---
                elif inner_wire == 0:
                    # Read the Varint value directly
                    varint_val = 0
                    shift = 0
                    while True:
                        b = data_bytes[i]
                        i += 1
                        varint_val |= (b & 0x7F) << shift
                        if not (b & 0x80): break
                        shift += 7
                        
                    if inner_field == 4:       # 4. Hashing Algorithm
                        algo = ALGO_MAP.get(varint_val, f"Unknown ({varint_val})")
                    elif inner_field == 5:     # 5. Pin Digits Length
                        digits = DIGITS_MAP.get(varint_val, f"Unknown ({varint_val})")
                    elif inner_field == 6:     # 6. OTP Type
                        otp_type = TYPE_MAP.get(varint_val, f"Unknown ({varint_val})")
                    elif inner_field == 7:     # 7. Counter (For HOTP)
                        counter = varint_val
            
            if secret:
                accounts.append({
                    "issuer": issuer, "name": name, "secret": secret, 
                    "type": otp_type, "algo": algo, "digits": digits, "counter": counter
                })
        else:
            # Skip non-relevant top-level structural fields safely
            if wire_type == 0:
                while data_bytes[i] & 0x80: i += 1
                i += 1
            elif wire_type == 2:
                skip_len = 0
                shift = 0
                while True:
                    b = data_bytes[i]
                    i += 1
                    skip_len |= (b & 0x7F) << shift
                    if not (b & 0x80): break
                    shift += 7
                i += skip_len
            elif wire_type == 1: i += 8
            elif wire_type == 5: i += 4
            
    return accounts

def extract_and_decode(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print("Scanning QR code locally...")
    img = Image.open(file_path)
    decoded_objects = decode(img)
    
    if not decoded_objects:
        print("No QR code detected in the image.")
        return

    migration_string = decoded_objects[0].data.decode('utf-8')
    print(f"Migration string:{migration_string}")
    if "otpauth-migration" not in migration_string:
        print("Error: This QR code is not a Google Authenticator migration export.")
        return

    # Extract the base64 encrypted query string
    parsed_url = urllib.parse.urlparse(migration_string)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    if 'data' not in query_params:
        print("Error: Could not find migration data payload in the URL string.")
        return
        
    base64_data = query_params['data'][0]
    
    # Fix potential padding padding issues or URL artifact gaps
    try:
        raw_bytes = base64.b64decode(base64_data)
    except Exception:
        # Add padding back manually if it was stripped
        raw_bytes = base64.b64decode(base64_data + "===")

    # Parse and display the secrets
    extracted_accounts = parse_protobuf_manually(raw_bytes)
    
    # --- MIGRATION DATA SUMMARY FORMAT ---
    # Width adjusted to 110 characters to comfortably accommodate all 7 fields
    print("\n" + "="*110)
    print(f"{'COMPREHENSIVE MIGRATION SUMMARY':^110}")
    print("="*110)
    
    header_fmt = "{:<12} | {:<22} | {:<6} | {:<7} | {:<6} | {:<8} | {:<32}"
    print(header_fmt.format('ISSUER', 'ACCOUNT NAME', 'TYPE', 'ALGO', 'DIGITS', 'COUNTER', 'SECRET KEY'))
    print("-"*110)
    
    for account in extracted_accounts:
        print(header_fmt.format(
            account['issuer'], 
            account['name'], 
            account['type'], 
            account['algo'], 
            account['digits'], 
            account['counter'], 
            account['secret']
        ))
        
    print("="*110 + "\n")


if __name__ == "__main__":
    extract_and_decode(image_path)
