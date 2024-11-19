# services/database.py
from typing import Optional, Dict
import json
import csv
from pathlib import Path

# Get the base directory of your project
BASE_DIR = Path(__file__).resolve().parent.parent

def load_cpt_database() -> Dict:
    """Load CPT codes from text file"""
    cpt_codes = {}
    try:
        with open(BASE_DIR / "databases" / "cpt.txt", 'r') as file:
            for line in file:
                parts = line.strip().split(": ")
                if len(parts) == 2:
                    code, description = parts
                    cpt_codes[code] = {
                        "code": code,
                        "description": description
                    }
    except FileNotFoundError:
        print(f"Error: CPT database file not found")
    return cpt_codes

def load_medicare_database() -> Dict:
    """Load Medicare rates from CSV file"""
    medicare_rates = {}
    try:
        with open(BASE_DIR / "databases" / "medicare_rates.csv", 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                code = row['HCPCS Code']
                medicare_rates[code] = {
                    'code': code,
                    'apc': row['APC'],
                    'description': row['Description']
                }
    except FileNotFoundError:
        print(f"Error: Medicare rates database file not found")
    return medicare_rates

async def get_cpt_code(code: str) -> Optional[Dict]:
    """Get a specific CPT code information"""
    cpt_codes = load_cpt_database()
    return cpt_codes.get(code)

async def get_medicare_rate(code: str) -> Optional[Dict]:
    """Get a specific Medicare rate information"""
    medicare_rates = load_medicare_database()
    return medicare_rates.get(code)