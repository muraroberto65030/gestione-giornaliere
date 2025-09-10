from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Area, Street, WorkOrder, CleaningMachine, PassagePlan
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
            messages.error(request, 'Invalid username or password.')
    
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
                return JsonResponse({'success': False, 'error': 'Missing file or cleaning machine'})
            
            cleaning_machine = CleaningMachine.objects.get(id=cleaning_machine_id)
            
            df = pd.read_excel(excel_file)
            
            required_columns = ['street_name', 'area_name', 'daily_passages']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return JsonResponse({
                    'success': False, 
                    'error': f'Missing columns: {", ".join(missing_columns)}'
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
