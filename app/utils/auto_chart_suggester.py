from app.models import CleanedDataset

def get_chart_suggestions(dataset: CleanedDataset):
    """
    Returns a list of chart suggestions based on dataset columns and stats.
    Rules:
       - 1 categorical + 1 numeric -> Bar chart
       - date column + numeric -> Line chart  
       - 2 numeric columns -> Scatter chart
       - 1 categorical with few unique values (<8) -> Pie chart
       - Multiple numeric columns -> suggest Correlation heatmap
    """
    suggestions = []
    
    health = dataset.health_report or {}
    numeric_cols = health.get('numeric_columns', [])
    categorical_cols = health.get('categorical_columns', [])
    date_cols = health.get('date_columns', [])
    
    stats = dataset.stats or {}
    
    # 1 categorical with few unique values (<8) -> Pie chart
    for cat in categorical_cols:
        col_stats = stats.get(cat, {})
        # Depending on describe() output, unique count is typically 'unique'
        unique_count = col_stats.get('unique', 0)
        
        # fallback if not in stats
        if not unique_count and dataset.rows:
            # this is a bit expensive if many rows, but safe if small
            pass
            
        if unique_count and unique_count > 0 and unique_count < 8:
            # Needs a numeric column to aggregate, or just count
            suggestions.append({
                'chart_type': 'pie',
                'x_col': cat,
                'y_col': cat,
                'agg_mode': 'count',
                'title': f'Distribution of {cat}',
                'reason': f'Categorical column with few unique values ({unique_count}).'
            })
            
    # 1 categorical + 1 numeric -> Bar chart
    if categorical_cols and numeric_cols:
        # Suggest top combination
        cat = categorical_cols[0]
        num = numeric_cols[0]
        suggestions.append({
            'chart_type': 'bar',
            'x_col': cat,
            'y_col': num,
            'agg_mode': 'sum',
            'title': f'Total {num} by {cat}',
            'reason': 'Good for comparing numeric values across categories.'
        })
        
    # date column + numeric -> Line chart
    if date_cols and numeric_cols:
        date_col = date_cols[0]
        num_col = numeric_cols[0]
        suggestions.append({
            'chart_type': 'line',
            'x_col': date_col,
            'y_col': num_col,
            'agg_mode': 'sum',
            'title': f'{num_col} over {date_col}',
            'reason': 'Time series data is best visualized with a line chart.'
        })
        
    # 2 numeric columns -> Scatter chart
    if len(numeric_cols) >= 2:
        num1 = numeric_cols[0]
        num2 = numeric_cols[1]
        suggestions.append({
            'chart_type': 'scatter',
            'x_col': num1,
            'y_col': num2,
            'agg_mode': 'none', # scatter doesn't necessarily need aggregation
            'title': f'{num1} vs {num2}',
            'reason': 'Scatter charts are great for identifying correlation between two numeric variables.'
        })
        
    # Multiple numeric columns -> Correlation heatmap
    if len(numeric_cols) >= 3:
        suggestions.append({
            'chart_type': 'heatmap',
            'x_col': ','.join(numeric_cols[:5]),
            'y_col': '',
            'agg_mode': 'correlation',
            'title': 'Correlation Heatmap',
            'reason': f'Found {len(numeric_cols)} numeric columns. A heatmap helps identify relationships.'
        })
        
    return suggestions
