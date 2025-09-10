from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Area, Street, WorkOrder, CleaningMachine, PassagePlan, CleaningOperationType, StreetCleaningOperation
import json


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Nome utente o password non validi.')
    
    return render(request, 'main/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    areas = Area.objects.all()
    cleaning_machines = CleaningMachine.objects.all()
    
    context = {
        'areas': areas,
        'cleaning_machines': cleaning_machines,
    }
    return render(request, 'main/dashboard.html', context)


@login_required
def area_view(request, area_id, view_type='monthly'):
    area = Area.objects.get(id=area_id)
    streets = area.streets.all()
    
    if view_type == 'weekly':
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date()
    else:
        start_date = datetime.now().date().replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year+1, month=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month+1) - timedelta(days=1)
    
    work_orders = WorkOrder.objects.filter(
        street__area=area,
        date__range=[start_date, end_date]
    ).select_related('street', 'cleaning_machine')
    
    context = {
        'area': area,
        'streets': streets,
        'work_orders': work_orders,
        'view_type': view_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'main/area_view.html', context)


@login_required
def import_streets(request):
    if request.method == 'POST':
        try:
            import pandas as pd
            from datetime import date
            
            excel_file = request.FILES.get('excel_file')
            cleaning_machine_id = request.POST.get('cleaning_machine')
            
            if not excel_file or not cleaning_machine_id:
                return JsonResponse({'success': False, 'error': 'File o macchina spazzatrice mancanti'})
            
            cleaning_machine = CleaningMachine.objects.get(id=cleaning_machine_id)
            
            df = pd.read_excel(excel_file)
            
            required_columns = ['street_name', 'area_name', 'daily_passages']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return JsonResponse({
                    'success': False, 
                    'error': f'Colonne mancanti: {", ".join(missing_columns)}'
                })
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    area, created = Area.objects.get_or_create(
                        name=str(row['area_name']).strip()
                    )
                    
                    street, created = Street.objects.get_or_create(
                        name=str(row['street_name']).strip(),
                        area=area
                    )
                    
                    work_order, created = WorkOrder.objects.get_or_create(
                        street=street,
                        cleaning_machine=cleaning_machine,
                        date=date.today(),
                        defaults={
                            'daily_passages': int(row['daily_passages']),
                            'created_by': request.user
                        }
                    )
                    
                    if not created:
                        work_order.daily_passages = int(row['daily_passages'])
                        work_order.save()
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            if errors:
                return JsonResponse({
                    'success': False,
                    'error': f'Imported {imported_count} records with errors: {"; ".join(errors[:5])}'
                })
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully imported {imported_count} work orders'
            })
            
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': 'pandas library is required for Excel import. Please install it.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def import_areas(request):
    if request.method == 'POST':
        try:
            import pandas as pd
            
            excel_file = request.FILES.get('excel_file')
            
            if not excel_file:
                return JsonResponse({'success': False, 'error': 'Missing file'})
            
            df = pd.read_excel(excel_file)
            
            required_columns = ['area_name', 'street_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing columns: {", ".join(missing_columns)}'
                })
            
            imported_areas = 0
            imported_streets = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    area_name = str(row['area_name']).strip()
                    street_name = str(row['street_name']).strip()
                    
                    if not area_name or not street_name:
                        continue
                    
                    area, area_created = Area.objects.get_or_create(name=area_name)
                    if area_created:
                        imported_areas += 1
                    
                    street, street_created = Street.objects.get_or_create(
                        name=street_name,
                        area=area
                    )
                    if street_created:
                        imported_streets += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            if errors:
                return JsonResponse({
                    'success': False,
                    'error': f'Imported {imported_areas} areas and {imported_streets} streets with errors: {"; ".join(errors[:5])}'
                })
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully imported {imported_areas} areas and {imported_streets} streets'
            })
            
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': 'pandas library is required for Excel import. Please install it.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def import_daily_activities(request):
    """Import daily activities from Excel file with Italian format"""
    if request.method == 'POST':
        try:
            import pandas as pd
            from datetime import date, datetime
            import re
            
            excel_file = request.FILES.get('excel_file')
            
            if not excel_file:
                return JsonResponse({'success': False, 'error': 'Missing file'})
            
            xl = pd.ExcelFile(excel_file)
            
            imported_count = 0
            errors = []
            created_machines = []
            
            # Process each sheet (one per cleaning machine)
            for sheet_name in xl.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                    
                    if df.empty or len(df) < 4:
                        errors.append(f"Sheet '{sheet_name}' is too small or empty")
                        continue
                    
                    # Extract month/year from row 0 (e.g., "LUGLIO 2025")
                    month_year_cell = str(df.iloc[0, 0]).strip()
                    month_match = re.search(r'(\w+)\s+(\d{4})', month_year_cell)
                    
                    if not month_match:
                        errors.append(f"Could not parse month/year from '{month_year_cell}' in sheet '{sheet_name}'")
                        continue
                    
                    month_name = month_match.group(1)
                    year = int(month_match.group(2))
                    
                    # Convert Italian month names to numbers
                    italian_months = {
                        'GENNAIO': 1, 'FEBBRAIO': 2, 'MARZO': 3, 'APRILE': 4, 'MAGGIO': 5, 'GIUGNO': 6,
                        'LUGLIO': 7, 'AGOSTO': 8, 'SETTEMBRE': 9, 'OTTOBRE': 10, 'NOVEMBRE': 11, 'DICEMBRE': 12
                    }
                    
                    month_num = italian_months.get(month_name.upper())
                    if not month_num:
                        errors.append(f"Unknown month name '{month_name}' in sheet '{sheet_name}'")
                        continue
                    
                    # Extract cleaning machine name from row 1
                    machine_name = str(df.iloc[1, 0]).strip()
                    
                    # Get or create the cleaning machine
                    machine, created = CleaningMachine.objects.get_or_create(
                        name=machine_name,
                        defaults={'description': f'Imported from {excel_file.name}'}
                    )
                    
                    if created:
                        created_machines.append(machine_name)
                    
                    # Find the day numbers row (row 2) - look for numeric values
                    day_row = df.iloc[2]
                    
                    # Find which columns contain day numbers
                    day_columns = {}
                    for col_idx, value in enumerate(day_row):
                        if pd.notna(value):
                            try:
                                day_num = int(float(str(value).strip()))
                                if 1 <= day_num <= 31:
                                    day_columns[col_idx] = day_num
                            except (ValueError, TypeError):
                                continue
                    
                    if not day_columns:
                        errors.append(f"No valid day numbers found in sheet '{sheet_name}'")
                        continue
                    
                    # Default area for streets without specific area assignment
                    default_area, _ = Area.objects.get_or_create(
                        name=f"Area {machine_name}",
                        defaults={'description': f'Default area for {machine_name}'}
                    )
                    
                    # Process street data starting from row 3
                    for row_idx in range(3, len(df)):
                        street_name = str(df.iloc[row_idx, 0]).strip()
                        
                        if not street_name or street_name.lower() in ['nan', 'none', '']:
                            continue
                        
                        # Get or create the street
                        street, _ = Street.objects.get_or_create(
                            name=street_name,
                            area=default_area
                        )
                        
                        # Process each day's passages
                        for col_idx, day_num in day_columns.items():
                            try:
                                work_date = date(year, month_num, day_num)
                                passage_value = df.iloc[row_idx, col_idx]
                                
                                # Skip if no passage data
                                if pd.isna(passage_value) or str(passage_value).strip() == '':
                                    continue
                                
                                # Convert passage value to integer
                                passages = int(float(str(passage_value).strip()))
                                
                                if passages > 0:
                                    # Create or update work order
                                    work_order, created = WorkOrder.objects.get_or_create(
                                        street=street,
                                        cleaning_machine=machine,
                                        date=work_date,
                                        defaults={
                                            'daily_passages': passages,
                                            'created_by': request.user
                                        }
                                    )
                                    
                                    if not created:
                                        work_order.daily_passages = passages
                                        work_order.save()
                                    
                                    imported_count += 1
                                    
                            except (ValueError, TypeError, OverflowError) as e:
                                continue
                            except Exception as e:
                                errors.append(f"Error processing {street_name} on day {day_num}: {str(e)}")
                                continue
                
                except Exception as e:
                    errors.append(f"Error processing sheet '{sheet_name}': {str(e)}")
                    continue
            
            success_msg = f'Importati con successo {imported_count} ordini di lavoro'
            if created_machines:
                success_msg += f'. Create nuove macchine: {", ".join(created_machines)}'
            
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
                'error': 'pandas library is required for Excel import. Please install it.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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