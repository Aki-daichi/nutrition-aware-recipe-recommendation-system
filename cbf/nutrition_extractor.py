import ast
import pandas as pd
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "dataset"
CF_SPLIT_DIR = Path(__file__).parent.parent / "cf" / "outputs" / "cf_split"

def load_recipes() -> pd.DataFrame:
    import pickle
    try:
        df = pd.read_csv(DATA_DIR / "RAW_recipes_cleaned.csv")
    except FileNotFoundError:
        df = pd.read_csv(DATA_DIR / "RAW_recipes.csv")
        
    try:
        with open(CF_SPLIT_DIR / "item2idx.pkl", "rb") as f:
            item2idx = pickle.load(f)
        df = df[df['id'].isin(item2idx.keys())].copy()
        df['cf_idx'] = df['id'].map(item2idx)
        df = df.sort_values('cf_idx').reset_index(drop=True)
    except Exception:
        pass
        
    return df

def extract_nutrition_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract components of the 'nutrition' array into distinct numeric columns.
    Expected format in RAW_recipes.csv 'nutrition' column:
    [calories (#), total fat (PDV), sugar (PDV), sodium (PDV), protein (PDV), saturated fat (PDV), carbohydrates (PDV)]
    """
    df = df.copy()
    
    if 'nutrition' not in df.columns:
        print("Warning: 'nutrition' column missing in DataFrame.")
        return df

    def parse_nutrition(val):
        if pd.isna(val):
            return [0.0] * 7
        if isinstance(val, list):
            return [float(x) for x in val]
        try:
            parsed = ast.literal_eval(val)
            return [float(x) for x in parsed]
        except (ValueError, SyntaxError):
            return [0.0] * 7

    # Parse column into list
    parsed_nutr_col = df['nutrition'].apply(parse_nutrition)
    
    # Expand list into separate columns
    nutr_cols = ['calories', 'total_fat_pdv', 'sugar_pdv', 'sodium_pdv', 
                 'protein_pdv', 'saturated_fat_pdv', 'carbohydrates_pdv']
    
    # We create a temporary DataFrame and join it back
    nutr_df = pd.DataFrame(parsed_nutr_col.tolist(), columns=nutr_cols, index=df.index)
    
    # Concat
    df = pd.concat([df, nutr_df], axis=1)
    return df

if __name__ == "__main__":
    print("Testing Nutrition Extraction...")
    df_raw = load_recipes()
    if not df_raw.empty:
        df_processed = extract_nutrition_features(df_raw.head(10))
        print("Nutrition features extracted successfully!")
        print(df_processed[['id', 'nutrition', 'calories', 'total_fat_pdv', 'sugar_pdv', 'sodium_pdv', 'protein_pdv']].head())
