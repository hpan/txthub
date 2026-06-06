from mangum import Mangum
from main import app

try:
    from database import init_db
    init_db()
except Exception as e:
    print(f"DB init warning: {e}")

handler = Mangum(app, lifespan="off")
