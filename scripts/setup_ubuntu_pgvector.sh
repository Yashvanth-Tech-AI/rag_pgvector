#!/usr/bin/env bash
set -euo pipefail

# Ubuntu setup for PostgreSQL 16 + pgvector.
# This script assumes Ubuntu and sudo access.

echo "=== pgvector-rag-engine: PostgreSQL 16 + pgvector setup ==="

if ! command -v lsb_release >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y lsb-release ca-certificates curl
fi

if ! command -v psql >/dev/null 2>&1; then
    echo "PostgreSQL client is not installed."
    echo "This prototype expects PostgreSQL 16 to be installed."
    echo "Install PostgreSQL 16 first, then run this script again."
    exit 1
fi

PG_VERSION="$(psql --version | awk '{print $3}' | cut -d. -f1)"

if [[ "${PG_VERSION}" != "16" ]]; then
    echo "ERROR: PostgreSQL 16 is required."
    echo "Detected PostgreSQL major version: ${PG_VERSION}"
    exit 1
fi

echo "PostgreSQL 16 detected."

# The PostgreSQL APT repository provides the versioned pgvector package.
# The pgvector project documents this package as:
# postgresql-16-pgvector
if [[ ! -f /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh ]]; then
    echo "Installing PostgreSQL APT repository helper..."
    sudo apt-get update
    sudo apt-get install -y postgresql-common ca-certificates
fi

if [[ -f /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh ]]; then
    echo "Configuring PostgreSQL APT repository..."
    sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
fi

echo "Installing pgvector for PostgreSQL 16..."
sudo apt-get update
sudo apt-get install -y postgresql-16-pgvector

echo "Restarting PostgreSQL..."
sudo systemctl restart postgresql

echo "Checking pgvector extension files..."
if [[ ! -f /usr/share/postgresql/16/extension/vector.control ]]; then
    echo "ERROR: vector.control was not found."
    echo "pgvector installation did not complete correctly."
    exit 1
fi

echo "pgvector files found."

echo "Creating/enabling pgvector in the default postgres database..."
sudo -u postgres psql -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo
echo "=== Installation verification ==="
sudo -u postgres psql -d postgres -c \
    "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

echo
echo "SUCCESS: PostgreSQL 16 + pgvector are installed."
echo "Next step: run ./scripts/bootstrap.sh"
