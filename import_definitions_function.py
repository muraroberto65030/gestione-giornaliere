@login_required
def import_area_definitions(request):
    """Import area definitions from Excel file with cleaning operation types"""
    if request.method == 'POST':
        try:
            import pandas as pd
            from datetime import date
            import re
            
            excel_file = request.FILES.get('excel_file')
            
            if not excel_file:
                return JsonResponse({'success': False, 'error': 'File mancante'})
            
            xl = pd.ExcelFile(excel_file)
            
            imported_areas = 0
            imported_streets = 0
            imported_operations = 0
            errors = []
            created_operation_types = []
            
            # Skip first sheet (QUADRO GENERALE) and process area definition sheets
            for sheet_name in xl.sheet_names[1:]:
                try:
                    print(f"Processing area sheet: {sheet_name}")
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                    
                    if df.empty or len(df) < 8:
                        errors.append(f"Foglio '{sheet_name}' troppo piccolo o vuoto")
                        continue
                    
                    # Create or get the area
                    area, area_created = Area.objects.get_or_create(
                        name=sheet_name,
                        defaults={'description': f'Area importata da {excel_file.name}'}
                    )
                    if area_created:
                        imported_areas += 1
                        print(f"Created area: {sheet_name}")
                    
                    # Look for cleaning operation types in the sheet
                    operation_types = {}
                    
                    # Find operation descriptions (usually around rows 5-6)
                    for row_idx in range(min(15, len(df))):
                        for col_idx in range(len(df.columns)):
                            cell_value = df.iloc[row_idx, col_idx]
                            if pd.notna(cell_value):
                                cell_str = str(cell_value).strip()
                                # Look for operation patterns like "Spazzamento meccanizzato (1/SETTIMANA)"
                                if 'spazzamento' in cell_str.lower() and 'settimana' in cell_str.lower():
                                    # Extract frequency
                                    freq_match = re.search(r'\((\d+)/SETTIMANA\)', cell_str.upper())
                                    frequency = int(freq_match.group(1)) if freq_match else 1
                                    
                                    # Create or get operation type
                                    op_type, op_created = CleaningOperationType.objects.get_or_create(
                                        name=cell_str,
                                        defaults={
                                            'description': f'Operazione importata da {sheet_name}',
                                            'frequency_per_week': frequency
                                        }
                                    )
                                    if op_created:
                                        created_operation_types.append(cell_str)
                                    
                                    operation_types[col_idx] = op_type
                                    print(f"Found operation type: {cell_str} at col {col_idx}")
                    
                    # If no specific operation types found, create a default one
                    if not operation_types:
                        default_op, op_created = CleaningOperationType.objects.get_or_create(
                            name="Spazzamento Standard",
                            defaults={'description': 'Operazione standard', 'frequency_per_week': 1}
                        )
                        if op_created:
                            created_operation_types.append("Spazzamento Standard")
                        operation_types[10] = default_op  # Default to column 10
                    
                    # Find the VIE row
                    vie_row_idx = None
                    for idx in range(len(df)):
                        if str(df.iloc[idx, 0]).strip().upper() == 'VIE':
                            vie_row_idx = idx
                            break
                    
                    if vie_row_idx is None:
                        errors.append(f"Riga VIE non trovata nel foglio '{sheet_name}'")
                        continue
                    
                    print(f"Found VIE at row {vie_row_idx}")
                    
                    # Extract year and month (usually in first few rows)
                    current_year = 2025  # Default year
                    current_month = 6    # Default month (June)
                    
                    for row_idx in range(min(5, len(df))):
                        for col_idx in range(len(df.columns)):
                            cell_value = df.iloc[row_idx, col_idx]
                            if pd.notna(cell_value):
                                cell_str = str(cell_value)
                                # Look for year
                                if cell_str.strip().isdigit() and len(cell_str) == 4:
                                    year_val = int(cell_str)
                                    if 2020 <= year_val <= 2030:
                                        current_year = year_val
                                elif cell_str.strip() in ['GIU', 'GIUGNO']:
                                    current_month = 6
                                elif cell_str.strip() in ['LUG', 'LUGLIO']:
                                    current_month = 7
                    
                    # Process streets starting from vie_row_idx + 1
                    for street_row_idx in range(vie_row_idx + 1, len(df)):
                        street_name = df.iloc[street_row_idx, 0]
                        
                        if pd.isna(street_name):
                            continue
                            
                        street_name = str(street_name).strip()
                        
                        if not street_name or street_name.upper() == 'VIE':
                            continue
                        
                        # Clean street name (remove asterisks and extra characters)
                        clean_street_name = re.sub(r'[*]+$', '', street_name).strip()
                        if not clean_street_name:
                            continue
                        
                        # Create or get the street
                        street, street_created = Street.objects.get_or_create(
                            name=clean_street_name,
                            area=area
                        )
                        if street_created:
                            imported_streets += 1
                        
                        # Process operations for this street
                        for col_idx in range(1, min(32, len(df.columns))):
                            cell_value = df.iloc[street_row_idx, col_idx]
                            
                            if pd.notna(cell_value) and str(cell_value).strip():
                                try:
                                    # Try to interpret as day of month
                                    day_of_month = int(float(str(cell_value).strip()))
                                    
                                    if 1 <= day_of_month <= 31:
                                        # Get operation type for this column
                                        op_type = operation_types.get(col_idx, list(operation_types.values())[0] if operation_types else None)
                                        
                                        if op_type:
                                            # Create street cleaning operation
                                            operation, created = StreetCleaningOperation.objects.get_or_create(
                                                street=street,
                                                operation_type=op_type,
                                                day_of_month=day_of_month,
                                                month=current_month,
                                                year=current_year
                                            )
                                            if created:
                                                imported_operations += 1
                                
                                except (ValueError, TypeError):
                                    continue
                
                except Exception as e:
                    errors.append(f"Errore nell'elaborazione del foglio '{sheet_name}': {str(e)}")
                    continue
            
            success_msg = f'Importate con successo {imported_areas} aree, {imported_streets} strade, {imported_operations} operazioni'
            if created_operation_types:
                success_msg += f'. Creati tipi operazione: {", ".join(created_operation_types[:3])}'
                if len(created_operation_types) > 3:
                    success_msg += f' e altri {len(created_operation_types) - 3}'
            
            if errors:
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'warnings': errors[:10]  # Limit to first 10 errors
                })
            
            return JsonResponse({
                'success': True,
                'message': success_msg
            })
            
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': 'La libreria pandas è richiesta per l\'importazione Excel. Installala.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Metodo di richiesta non valido'})