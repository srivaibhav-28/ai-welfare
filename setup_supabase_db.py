import os
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def build_database_url(raw_url: str) -> str:
    if not raw_url or "[YOUR-PASSWORD]" in raw_url:
        raise ValueError("DATABASE_URL is not configured.")

    parsed = urlsplit(raw_url)
    if not parsed.username or not parsed.password:
        return raw_url

    encoded_password = quote(parsed.password, safe="")
    netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"

    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def main() -> None:
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 is not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    raw_url = os.environ.get("DATABASE_URL", "").strip()
    database_url = build_database_url(raw_url)
    schema_sql = (BASE_DIR / "supabase_schema.sql").read_text(encoding="utf-8")

    connection_urls = [database_url]

    project_ref = "mborxydvtiekgnxflsci"
    password = quote("SriVaibhav@2007", safe="")
    regions = ["ap-south-1", "us-east-1", "eu-central-1", "ap-southeast-1", "us-west-1"]
    for r in regions:
        for port in [6543, 5432]:
            connection_urls.append(f"postgresql://postgres.{project_ref}:{password}@aws-0-{r}.pooler.supabase.com:{port}/postgres")

    conn = None
    for url in connection_urls:
        try:
            conn = psycopg2.connect(url, connect_timeout=4)
            print(f"Successfully connected to database!")
            break
        except Exception:
            continue

    if not conn:
        print("Could not connect directly via TCP pooler. Please run supabase_schema.sql in the Supabase SQL Editor.")
        sys.exit(1)

    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(schema_sql)
    cur.close()
    conn.close()
    print("Supabase tables created successfully.")


if __name__ == "__main__":
    main()
