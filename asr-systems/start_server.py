"""ASR Production Server - Direct Startup"""
import sys
import os
import importlib
from pathlib import Path

# Set up paths
root = Path(__file__).parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "shared"))

os.chdir(root)

# Register the hyphenated directory as a Python package with underscore name
import importlib.util

pkg_path = root / "production_server"
spec = importlib.util.spec_from_file_location(
    "production_server",
    str(pkg_path / "__init__.py"),
    submodule_search_locations=[str(pkg_path)]
)
production_server = importlib.util.module_from_spec(spec)
sys.modules["production_server"] = production_server

# Also register sub-packages before loading __init__
for sub_pkg in ["config", "api", "services", "middleware"]:
    sub_path = pkg_path / sub_pkg
    if sub_path.exists():
        sub_spec = importlib.util.spec_from_file_location(
            f"production_server.{sub_pkg}",
            str(sub_path / "__init__.py"),
            submodule_search_locations=[str(sub_path)]
        )
        sub_mod = importlib.util.module_from_spec(sub_spec)
        sys.modules[f"production_server.{sub_pkg}"] = sub_mod

# Now load the actual modules
if __name__ == "__main__":
    try:
        # Load production settings first
        settings_spec = importlib.util.spec_from_file_location(
            "production_server.config.production_settings",
            str(pkg_path / "config" / "production_settings.py")
        )
        settings_mod = importlib.util.module_from_spec(settings_spec)
        sys.modules["production_server.config.production_settings"] = settings_mod
        settings_spec.loader.exec_module(settings_mod)

        # Load middleware
        for mw_name in ["tenant_middleware", "rate_limit_middleware"]:
            mw_spec = importlib.util.spec_from_file_location(
                f"production_server.middleware.{mw_name}",
                str(pkg_path / "middleware" / f"{mw_name}.py")
            )
            mw_mod = importlib.util.module_from_spec(mw_spec)
            sys.modules[f"production_server.middleware.{mw_name}"] = mw_mod
            mw_spec.loader.exec_module(mw_mod)

        # Load services
        for svc_name in [
            "gl_account_service", "payment_detection_service",
            "billing_router_service", "document_processor_service",
            "storage_service", "scanner_manager_service"
        ]:
            svc_path = pkg_path / "services" / f"{svc_name}.py"
            if svc_path.exists():
                svc_spec = importlib.util.spec_from_file_location(
                    f"production_server.services.{svc_name}",
                    str(svc_path)
                )
                svc_mod = importlib.util.module_from_spec(svc_spec)
                sys.modules[f"production_server.services.{svc_name}"] = svc_mod
                svc_spec.loader.exec_module(svc_mod)

        # Load API main
        api_spec = importlib.util.spec_from_file_location(
            "production_server.api.main",
            str(pkg_path / "api" / "main.py")
        )
        api_mod = importlib.util.module_from_spec(api_spec)
        sys.modules["production_server.api.main"] = api_mod
        api_spec.loader.exec_module(api_mod)

        # Start uvicorn with the app
        import uvicorn
        app = api_mod.app

        port = int(os.environ.get("API_PORT", 8080))

        print("=" * 50)
        print("ASR Production Server Starting")
        print("=" * 50)
        print(f"Server: http://localhost:{port}")
        print(f"API Docs: http://localhost:{port}/docs")
        print(f"Health: http://localhost:{port}/health")
        print("=" * 50)

        uvicorn.run(app, host="0.0.0.0", port=port)

    except Exception as e:
        print(f"Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
