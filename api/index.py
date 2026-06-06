from main import app
from database import init_db
from mangum import Mangum

init_db()
handler = Mangum(app, lifespan="off")
