import inspect
import sys

# 1. Target the official high-performance indicator compilation layer
try:
    from openalgo import api as target_module
except ImportError:
    print("❌ Critical Error: Please run 'pip install --upgrade openalgo' to ensure the Rust core is installed.")
    sys.exit(1)


# from openalgo import api as target_module
# from openalgo import Strategy as target_module
# from openalgo import ta as target_module
# from openalgo import HAS_NUMBA as target_module
# from openalgo import prange as target_module
# from openalgo import nbjit as target_module




module_symbols = dir(target_module)
print(f"🔁 OpenAlgo High-Performance Modules Scanner Running for module:{target_module}.\n")
print("=" * 80)

text_block = """Modules / Mathematical Endpoints: All public methods with their
1.signatures
2.return type 
3.annotations
4.docstring 
5.actual source file and line number"""
print(text_block)
print("=" * 80)

# Unpack internal module references if hidden inside an extension wrapper
module_symbols = dir(target_module)

# Counter to verify total extraction volume
total_found = 0

for name in sorted(module_symbols):
    # Filter private symbols
    if name.startswith("_"):
        continue

    try:
        obj = getattr(target_module, name)
        print(f"\n🔹 EXTRACTED: {name.upper()}")
        # Ensure we are extracting indicator functions or mathematical utilities
        if callable(obj):
            total_found += 1
            print(f"\n📈 Type:           METHOD [Method Number {total_found}]: {name.upper()}")
            
            print("  Type:           COMPILED RUST FUNCTION")
            # 1 & 2 & 3. Extract Signature, Return Type, and Annotations
            try:
                sig = inspect.signature(obj)
                return_type = sig.return_annotation
                if return_type is inspect.Signature.empty:
                    return_type = "Not Specified (Handled by Rust Core)"
                
                annotations = getattr(obj, "__annotations__", {})
                print(f"  1. Signature:   {name}{sig}")
                print(f"  2. Return Type: {return_type}")
                print(f"  3. Annotations: {annotations if annotations else 'Implicitly typed inside wheel'}")
            except (ValueError, TypeError):
                # Built-in or compiled functions often do not expose signatures to python's inspect module
                print(f"  1. Signature:   {name}(*args, **kwargs)")
                print("  2. Return Type: Variant Array / Float")
                print("  3. Annotations: Bound in pre-compiled binary wrapper")

            # 4. Docstring extraction
            doc = inspect.getdoc(obj)
            if doc:
                clean_doc = "\n".join(f"      {line}" for line in doc[:5000].splitlines())
                print(f"  4. Docstring:\n{clean_doc}")
            else:
                print("  4. Docstring:   None provided (refer to docs.openalgo.in).")

            # 5. Extract source file and line number
            try:
                source_file = inspect.getfile(obj)
                _, line_num = inspect.getsourcelines(obj)
                print(f"  5. Source File: {source_file}")
                print(f"     Line Number: {line_num}")
            except (TypeError, OSError):
                # This safely informs you that it's a high-performance compiled binary function
                print("  5. Source Info: OpenAlgo Rust Core Core Extension (No Python source text line).")
        else:
            # Handles primitive properties or variables
            print("  Type:           VARIABLE / PROPERTY")
            # Variables don't have individual modules, so print parent class module
            print(f"  Parent Module:  {type(target_instance).__module__}")
            print(f"  Value:          {repr(obj)}")

        print("-" * 80)
    except Exception as e:
        print(f"❌ ERROR PROCESSING '{name}': {e}")

print(f"\n✅ Scan Complete. Successfully uncovered {total_found} indicator endpoints.")
