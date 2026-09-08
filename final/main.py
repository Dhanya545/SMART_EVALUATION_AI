import os
import cv2
import pytesseract

# ✅ Path to Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"D:\mini project\data"

# ✅ Path to your dataset folder (which contains subfolders with images)
base_folder = r"C:\Users\DELL\Desktop\5TH SEM\AI\chartbot\data"

# ✅ Supported image extensions
valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.jfif')

output_text = ""
count = 0
limit = 10  # 👈 Process only first 10 images for testing (you can increase later)

# 🔍 Scan all subfolders
for root, dirs, files in os.walk(base_folder):
    for file in files:
        if file.lower().endswith(valid_exts):
            count += 1
            img_path = os.path.join(root, file)
            print(f"\n📄 [{count}] Processing: {img_path}")

            # Stop after 'limit' images for testing
            if count > limit:
                print("\n⚠ Reached test limit. Stopping early to avoid long processing.")
                break

            # Read image
            img = cv2.imread(img_path)
            if img is None:
                print("⚠ Skipping unreadable image.")
                continue

            # Resize for faster OCR
            img = cv2.resize(img, (1000, 1000))

            # Convert to grayscale & threshold
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            # Extract text using Tesseract
            text = pytesseract.image_to_string(gray, lang='eng')

            # Add extracted text
            output_text += f"\n--- {file} ---\n{text}\n"

    if count > limit:
        break

# ✅ Save all extracted text to one file
if output_text.strip():
    with open("output_text.txt", "w", encoding="utf-8") as f:
        f.write(output_text)
    print(f"\n✅ OCR complete! Processed {count if count < limit else limit} images.")
    print("📂 Text saved to: output_text.txt")
else:
    print("\n❌ No images found inside the folder or subfolders!")