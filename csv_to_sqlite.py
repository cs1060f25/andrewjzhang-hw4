#!/usr/bin/env python3
"""
CSV to SQLite converter script.
Converts CSV files with header rows to SQLite database tables.
"""

import sys
import csv
import sqlite3
import os
from pathlib import Path


def csv_to_sqlite(db_name, csv_file):
    """
    Convert a CSV file to a SQLite table.
    
    Args:
        db_name (str): Name of the SQLite database file
        csv_file (str): Name of the CSV file to convert
    """
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found.")
        sys.exit(1)
    
    # Get table name from CSV filename (without extension)
    table_name = Path(csv_file).stem
    
    try:
        # Connect to SQLite database (creates if doesn't exist)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Open and read CSV file
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Try to detect delimiter, with fallbacks
            sample = file.read(1024)
            file.seek(0)
            
            delimiter = ','  # Default to comma
            try:
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
            except csv.Error:
                # If sniffer fails, try common delimiters
                common_delimiters = [',', '\t', ';', '|']
                delimiter_counts = {}
                
                for delim in common_delimiters:
                    delimiter_counts[delim] = sample.count(delim)
                
                # Use the delimiter that appears most frequently
                if delimiter_counts:
                    delimiter = max(delimiter_counts, key=delimiter_counts.get)
                    if delimiter_counts[delimiter] == 0:
                        delimiter = ','  # Fall back to comma if no delimiters found
            
            # Create CSV reader
            csv_reader = csv.reader(file, delimiter=delimiter)
            
            # Get header row (column names)
            headers = next(csv_reader)
            
            # Clean headers to be valid SQL column names
            clean_headers = []
            for header in headers:
                # Replace spaces and special characters with underscores
                clean_header = ''.join(c if c.isalnum() else '_' for c in header)
                # Ensure it doesn't start with a number
                if clean_header and clean_header[0].isdigit():
                    clean_header = 'col_' + clean_header
                # Ensure it's not empty
                if not clean_header:
                    clean_header = f'column_{len(clean_headers)}'
                clean_headers.append(clean_header)
            
            # Drop table if it exists
            cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
            
            # Create table with all columns as TEXT type
            columns_def = ', '.join([f'{col} TEXT' for col in clean_headers])
            create_table_sql = f'CREATE TABLE {table_name} ({columns_def})'
            cursor.execute(create_table_sql)
            
            # Prepare insert statement
            placeholders = ', '.join(['?' for _ in clean_headers])
            insert_sql = f'INSERT INTO {table_name} VALUES ({placeholders})'
            
            # Insert data rows
            rows_inserted = 0
            for row in csv_reader:
                # Pad row with empty strings if it has fewer columns than headers
                while len(row) < len(clean_headers):
                    row.append('')
                # Truncate row if it has more columns than headers
                row = row[:len(clean_headers)]
                
                cursor.execute(insert_sql, row)
                rows_inserted += 1
            
            # Commit changes
            conn.commit()
            print(f"Successfully imported {rows_inserted} rows into table '{table_name}' in database '{db_name}'")
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        sys.exit(1)
    except csv.Error as e:
        print(f"CSV error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 3:
        print("Usage: python3 csv_to_sqlite.py <database_name> <csv_file>")
        print("Example: python3 csv_to_sqlite.py data.db zip_county.csv")
        sys.exit(1)
    
    db_name = sys.argv[1]
    csv_file = sys.argv[2]
    
    csv_to_sqlite(db_name, csv_file)


if __name__ == "__main__":
    main()