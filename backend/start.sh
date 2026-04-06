#!/usr/bin/env bash
# Startup diagnostic — prints exact error to deploy log, then starts uvicorn.
set -e

echo "===== STARTUP DIAGNOSTIC ====="
echo "Python: $(python --version 2>&1)"
echo "Working dir: $(pwd)"
echo "PORT: ${PORT:-NOT SET}"
echo "SUPABASE_URL set: $([ -n "$SUPABASE_URL" ] && echo YES || echo NO)"
echo "SUPABASE_KEY set: $([ -n "$SUPABASE_KEY" ] && echo YES || echo NO)"
echo "SUPABASE_SERVICE_KEY set: $([ -n "$SUPABASE_SERVICE_KEY" ] && echo YES || echo NO)"
echo "JWT_SECRET_KEY set: $([ -n "$JWT_SECRET_KEY" ] && echo YES || echo NO)"
echo "ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-not set}"

echo ""
echo "--- Testing app import ---"
python - <<'EOF'
import sys, traceback
try:
    from app.config import get_settings
    s = get_settings()
    print(f"Config OK  |  SUPABASE_URL={s.SUPABASE_URL[:30]}...")
except Exception as e:
    print(f"CONFIG ERROR: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

try:
    from app.main import app
    print("App import OK")
except Exception as e:
    print(f"APP IMPORT ERROR: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

print("All checks passed — starting uvicorn")
EOF

echo "===== STARTING UVICORN ====="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
