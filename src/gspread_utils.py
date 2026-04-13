import pandas as pd
import gspread as gs
import time
from gspread.exceptions import APIError

from typing import List, Any, Tuple

from apis import init_gspread_api


def download_as_dataframe(spreadsheet, ws_name, table_name, max_retries=3, initial_backoff=1) -> Tuple[pd.DataFrame, List[Any]]:
    """
    Download a named range from Google Sheets with retry logic for transient API failures.
    
    Args:
        spreadsheet: gspread Spreadsheet object
        ws_name: worksheet name
        table_name: named range/table name
        max_retries: maximum number of retry attempts (default: 3)
        initial_backoff: initial backoff time in seconds (default: 1)
    
    Returns:
        Tuple of (DataFrame, header list)
    """
    worksheet = spreadsheet.worksheet(ws_name)
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            table = worksheet.get(table_name)
            break
        except APIError as e:
            if attempt == max_retries - 1:
                raise  # Re-raise on final attempt
            
            # Check if it's a retryable error (5xx or rate limit)
            error_code = int(str(e).split('[')[1].split(']')[0]) if '[' in str(e) else None
            if error_code and error_code >= 500:
                backoff_time = initial_backoff * (2 ** attempt)  # Exponential backoff
                print(f"API error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {backoff_time}s...")
                time.sleep(backoff_time)
            else:
                raise  # Don't retry on non-5xx errors
    df = pd.DataFrame(table[1:], columns=table[0])
    
    # Replace Google Sheets error values with empty strings
    df = df.replace('#N/A', '')
    df = df.replace('#DIV/0!', '')
    df = df.replace('#REF!', '')
    df = df.replace('#VALUE!', '')
    df = df.replace('#ERROR!', '')

    return df, table[0]


def upload_dataframe(spreadsheet: gs.Worksheet, ws_name, table_name, df: pd.DataFrame, header: List=None, max_retries=3, initial_backoff=1):
    """
    Upload a DataFrame to Google Sheets with retry logic for transient API failures.
    
    Args:
        spreadsheet: gspread Spreadsheet object
        ws_name: worksheet name
        table_name: named range/table name
        df: DataFrame to upload
        header: optional custom header row
        max_retries: maximum number of retry attempts (default: 3)
        initial_backoff: initial backoff time in seconds (default: 1)
    """
    worksheet = spreadsheet.worksheet(ws_name)
    table = df.values.tolist()

    print(header)

    if header is not None:
        table = [header] + table

    print(table)
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            worksheet.update(table_name, table)
            break
        except APIError as e:
            if attempt == max_retries - 1:
                raise  # Re-raise on final attempt
            
            # Check if it's a retryable error (5xx or rate limit)
            error_code = int(str(e).split('[')[1].split(']')[0]) if '[' in str(e) else None
            if error_code and error_code >= 500:
                backoff_time = initial_backoff * (2 ** attempt)  # Exponential backoff
                print(f"API error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {backoff_time}s...")
                time.sleep(backoff_time)
            else:
                raise  # Don't retry on non-5xx errors
