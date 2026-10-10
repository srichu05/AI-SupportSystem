#!/usr/bin/env python3
"""
CLI Database Connectivity Verification Script for Supabase PostgreSQL.
"""
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.core.config import settings
from backend.app.core.database import check_database_connectivity


def main():
    print("=" * 70)
    print("Intelligent Customer Complaint Response Assistant (PS-40)")
    print("Database Connectivity Check")
    print("=" * 70)

    print(f"\n- DATABASE_URL Configured: {'YES' if settings.is_database_configured else 'NO (Missing)'}")
    print(f"- Target Database: {settings.masked_database_url()}")

    result = check_database_connectivity()
    print(f"- Status: {result.get('status')}")
    print(f"- Connected: {result.get('connected')}")
    print(f"- Message: {result.get('message')}")

    print("=" * 70)
    if not result.get("connected"):
        if not settings.is_database_configured:
            print("[BLOCKER] DATABASE_URL is not set in .env. Configure Supabase PostgreSQL connection string.")
        else:
            print(f"[BLOCKER] Database connection failed: {result.get('message')}")
    else:
        print("[SUCCESS] Database is reachable and verified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
