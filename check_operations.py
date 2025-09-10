#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestione_giornaliere.settings')
django.setup()

import pandas as pd

def check_operations():
    print("Checking cleaning operations across all area sheets...")
    
    try:
        excel_file = 'docs/in/definitions.xlsx'
        xl = pd.ExcelFile(excel_file)
        
        # Skip first sheet (QUADRO GENERALE) and check area sheets
        for sheet_name in xl.sheet_names[1:6]:  # Check first 5 area sheets
            print(f"\n=== {sheet_name} ===")
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            
            # Look for cleaning operation descriptions
            operations_found = []
            for row_idx in range(min(15, len(df))):
                for col_idx in range(len(df.columns)):
                    cell_value = df.iloc[row_idx, col_idx]
                    if pd.notna(cell_value):
                        cell_str = str(cell_value).strip()
                        # Look for operation keywords
                        if any(keyword in cell_str.lower() for keyword in ['spazzamento', 'lavaggio', 'meccaniz', 'manual']):
                            operations_found.append(f"Row {row_idx}, Col {col_idx}: '{cell_str}'")
            
            if operations_found:
                print("Operations found:")
                for op in operations_found:
                    print(f"  {op}")
            else:
                print("No explicit operations found")
            
            # Find VIE row and show structure
            for idx in range(len(df)):
                if str(df.iloc[idx, 0]).strip().upper() == 'VIE':
                    print(f"VIE found at row {idx}")
                    
                    # Sample a few streets
                    print("Sample streets:")
                    for street_row in range(idx + 1, min(idx + 6, len(df))):
                        street_name = df.iloc[street_row, 0]
                        if pd.notna(street_name) and str(street_name).strip():
                            # Count operations
                            op_count = 0
                            for col in range(1, min(32, len(df.columns))):
                                val = df.iloc[street_row, col]
                                if pd.notna(val) and str(val).strip():
                                    op_count += 1
                            print(f"  {street_name}: {op_count} operations")
                    break
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_operations()