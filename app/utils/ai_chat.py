import json
import pandas as pd
import re
from .data_cleaner import _to_json_safe

def process_chat_query(query: str, dataset) -> dict:
    """
    Process a natural language query against the dataset.
    Since we don't have an LLM attached, we use robust regex heuristics to
    answer common dataset questions.
    """
    df = pd.DataFrame(dataset.rows)
    query = query.lower()
    
    if df.empty:
        return {"answer": "The dataset is empty, I cannot answer questions about it."}
    
    # Heuristic 0: Group By (e.g. "average salary by department")
    # match pattern: (average|sum|max|min|count) [col1] by [col2]
    match = re.search(r'(average|mean|sum|total|highest|max|lowest|min|count)\s+([a-zA-Z0-9_\s]+)\s+by\s+([a-zA-Z0-9_\s]+)', query)
    if match:
        metric = match.group(1)
        val_term = match.group(2)
        group_term = match.group(3)
        
        val_col = _find_best_column(df, val_term)
        group_col = _find_best_column(df, group_term)
        
        if val_col and group_col and val_col != group_col:
            if metric in ['count']:
                res = df.groupby(group_col).size().reset_index(name='count').sort_values('count', ascending=False).head(5)
                res_str = ", ".join([f"**{r[group_col]}**: {r['count']}" for _, r in res.iterrows()])
                return {"answer": f"Top 5 counts of records by **{group_col}**:\n{res_str}"}
            elif pd.api.types.is_numeric_dtype(df[val_col]):
                if metric in ['average', 'mean']:
                    res = df.groupby(group_col)[val_col].mean().reset_index().sort_values(val_col, ascending=False).head(5)
                elif metric in ['sum', 'total']:
                    res = df.groupby(group_col)[val_col].sum().reset_index().sort_values(val_col, ascending=False).head(5)
                elif metric in ['highest', 'max']:
                    res = df.groupby(group_col)[val_col].max().reset_index().sort_values(val_col, ascending=False).head(5)
                elif metric in ['lowest', 'min']:
                    res = df.groupby(group_col)[val_col].min().reset_index().sort_values(val_col, ascending=True).head(5)
                
                res_str = ", ".join([f"**{r[group_col]}**: {_to_json_safe(round(r[val_col], 2) if isinstance(r[val_col], float) else r[val_col])}" for _, r in res.iterrows()])
                return {"answer": f"Top 5 {metric} **{val_col}** by **{group_col}**:\n{res_str}"}

    # Heuristic 1: "Highest/Max [Column]"
    match = re.search(r'(highest|max|maximum|top)\s+([a-zA-Z0-9_\s]+)', query)
    if match:
        col = _find_best_column(df, match.group(2))
        if col and pd.api.types.is_numeric_dtype(df[col]):
            max_idx = df[col].idxmax()
            max_val = df.loc[max_idx, col]
            
            label_col = _find_label_column(df, exclude=col)
            if label_col:
                label_val = df.loc[max_idx, label_col]
                return {"answer": f"The highest **{col}** is **{_to_json_safe(max_val)}**, belonging to **{label_val}** ({label_col})."}
            else:
                return {"answer": f"The highest **{col}** is **{_to_json_safe(max_val)}**."}

    # Heuristic 2: "Lowest/Min [Column]"
    match = re.search(r'(lowest|min|minimum|bottom)\s+([a-zA-Z0-9_\s]+)', query)
    if match:
        col = _find_best_column(df, match.group(2))
        if col and pd.api.types.is_numeric_dtype(df[col]):
            min_idx = df[col].idxmin()
            min_val = df.loc[min_idx, col]
            
            label_col = _find_label_column(df, exclude=col)
            if label_col:
                label_val = df.loc[min_idx, label_col]
                return {"answer": f"The lowest **{col}** is **{_to_json_safe(min_val)}**, belonging to **{label_val}** ({label_col})."}
            else:
                return {"answer": f"The lowest **{col}** is **{_to_json_safe(min_val)}**."}

    # Heuristic 3: "Average/Mean/Median [Column]"
    match = re.search(r'(average|mean|median)\s+([a-zA-Z0-9_\s]+)', query)
    if match:
        metric = match.group(1)
        col = _find_best_column(df, match.group(2))
        if col and pd.api.types.is_numeric_dtype(df[col]):
            if metric == 'median':
                val = df[col].median()
            else:
                val = df[col].mean()
            return {"answer": f"The {metric} **{col}** is **{_to_json_safe(round(val, 2))}**."}

    # Heuristic 4: "Sum/Total [Column]"
    match = re.search(r'(sum|total)\s+([a-zA-Z0-9_\s]+)', query)
    if match:
        col = _find_best_column(df, match.group(2))
        if col and pd.api.types.is_numeric_dtype(df[col]):
            val = df[col].sum()
            return {"answer": f"The total sum of **{col}** is **{_to_json_safe(round(val, 2) if isinstance(val, float) else val)}**."}

    # Heuristic 5: "Unique [Column]"
    match = re.search(r'(unique|distinct)\s+([a-zA-Z0-9_\s]+)', query)
    if match:
        col = _find_best_column(df, match.group(2))
        if col:
            unique_count = df[col].nunique()
            top_vals = df[col].value_counts().head(3).index.tolist()
            top_str = ", ".join(map(str, top_vals))
            return {"answer": f"There are **{unique_count}** unique values in **{col}**. Some examples are: {top_str}."}

    # Heuristic 6: "Count/How many [Rows/Students/etc]"
    match = re.search(r'(how many|count)', query)
    if match:
        return {"answer": f"There are **{len(df)}** records in this dataset."}

    # Fallback
    return {
        "answer": "I'm sorry, my heuristic engine couldn't understand that query. Try asking things like:\n- 'Average salary by department'\n- 'Total revenue'\n- 'Who has the highest marks?'\n- 'Unique cities'"
    }

def _find_best_column(df: pd.DataFrame, search_term: str) -> str:
    """Finds the column that best matches the search term."""
    search_term = search_term.strip().replace('of', '').replace('the', '').strip()
    columns = list(df.columns)
    
    # Exact match
    for col in columns:
        if col.lower() == search_term:
            return col
            
    # Partial match
    for col in columns:
        if search_term in col.lower() or col.lower() in search_term:
            return col
            
    # Fallback heuristic: just return the first numeric column if the term implies numeric
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        return numeric_cols[0]
        
    return None

def _find_label_column(df: pd.DataFrame, exclude: str = None) -> str:
    """Finds a column suitable for labeling rows (e.g. Name, ID)."""
    candidates = ['student_name', 'name', 'student', 'employee', 'title', 'id', 'email', 'company', 'product', 'item']
    for cand in candidates:
        for col in df.columns:
            if col != exclude and cand in col.lower():
                return col
                
    # Fallback: first object/string column
    non_numeric = df.select_dtypes(exclude='number').columns
    if len(non_numeric) > 0:
        for col in non_numeric:
            if col != exclude:
                return col
                
    return None
