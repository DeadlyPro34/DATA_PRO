import io
import pandas as pd

def parse_file(file_obj, file_type):
    """
    Parses CSV, Excel, or JSON files into a Pandas DataFrame.
    file_obj: file-like object
    file_type: str ('csv', 'excel', or 'json')
    """
    file_type = file_type.lower()
    
    try:
        if file_type == 'csv':
            try:
                # Seek to start
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                content = file_obj.read()
                if isinstance(content, bytes):
                    try:
                        decoded = content.decode('utf-8')
                    except UnicodeDecodeError:
                        decoded = content.decode('latin-1')
                    file_io = io.StringIO(decoded)
                else:
                    file_io = io.StringIO(content)
                df = pd.read_csv(file_io)
            except Exception as e:
                raise ValueError(f"Failed to parse CSV: {str(e)}")
                
        elif file_type == 'excel':
            try:
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                # Excel file needs bytes representation
                content = file_obj.read()
                if isinstance(content, str):
                    # Should not normally happen for file uploads, but handle it
                    content = content.encode('utf-8')
                file_io = io.BytesIO(content)
                df = pd.read_excel(file_io)
            except Exception as e:
                raise ValueError(f"Failed to parse Excel: {str(e)}")
                
        elif file_type == 'json':
            try:
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                content = file_obj.read()
                if isinstance(content, bytes):
                    try:
                        decoded = content.decode('utf-8')
                    except UnicodeDecodeError:
                        decoded = content.decode('latin-1')
                    file_io = io.StringIO(decoded)
                else:
                    file_io = io.StringIO(content)
                df = pd.read_json(file_io)
            except Exception as e:
                raise ValueError(f"Failed to parse JSON: {str(e)}")
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        return df
    except Exception as e:
        if not isinstance(e, ValueError):
            raise ValueError(f"Error reading file: {str(e)}")
        raise e
