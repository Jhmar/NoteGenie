import nltk
import os

print("=" * 60)
print("📥 DOWNLOADING NLTK DATA FOR NOTEGENIE")
print("=" * 60)

# Create nltk_data directory in a accessible location
nltk_data_path = os.path.join(os.path.expanduser('~'), 'nltk_data')
os.makedirs(nltk_data_path, exist_ok=True)

# Add to NLTK path
nltk.data.path.append(nltk_data_path)

print(f"NLTK data will be saved to: {nltk_data_path}")

# Required NLTK packages
required_packages = [
    'punkt',        # Sentence tokenizer
    'stopwords',    # Stopwords list
    'punkt_tab',    # Tokenizer tables
    'averaged_perceptron_tagger'  # POS tagger (optional but useful)
]

print("\n📦 Downloading packages...")
for package in required_packages:
    try:
        print(f"\n⬇️  Downloading '{package}'...")
        nltk.download(package, quiet=False)
        print(f"✅ '{package}' downloaded successfully!")
    except Exception as e:
        print(f"⚠️  Failed to download '{package}': {e}")

print("\n" + "=" * 60)
print("✅ DOWNLOAD COMPLETE!")
print("=" * 60)
print("\n📋 Summary of downloaded packages:")
for package in required_packages:
    try:
        nltk.data.find(package)
        print(f"  ✓ {package}")
    except:
        print(f"  ✗ {package} (failed)")

print("\n🔧 Next steps:")
print("1. RESTART your FastAPI server")
print("2. Test the summarization feature again")
print("=" * 60)