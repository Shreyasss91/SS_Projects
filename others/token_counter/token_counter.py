import tiktoken
from pathlib import Path
import locale

# ====================================================================
# import tiktoken.model
# # 1. Exact model names explicitly mapped
# exact_models = list(tiktoken.model.MODEL_TO_ENCODING.keys())

# # 2. Model prefix rules (e.g., "gpt-4o-", "gpt-4-")
# prefix_models = list(tiktoken.model.MODEL_PREFIX_TO_ENCODING.keys())

# print("--- Exact Models ---")
# print(exact_models)

# print("\n--- Prefix Rules ---")
# print(prefix_models)
# ====================================================================

# 0. Dynamically locate msg.txt relative to this script's directory
SCRIPT_DIR = Path(__file__).resolve().parent
FILE_PATH = SCRIPT_DIR / "msg.txt"

# 1. Read the text from the msg.txt file
try:
    with open(FILE_PATH, "r", encoding="utf-8") as file:
        text_content = file.read()
except FileNotFoundError:
    print("Error: The file './msg.txt' was not found.")
    text_content = None

if text_content is not None:
    # 2. Get the encoding for the model
    # Note: If your local tiktoken version doesn't have the explicit "gpt-5" string 
    # mapped yet, use tiktoken.get_encoding("o200k_base") directly.
    try:
        encoding = tiktoken.encoding_for_model("gpt-5")
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")

    # 3. Encode the file's text and get the count
    token_list = encoding.encode(text_content)
    token_count = len(token_list)
    # print(f"Total tokens in msg.txt: {len(token_list)}")
    

# Set the locale to English (India) to apply the lakh/crore format
# Note: On Windows, use "English_India.1252" or "hi_IN" if "en_IN" raises an error
try:
    locale.setlocale(locale.LC_ALL, "en_IN.utf-8")
except locale.Error:
    locale.setlocale(locale.LC_ALL, "") # Fallback to system default

# Format the number using local grouping rules
formatted_count = locale.format_string("%d", token_count, grouping=True)

print(f"Total tokens in msg.txt: {formatted_count}")