# Python's inspect module to enumerate all public methods, print their signatures, and optionally show return type annotations.
import os
import inspect
from openalgo import api

# Environment variables
api_key = os.getenv("OPENALGO_API_KEY")
host = os.getenv("HOST_SERVER") or os.getenv("OPENALGO_HOST", "http://127.0.0.1:5000")

client = api(api_key=api_key, host=host)

print("🔁 OpenAlgo Python Bot is running.\n")
print("=" * 80)

text_block = """API Server Endpoints: All public methods with their
1.signatures
2.return type 
3.annotations
4.docstring 
5.actual source file and line number"""
print(text_block)
print("=" * 80)

# Process all public endpoints and attributes
for name in sorted(dir(client)):
    if name.startswith("_"):
        continue

    try:
        obj = getattr(client, name)
        print(f"\n🔹 EXTRACTED: {name.upper()}")

        if callable(obj):
            print("  Type:           METHOD")
            
            # 1 & 2 & 3. Extract Signature, Return Type, and Annotations
            try:
                sig = inspect.signature(obj)
                return_type = sig.return_annotation
                if return_type is inspect.Signature.empty:
                    return_type = "Not Specifed"
                
                # Retrieve explicit Python dict type annotations
                annotations = getattr(obj, "__annotations__", {})
                
                print(f"  1. Signature:   {name}{sig}")
                print(f"  2. Return Type: {return_type}")
                print(f"  3. Annotations: {annotations if annotations else 'None found'}")
            except Exception as e:
                print(f"  Signature Error: {e}")

            # 4. Docstring extraction
            doc = inspect.getdoc(obj)
            if doc:
                # Clean up indentation and limit size
                clean_doc = "\n".join(f"      {line}" for line in doc[:5000].splitlines())
                print(f"  4. Docstring:\n{clean_doc}")
            else:
                print("  4. Docstring:   None provided.")

            # 5. Extract source file and line number
            try:
                source_file = inspect.getfile(obj)
                _, line_num = inspect.getsourcelines(obj)
                print(f"  5. Source File: {source_file}")
                print(f"     Line Number: {line_num}")
            except (TypeError, OSError):
                # Handles compiled modules, built-ins, or dynamically injected methods
                print("  5. Source Info: External compiled code / source line untrackable.")

        else:
            # Handles primitive properties or variables
            print("  Type:           VARIABLE / PROPERTY")
            print(f"  Value:          {repr(obj)}")
            
        print("-" * 80)

    except Exception as e:
        print(f"❌ ERROR PROCESSING '{name}': {e}")
    
        