import os
from difflib import SequenceMatcher

# Folder where model answer files are stored
model_answers_folder = r"D:\mini project\project\sentance database"


# File that contains the OCR output
ocr_output_file = r"D:\mini project\project\output_text.txt"

# Read model answer texts
model_texts = []
for file in os.listdir(model_answers_folder):
    if file.endswith(".txt"):  # only text files
        with open(os.path.join(model_answers_folder, file), 'r', encoding='latin-1', errors='ignore') as f:
            model_texts.append(f.read().strip())

# Read OCR output text
with open(ocr_output_file, 'r', encoding='utf-8', errors='ignore') as f:
    ocr_text = f.read().strip()

# Compare OCR output with model answers using SequenceMatcher
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Evaluate similarity with each model text
scores = [similarity(ocr_text, model) for model in model_texts]

# Get best match
best_score = max(scores) if scores else 0
best_index = scores.index(best_score) if scores else -1

print("✅ Evaluation Complete!")
print(f"📊 Best similarity score: {best_score:.2f}")
if best_index != -1:
    print(f"📄 Closest matching model answer file: {os.listdir(model_answers_folder)[best_index]}")
else:
    print("⚠ No model answer files found for comparison.")