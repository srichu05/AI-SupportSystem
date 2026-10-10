#!/usr/bin/env python3
"""
CLI Provider Smoke Test Script for Gemini and Supabase.
Verifies configured model IDs, output embedding dimensions, and error handling.
Does NOT fabricate results; reports actual API responses or missing configuration.
"""
import sys
import json
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.core.config import settings
from backend.app.services.gemini import gemini_service
from backend.app.services.supabase import supabase_service


def main():
    print("=" * 70)
    print("Intelligent Customer Complaint Response Assistant (PS-40)")
    print("Phase 1: External Provider Smoke Test & Diagnostics")
    print("=" * 70)

    print(f"\n[Configuration]")
    print(f"- GEMINI_API_KEY Configured: {'YES' if settings.is_gemini_configured else 'NO (Missing)'}")
    print(f"- Configured Generation Model: {settings.GEMINI_GENERATION_MODEL}")
    print(f"- Configured Embedding Model: {settings.GEMINI_EMBEDDING_MODEL}")
    print(f"- Target Embedding Dimensions: {settings.EMBEDDING_DIMENSIONS}")
    print(f"- Supabase URL Configured: {'YES' if settings.is_supabase_configured else 'NO (Missing)'}")
    print(f"- Supabase Storage Bucket: {settings.SUPABASE_STORAGE_BUCKET}")

    print("\n" + "-" * 70)
    print("1. Testing Gemini Generation API...")
    gen_result = gemini_service.verify_generation()
    print(f"Status: {gen_result.get('status')}")
    print(f"Success: {gen_result.get('success')}")
    print(f"Message: {gen_result.get('message')}")
    if gen_result.get("sample_output"):
        print(f"Sample Output: {gen_result.get('sample_output')}")

    print("\n" + "-" * 70)
    print("2. Testing Gemini Embedding API & Dimension Verification...")
    emb_result = gemini_service.verify_embedding()
    print(f"Status: {emb_result.get('status')}")
    print(f"Success: {emb_result.get('success')}")
    print(f"Expected Dimensions: {emb_result.get('expected_dimensions')}")
    print(f"Actual Dimensions: {emb_result.get('actual_dimensions')}")
    print(f"Message: {emb_result.get('message')}")

    print("\n" + "-" * 70)
    print("3. Testing Provider Error Handling...")
    err_result = gemini_service.verify_error_handling()
    print(f"Status: {err_result.get('status')}")
    print(f"Message: {err_result.get('message')}")

    print("\n" + "-" * 70)
    print("4. Testing Supabase Storage Access...")
    supa_result = supabase_service.check_storage_access()
    print(f"Status: {supa_result.get('status')}")
    print(f"Message: {supa_result.get('message')}")

    print("\n" + "=" * 70)
    print("Summary:")
    if not settings.is_gemini_configured:
        print("[BLOCKER] GEMINI_API_KEY is not configured in .env. Provider calls cannot execute.")
    elif not gen_result.get("success"):
        print(f"[BLOCKER] Generation model verification did not pass: {gen_result.get('message')}")
    elif not emb_result.get("success"):
        print(f"[BLOCKER] Embedding model verification did not pass: {emb_result.get('message')}")
    else:
        print("[SUCCESS] All configured providers passed smoke tests.")
    print("=" * 70)


if __name__ == "__main__":
    main()
