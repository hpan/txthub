import os
import re
import time
import psycopg2
import bcrypt
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from jose import jwt, JWTError
from mangum import Mangum

SECRET_KEY = "txthub-secret-key-change-in-production"
ALGORITHM = "HS256"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db_url():
    for key in ["DATABASE_URL", "POSTGRES_URL", "POSTGRES_PRISMA_URL", "POSTGRES_URL_NON_POOLING"]:
        url = os.environ.get(key)
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
    raise RuntimeError("No database URL found")

_db_initialized = False

def get_db():
    global _db_initialized
    if not _db_initialized:
        # init_db called via get_db()
        _db_initialized = True
    conn = psycopg2.connect(get_db_url())
    conn.autocommit = True
    return conn

def # init_db called via get_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at REAL NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), content TEXT NOT NULL, created_at REAL NOT NULL, is_processed BOOLEAN NOT NULL DEFAULT FALSE)')
    c.execute('CREATE TABLE IF NOT EXISTS tags (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS message_tags (message_id INTEGER NOT NULL REFERENCES messages(id), tag_id INTEGER NOT NULL REFERENCES tags(id), PRIMARY KEY (message_id, tag_id))')
    conn.close()

@app.get("/api/debug")
async def debug():
    info = {"imports": "ok"}
    try:
        url = get_db_url()
        info["db_url_prefix"] = url[:30] + "..."
    except Exception as e:
        info["db_url_error"] = str(e)
    try:
        # init_db called via get_db()
        info["db_init"] = "ok"
    except Exception as e:
        info["db_init_error"] = str(e)
    return info

@app.get("/api/health")
async def health():
    return {"status": "ok"}

CLOUD_DRIVE_PATTERNS = [r'pan\.baidu\.com', r'quark\.cn', r'www\.alipan\.com', r'aliyundrive\.com', r'pan\.xunlei\.com', r'cloud\.189\.cn']

def detect_tags(content: str) -> List[str]:
    for p in CLOUD_DRIVE_PATTERNS:
        if re.search(p, content, re.IGNORECASE):
            return ["网盘"]
    return ["日记"]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的token")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")

def ensure_tag(conn, name: str) -> int:
    c = conn.cursor()
    c.execute("SELECT id FROM tags WHERE name = %s", (name,))
    row = c.fetchone()
    if row: return row[0]
    c.execute("INSERT INTO tags (name) VALUES (%s) RETURNING id", (name,))
    return c.fetchone()[0]

def get_message_tags(conn, message_id: int) -> List[str]:
    c = conn.cursor()
    c.execute('SELECT t.name FROM tags t JOIN message_tags mt ON t.id = mt.tag_id WHERE mt.message_id = %s', (message_id,))
    return [row[0] for row in c.fetchall()]

class UserCreate(BaseModel):
    username: str
    password: str

class MessageCreate(BaseModel):
    content: str

class Message(BaseModel):
    id: int
    user_id: int
    username: str
    content: str
    created_at: float
    is_processed: bool
    tags: List[str]

class PaginatedMessages(BaseModel):
    items: List[Message]
    total: int
    page: int
    page_size: int
    total_pages: int

@app.post("/api/register")
async def register(user: UserCreate):
    if len(user.username) < 2 or len(user.password) < 4:
        raise HTTPException(status_code=400, detail="用户名至少2位，密码至少4位")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = %s", (user.username,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    hash_ = hash_password(user.password)
    c.execute("INSERT INTO users (username, password_hash, created_at) VALUES (%s, %s, %s) RETURNING id",
              (user.username, hash_, time.time()))
    user_id = c.fetchone()[0]
    conn.close()
    token = jwt.encode({"sub": str(user_id)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"token": token, "username": user.username}

@app.post("/api/login")
async def login(user: UserCreate):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (user.username,))
    row = c.fetchone()
    conn.close()
    if not row or not verify_password(user.password, row[2]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = jwt.encode({"sub": str(row[0])}, SECRET_KEY, algorithm=ALGORITHM)
    return {"token": token, "username": row[1]}

@app.get("/api/me")
async def get_me(user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    row = c.fetchone()
    conn.close()
    return {"id": row[0], "username": row[1]}

@app.get("/api/tags")
async def list_tags(user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT t.name, COUNT(mt.message_id) as count FROM tags t JOIN message_tags mt ON t.id = mt.tag_id JOIN messages m ON mt.message_id = m.id WHERE m.user_id = %s GROUP BY t.id ORDER BY count DESC''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"name": row[0], "count": row[1]} for row in rows]

@app.post("/api/messages", response_model=Message)
async def create_message(msg: MessageCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    created_at = time.time()
    c.execute("INSERT INTO messages (user_id, content, created_at) VALUES (%s, %s, %s) RETURNING id", (user_id, msg.content, created_at))
    msg_id = c.fetchone()[0]
    tag_names = detect_tags(msg.content)
    for name in tag_names:
        tag_id = ensure_tag(conn, name)
        c.execute("INSERT INTO message_tags (message_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (msg_id, tag_id))
    c.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    username = c.fetchone()[0]
    conn.close()
    return {"id": msg_id, "user_id": user_id, "username": username, "content": msg.content, "created_at": created_at, "is_processed": False, "tags": tag_names}

@app.get("/api/messages", response_model=PaginatedMessages)
async def list_messages(page: int = 1, page_size: int = 10, tag: Optional[str] = None, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    if tag:
        c.execute('SELECT COUNT(DISTINCT m.id) FROM messages m JOIN message_tags mt ON m.id = mt.message_id JOIN tags t ON mt.tag_id = t.id WHERE m.user_id = %s AND t.name = %s', (user_id, tag))
    else:
        c.execute("SELECT COUNT(*) FROM messages WHERE user_id = %s", (user_id,))
    total = c.fetchone()[0]
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * page_size
    if tag:
        c.execute('''SELECT DISTINCT m.id, m.user_id, u.username, m.content, m.created_at, m.is_processed FROM messages m JOIN users u ON m.user_id = u.id JOIN message_tags mt ON m.id = mt.message_id JOIN tags t ON mt.tag_id = t.id WHERE m.user_id = %s AND t.name = %s ORDER BY m.created_at DESC LIMIT %s OFFSET %s''', (user_id, tag, page_size, offset))
    else:
        c.execute('''SELECT m.id, m.user_id, u.username, m.content, m.created_at, m.is_processed FROM messages m JOIN users u ON m.user_id = u.id WHERE m.user_id = %s ORDER BY m.created_at DESC LIMIT %s OFFSET %s''', (user_id, page_size, offset))
    rows = c.fetchall()
    items = []
    for r in rows:
        item = {"id": r[0], "user_id": r[1], "username": r[2], "content": r[3], "created_at": r[4], "is_processed": r[5]}
        item["tags"] = get_message_tags(conn, item["id"])
        items.append(item)
    conn.close()
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

@app.put("/api/messages/{message_id}/process")
async def process_message(message_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT is_processed FROM messages WHERE id = %s AND user_id = %s", (message_id, user_id))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="消息不存在")
    new_status = not row[0]
    c.execute("UPDATE messages SET is_processed = %s WHERE id = %s", (new_status, message_id))
    conn.close()
    return {"status": "success", "is_processed": new_status}

# init_db is called lazily on first request
handler = Mangum(app, lifespan="off")
