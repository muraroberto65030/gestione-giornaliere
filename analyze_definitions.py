#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestione_giornaliere.settings')
django.setup()

import pandas as pd

def analyze_definitions():
    print("Analyzing definitions.xlsx file structure...")
    
    try:
        excel_file = 'docs/in/definitions.xlsx'
        
        if not os.path.exists(excel_file):
            print(f"File not found: {excel_file}")
            return
            
        xl = pd.ExcelFile(excel_file)
        print(f"Found sheets: {xl.sheet_names}")
        
        # Analyze first sheet (area names)
        print(f"\n=== First Sheet: '{xl.sheet_names[0]}' (Area Names) ===")
        first_df = pd.read_excel(excel_file, sheet_name=xl.sheet_names[0], header=None)
        print(f"Shape: {first_df.shape}")
        print("Content:")
        for idx in range(min(10, len(first_df))):
            row_values = [str(val) if pd.notna(val) else 'NaN' for val in first_df.iloc[idx]]
            print(f"  Row {idx}: {row_values}")
        
        # Analyze area definition sheets
        for i, sheet_name in enumerate(xl.sheet_names[1:], 1):
            print(f"\n=== Sheet {i+1}: '{sheet_name}' (Area Definition) ===")
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            print(f"Shape: {df.shape}")
            
            # Look for "vie" row
            vie_row_idx = None
            for idx in range(len(df)):
                for col_idx in range(len(df.columns)):
                    cell_value = str(df.iloc[idx, col_idx]).strip().lower()
                    if 'vie' in cell_value:
                        vie_row_idx = idx
                        print(f"Found 'vie' at row {idx}, column {col_idx}: '{df.iloc[idx, col_idx]}'")
                        break
                if vie_row_idx is not None:
                    break
            
            # Show row 6 (cleaning operation types)
            if len(df) > 6:
                print(f"Row 6 (cleaning operations): {[str(val) if pd.notna(val) else 'NaN' for val in df.iloc[6]]}")
            
            # Show street names starting from vie+1
            if vie_row_idx is not None and vie_row_idx + 1 < len(df):
                print("Street names and operations:")
                for row_idx in range(vie_row_idx + 1, min(vie_row_idx + 11, len(df))):
                    street_name = str(df.iloc[row_idx, 0]).strip()
                    if street_name and street_name.lower() not in ['nan', 'none', '']:
                        # Show operations for this street
                        operations = []
                        for col_idx in range(1, min(10, len(df.columns))):
                            cell_value = df.iloc[row_idx, col_idx]
                            if pd.notna(cell_value) and str(cell_value).strip():
                                # Get operation type from row 6
                                if len(df) > 6:
                                    op_type = df.iloc[6, col_idx]
                                    operations.append(f"Col{col_idx}({op_type}): {cell_value}")
                        print(f"  {street_name}: {operations}")
            
            if i >= 2:  # Only show first 3 area sheets
                break
        
        print("Analysis completed!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analyze_definitions()