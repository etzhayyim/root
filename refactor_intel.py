import re
import sys

def patch(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. remove psycopg imports
    content = re.sub(r'\n    import psycopg\n', '\n', content)
    
    # 2. IntelStore.__init__ and connect
    old_init = """    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def connect(self) -> psycopg.Connection[Any]:
        import psycopg

        # RisingWave's PostgreSQL wire path is sensitive to psycopg3 server-side
        # prepared statements (for example LIMIT parameters and some SELECTs).
        # Keep statements simple-protocol unless a future RW version proves safe.
        return psycopg.connect(self.dsn, autocommit=True, prepare_threshold=None)"""
    new_init = """    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        from pymagatama.kotoba_datomic import get_kotoba_client
        self.client = get_kotoba_client()"""
    content = content.replace(old_init, new_init)

    # 3. dict_row_factory removal
    old_drf = """def dict_row_factory() -> Any:
    import psycopg

    return psycopg.rows.dict_row"""
    content = content.replace(old_drf, "def dict_row_factory() -> Any:\n    pass")

    # Now we need to manually adjust all the methods.
    # It might be easier to use replace via default_api for each function,
    # or write string replacements here. I will just print the file and do string replacement step by step.

    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    patch(sys.argv[1])
