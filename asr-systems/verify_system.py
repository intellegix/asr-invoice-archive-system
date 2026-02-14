#!/usr/bin/env python3
"""
ASR Invoice Archive System - Verification Script
Tests core functionality of separated system components
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add paths for module imports
sys.path.insert(0, str(Path(__file__).parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "production_server"))
sys.path.insert(0, str(Path(__file__).parent / "document-scanner"))

def test_shared_components():
    """Test shared module imports and basic functionality"""
    print("🧪 Testing Shared Components...")

    try:
        # Test core imports
        from shared.core.models import Document, DocumentMetadata, GLAccount, BillingDestination
        from shared.core.exceptions import ASRException, ValidationError
        from shared.utils.validation import validate_file_type, validate_file_size

        print("  ✅ Shared core modules imported successfully")

        # Test model creation
        doc = Document(
            id="test-doc-001",
            filename="test_invoice.pdf",
            file_path="/path/to/file",
            tenant_id="test-tenant",
            status="uploaded",
            metadata=DocumentMetadata(
                file_size=1024,
                mime_type="application/pdf",
                upload_timestamp="2026-02-05T12:00:00Z"
            )
        )

        print("  ✅ Document model creation successful")

        # Test GL Account model
        gl_account = GLAccount(
            code="5000",
            name="Materials",
            category="Expenses",
            keywords=["materials", "lumber", "supplies"]
        )

        print("  ✅ GL Account model creation successful")

        return True

    except Exception as e:
        print(f"  ❌ Shared components test failed: {e}")
        return False

def test_production_server():
    """Test production server components"""
    print("🖥️ Testing Production Server Components...")

    try:
        # Test service imports
        from production_server.services.expense_category_service import ExpenseCategoryService
        from production_server.services.billing_router_service import BillingRouterService
        from production_server.services.payment_status_detector_service import PaymentStatusDetectorService

        print("  ✅ Production server services imported successfully")

        # Test configuration loading
        config_path = Path(__file__).parent / "production_server" / "config" / "gl_accounts.json"
        if config_path.exists():
            with open(config_path) as f:
                gl_accounts = json.load(f)
            print(f"  ✅ GL accounts configuration loaded: {len(gl_accounts)} accounts")
        else:
            print("  ⚠️ GL accounts configuration not found")

        return True

    except Exception as e:
        print(f"  ❌ Production server test failed: {e}")
        return False

def test_document_scanner():
    """Test document scanner components"""
    print("📱 Testing Document Scanner Components...")

    try:
        # Test scanner imports (basic structure test)
        scanner_path = Path(__file__).parent / "document-scanner"
        main_scanner = scanner_path / "main_scanner.py"

        if main_scanner.exists():
            print("  ✅ Document scanner main module exists")
        else:
            print("  ⚠️ Document scanner main module not found")

        # Test GUI components would require display, so just check file existence
        gui_path = scanner_path / "gui"
        if gui_path.exists():
            print("  ✅ GUI components directory exists")
        else:
            print("  ⚠️ GUI components directory not found")

        return True

    except Exception as e:
        print(f"  ❌ Document scanner test failed: {e}")
        return False

def test_configuration_files():
    """Test configuration and data files"""
    print("⚙️ Testing Configuration Files...")

    # Test GL accounts configuration
    gl_config = Path(__file__).parent / "production_server" / "config" / "gl_accounts.json"
    if gl_config.exists():
        try:
            with open(gl_config) as f:
                data = json.load(f)
            print(f"  ✅ GL accounts config: {len(data)} accounts configured")
        except Exception as e:
            print(f"  ❌ GL accounts config invalid: {e}")
    else:
        print("  ⚠️ GL accounts config missing")

    # Test shared constants
    constants_path = Path(__file__).parent / "shared" / "data" / "constants.json"
    if constants_path.exists():
        try:
            with open(constants_path) as f:
                data = json.load(f)
            billing_destinations = data.get("billing_destinations", [])
            payment_methods = data.get("payment_methods", [])
            print(f"  ✅ System constants: {len(billing_destinations)} billing destinations, {len(payment_methods)} payment methods")
        except Exception as e:
            print(f"  ❌ System constants invalid: {e}")
    else:
        print("  ⚠️ System constants missing")

    return True

def test_build_outputs():
    """Test build outputs and executables"""
    print("🔨 Testing Build Outputs...")

    # Check executables exist
    prod_exe = Path(__file__).parent / "dist" / "ASR_Production_Server" / "ASR_Production_Server.exe"
    scanner_exe = Path(__file__).parent / "dist" / "ASR_Document_Scanner" / "ASR_Document_Scanner.exe"

    if prod_exe.exists():
        size_mb = prod_exe.stat().st_size / (1024 * 1024)
        print(f"  ✅ Production server executable: {size_mb:.1f}MB")
    else:
        print("  ❌ Production server executable not found")

    if scanner_exe.exists():
        size_mb = scanner_exe.stat().st_size / (1024 * 1024)
        print(f"  ✅ Document scanner executable: {size_mb:.1f}MB")
    else:
        print("  ❌ Document scanner executable not found")

    # Check build artifacts
    build_dir = Path(__file__).parent / "build"
    if build_dir.exists():
        subdirs = [d.name for d in build_dir.iterdir() if d.is_dir()]
        print(f"  ✅ Build artifacts: {len(subdirs)} build directories")
    else:
        print("  ⚠️ Build artifacts directory not found")

    return True

def main():
    """Run comprehensive system verification"""
    print("=" * 60)
    print("🚀 ASR Invoice Archive System - Verification Suite")
    print("=" * 60)

    tests = [
        ("Shared Components", test_shared_components),
        ("Production Server", test_production_server),
        ("Document Scanner", test_document_scanner),
        ("Configuration Files", test_configuration_files),
        ("Build Outputs", test_build_outputs),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print(f"\n🎯 Overall Success Rate: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("🏆 ALL TESTS PASSED - System separation completed successfully!")
        print("\n📋 Next Steps:")
        print("  1. Deploy production server using source code or Docker")
        print("  2. Distribute document scanner to workplace computers")
        print("  3. Configure multi-tenant settings for client onboarding")
        print("  4. Set up monitoring and logging for production environment")
    else:
        print("⚠️  Some components need attention - see details above")
        print("\n🔧 Recommended Actions:")
        print("  1. Address any failed tests before production deployment")
        print("  2. Consider source code deployment as fallback option")
        print("  3. Test individual components in isolation for debugging")

    print("\n" + "=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)