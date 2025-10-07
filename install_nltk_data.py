#!/usr/bin/env python3
"""
Script to download required NLTK data for the Stress Management Coach
"""

import nltk
import sys

def main():
    print("Downloading required NLTK data...")
    
    # List of required NLTK datasets
    datasets = ['punkt', 'stopwords', 'vader_lexicon']
    
    for dataset in datasets:
        try:
            print(f"Downloading {dataset}...")
            nltk.download(dataset, quiet=False)
            print(f"✓ {dataset} downloaded successfully")
        except Exception as e:
            print(f"✗ Error downloading {dataset}: {e}")
            sys.exit(1)
    
    print("\nAll NLTK data downloaded successfully!")
    print("You can now run the Stress Estimator Agent.")

if __name__ == "__main__":
    main()