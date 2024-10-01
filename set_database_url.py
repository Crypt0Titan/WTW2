import os

pguser = os.environ.get('PGUSER')
pgpassword = os.environ.get('PGPASSWORD')
pghost = os.environ.get('PGHOST')
pgport = os.environ.get('PGPORT')
pgdatabase = os.environ.get('PGDATABASE')

if all([pguser, pgpassword, pghost, pgport, pgdatabase]):
    database_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
    print(f"export DATABASE_URL='{database_url}'")
else:
    print("Error: One or more required environment variables are missing.")
