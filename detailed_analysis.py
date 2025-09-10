#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestione_giornaliere.settings')
django.setup()

import pandas as pd

def detailed_analysis():
    print("Detailed analysis of definitions.xlsx...")
    
    try:
        excel_file = 'docs/in/definitions.xlsx'
        xl = pd.ExcelFile(excel_file)
        
        # Analyze a specific area sheet in detail
        sheet_name = '167'  # First area sheet
        print(f"\n=== Detailed Analysis of '{sheet_name}' ===")
        
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        print(f"Shape: {df.shape}")
        
        # Show first 10 rows completely to understand structure
        print("\nFirst 10 rows (all columns):")
        for row_idx in range(min(10, len(df))):
            row_values = []
            for col_idx in range(len(df.columns)):
                val = df.iloc[row_idx, col_idx]
                if pd.notna(val):
                    row_values.append(f"Col{col_idx}: '{val}'")
            print(f"Row {row_idx}: {row_values}")
        
        # Look for cleaning operation headers
        print(f"\nLooking for cleaning operation types...")
        for row_idx in range(min(15, len(df))):
            for col_idx in range(len(df.columns)):
                cell_value = df.iloc[row_idx, col_idx]
                if pd.notna(cell_value):
                    cell_str = str(cell_value).strip()
                    if any(keyword in cell_str.lower() for keyword in ['spaz', 'lava', 'mecc', 'man', 'pass', 'freq']):
                        print(f"  Row {row_idx}, Col {col_idx}: '{cell_str}'")
        
        # Find VIE row and analyze what follows
        vie_row_idx = None
        for idx in range(len(df)):
            if str(df.iloc[idx, 0]).strip().upper() == 'VIE':
                vie_row_idx = idx
                break
        
        if vie_row_idx:
            print(f"\nFound VIE at row {vie_row_idx}")
            
            # Show the header row structure around VIE
            print(f"Rows around VIE ({vie_row_idx-3} to {vie_row_idx+2}):")
            for r in range(max(0, vie_row_idx-3), min(len(df), vie_row_idx+3)):
                non_empty_cells = []
                for c in range(min(15, len(df.columns))):
                    val = df.iloc[r, c]
                    if pd.notna(val) and str(val).strip():
                        non_empty_cells.append(f"Col{c}: '{val}'")
                if non_empty_cells:
                    print(f"  Row {r}: {non_empty_cells}")
            
            # Analyze streets and their operations
            print(f"\nStreets and operations (from row {vie_row_idx+1}):")
            for street_row in range(vie_row_idx + 1, min(vie_row_idx + 15, len(df))):
                street_name = df.iloc[street_row, 0]
                if pd.notna(street_name) and str(street_name).strip():
                    operations = {}
                    for col in range(1, min(15, len(df.columns))):
                        val = df.iloc[street_row, col]
                        if pd.notna(val) and str(val).strip():
                            operations[f"Col{col}"] = val
                    
                    if operations:
                        print(f"  {street_name}: {operations}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    detailed_analysis()