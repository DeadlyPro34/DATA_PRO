from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import UploadedFile, CleanedDataset
from .utils.file_parser import parse_file
from .utils.data_cleaner import clean_dataframe
import json
import os

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'dashboard.html', {'files': files})

@login_required
def upload_file(request):
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'No file uploaded.')
            return redirect('upload_file')
            
        file = request.FILES['file']
        custom_name = request.POST.get('custom_name', '')
        
        # Create UploadedFile
        uploaded_file = UploadedFile.objects.create(
            user=request.user,
            original_filename=file.name,
            file_type=file.name.split('.')[-1].lower(),
            custom_name=custom_name,
            file=file
        )
        
        # Process file synchronously as requested
        try:
            df = parse_file(uploaded_file.file.path)
            cleaned_df, cleaning_log, stats = clean_dataframe(df)
            
            uploaded_file.row_count = len(cleaned_df)
            uploaded_file.column_count = len(cleaned_df.columns)
            uploaded_file.save()
            
            import json
            
            # Serialize safely via pandas to avoid NaN/Infinity JSON serialization errors in SQLite
            safe_rows = json.loads(cleaned_df.to_json(orient='records', date_format='iso'))
            # Some stats might have np floats
            safe_stats = json.loads(pd.Series(stats).to_json()) if stats else {}

            # Create Dataset
            CleanedDataset.objects.create(
                uploaded_file=uploaded_file,
                columns=list(cleaned_df.columns),
                rows=safe_rows,
                cleaning_log=cleaning_log,
                stats=safe_stats
            )
            
            messages.success(request, 'File uploaded and cleaned successfully!')
            return redirect('dataset_view', file_id=uploaded_file.id)
            
        except Exception as e:
            uploaded_file.delete()
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('upload_file')
            
    return render(request, 'upload.html')

@login_required
def dataset_view(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    dataset = get_object_or_404(CleanedDataset, uploaded_file=uploaded_file)
    
    context = {
        'file': uploaded_file,
        'dataset': dataset,
        # Safely dump lists to JSON strings for frontend JS
        'columns_json': json.dumps(dataset.columns),
        'rows_json': json.dumps(dataset.rows),
    }
    return render(request, 'dataset.html', context)

@login_required
def delete_dataset(request, file_id):
    if request.method == 'POST':
        uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        try:
            if uploaded_file.file and os.path.exists(uploaded_file.file.path):
                os.remove(uploaded_file.file.path)
        except Exception:
            pass
        uploaded_file.delete()
        messages.success(request, 'Dataset deleted successfully.')
    return redirect('dashboard')

