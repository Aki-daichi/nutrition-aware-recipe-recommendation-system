import ast
import pandas as pd
import numpy as np
import re
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "dataset"
CF_SPLIT_DIR = Path(__file__).parent.parent / "cf" / "outputs" / "cf_split"

def load_recipes() -> pd.DataFrame:
    """
    Load raw recipes data and filter strictly based on CF split (item2idx).
    Assumes the file is RAW_recipes_cleaned.csv in the dataset directory.
    """
    import pickle
    
    # 1. Load Recipes
    try:
        df = pd.read_csv(DATA_DIR / "RAW_recipes_cleaned.csv")
    except FileNotFoundError:
        df = pd.read_csv(DATA_DIR / "RAW_recipes.csv")
        
    # 2. Filter using item2idx from CF split so features align perfectly!
    try:
        with open(CF_SPLIT_DIR / "item2idx.pkl", "rb") as f:
            item2idx = pickle.load(f)
            
        print(f"Total recipes raw: {len(df)}")
        df = df[df['id'].isin(item2idx.keys())].copy()
        print(f"Filtered recipes matching CF split: {len(df)}")
        
        # Mapping CF index
        df['cf_idx'] = df['id'].map(item2idx)
        df = df.sort_values('cf_idx').reset_index(drop=True)
    except FileNotFoundError:
        print("Warning: item2idx.pkl not found. Returning unfiltered recipes.")
        
    return df

def parse_ast_list(val):
    """
    Safely evaluate strings representing lists (e.g., "['sugar', 'salt']").
    """
    if pd.isna(val):
        return []
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return []

def extract_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and preprocess text features from recipes for NLP/TF-IDF models.
    Combines ingredients, tags, and steps (or descriptions) into a single textual representation.
    """
    df = df.copy()
    
    # Text columns that contain list structures as strings
    # Tangani perbedaan nama kolom antara dataset cleaned dan raw
    ingredients_col = 'ingredient_names' if 'ingredient_names' in df.columns else 'ingredients'
    list_cols = [ingredients_col, 'tags']
    
    for col in list_cols:
        if col in df.columns:
            df[col + '_parsed'] = df[col].apply(parse_ast_list)
            df[col + '_text'] = df[col + '_parsed'].apply(lambda x: ' '.join([str(item).lower() for item in x]))
            # Clean punctuation and extra spaces
            df[col + '_text'] = df[col + '_text'].apply(lambda x: re.sub(r'[^\w\s]', ' ', x))
            df[col + '_text'] = df[col + '_text'].apply(lambda x: re.sub(r'\s+', ' ', x).strip())
    
    # Combine text features to create a single document per recipe
    ing_text_col = ingredients_col + '_text'
    if ing_text_col in df.columns and 'tags_text' in df.columns:
        df['combined_text'] = df[ing_text_col] + ' ' + df['tags_text']
        
        # Optionally incorporate 'name'
        if 'name' in df.columns:
            df['name_clean'] = df['name'].fillna('').astype(str).str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', x))
            df['combined_text'] = df['name_clean'] + ' ' + df['combined_text']
            
    return df

if __name__ == "__main__":
    print("Testing Text Extraction...")
    df_raw = load_recipes()
    if not df_raw.empty:
        df_processed = extract_text_features(df_raw.head(10))
        print("Text features extracted successfully!")
        print(df_processed[['id', 'combined_text']].head())
