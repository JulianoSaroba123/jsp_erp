#!/bin/bash
# =============================================================================
# Render Release Script - Migrations Pre-Deploy
# =============================================================================
# Executado automaticamente no buildCommand do Render antes de iniciar app
# =============================================================================

set -e  # Exit on error

echo "========================================="
echo "🚀 Render Release: Starting migrations"
echo "========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL not set!"
    echo "   Skipping migrations (may fail if database required)"
    exit 0
fi

echo "✅ DATABASE_URL found (${DATABASE_URL:0:20}...)"

# Navigate to backend directory (script is in /scripts, backend is ../backend)
cd "$(dirname "$0")/../backend"
echo "📁 Working directory: $(pwd)"

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ ERROR: Alembic not found!"
    echo "   Make sure 'pip install -r requirements.txt' ran successfully"
    exit 1
fi

echo "✅ Alembic found: $(alembic --version)"

# Show current database revision
echo ""
echo "📊 Current database state:"
alembic current || echo "⚠️  No alembic_version table yet (first deploy?)"

# Run migrations
echo ""
echo "🔄 Running migrations..."
alembic upgrade head

# Verify final state
echo ""
echo "✅ Migrations complete!"
echo "📊 Final database revision:"
alembic current

echo ""
echo "========================================="
echo "✅ Render Release: Success"
echo "========================================="

exit 0
