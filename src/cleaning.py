"""Clean and validate historical Google Play Store app listings."""
import numpy as np
import pandas as pd


def parse_size_mb(value):
    """Convert values like '19M' and '201k' to megabytes; other values -> NaN."""
    if pd.isna(value):
        return np.nan
    value = str(value).strip().lower()
    if value in {'varies with device', '', 'nan'}:
        return np.nan
    try:
        if value.endswith('m'):
            return float(value[:-1])
        if value.endswith('k'):
            return float(value[:-1]) / 1024
    except ValueError:
        pass
    return np.nan


def clean_google_play(raw):
    """Return (clean DataFrame, cleaning audit dictionary)."""
    df = raw.copy()
    df.columns = df.columns.str.strip()
    original_rows = len(df)
    required = {'App','Category','Rating','Reviews','Size','Installs','Type','Price','Content Rating'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(sorted(missing)))

    # Remove rows whose category is a number (the known 2018 CSV shifted row).
    df['Category'] = df['Category'].astype('string').str.strip()
    malformed = df['Category'].str.fullmatch(r'\d+(?:\.\d+)?').fillna(False)
    malformed_count = int(malformed.sum())
    df = df.loc[~malformed].copy()
    empty_names = df['App'].isna() | df['App'].astype('string').str.strip().eq('')
    df = df.loc[~empty_names].copy()

    for col in ['App','Category','Type','Content Rating']:
        df[col] = df[col].astype('string').str.strip()
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    df.loc[~df['Rating'].between(1,5), 'Rating'] = np.nan
    df['Reviews_num'] = pd.to_numeric(df['Reviews'], errors='coerce')
    df['Installs_lower_bound'] = pd.to_numeric(
        df['Installs'].astype('string').str.replace(r'[, +]', '', regex=True), errors='coerce'
    )
    df['Price_usd'] = pd.to_numeric(
        df['Price'].astype('string').str.replace('$','',regex=False), errors='coerce'
    )
    df['Size_MB'] = df['Size'].map(parse_size_mb)
    if 'Last Updated' in df.columns:
        df['Last_Updated_date'] = pd.to_datetime(df['Last Updated'],errors='coerce')

    invalid = (df['Reviews_num'].lt(0) | df['Installs_lower_bound'].lt(0) | df['Price_usd'].lt(0)).fillna(False)
    df = df.loc[~invalid].copy()
    df = df.loc[df['Type'].isin(['Free','Paid'])].copy()
    # Highest review count is used to keep one snapshot per app name.
    df = df.sort_values('Reviews_num',ascending=False,na_position='last')
    duplicate_app_count = int(df.duplicated(subset=['App']).sum())
    df = df.drop_duplicates(subset=['App'], keep='first').reset_index(drop=True)
    audit = {'raw_rows':original_rows,'malformed_category_rows':malformed_count,
             'duplicate_app_names_removed':duplicate_app_count,
             'final_rows':len(df), 'missing_ratings':int(df['Rating'].isna().sum()),
             'missing_size_mb':int(df['Size_MB'].isna().sum())}
    return df,audit
