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

_db_initialized = False

def get_db_url():
    for key in ["DATABASE_URL", "POSTGRES_URL", "POSTGRES_PRISMA_URL", "POSTGRES_URL_NON_POOLING"]:
        url = os.environ.get(key)
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
    raise RuntimeError("No database URL found")

def init_db():
    conn = psycopg2.connect(get_db_url())
    conn.autocommit = True
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), content TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, is_processed BOOLEAN NOT NULL DEFAULT FALSE)')
    c.execute('CREATE TABLE IF NOT EXISTS tags (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS message_tags (message_id INTEGER NOT NULL REFERENCES messages(id), tag_id INTEGER NOT NULL REFERENCES tags(id), PRIMARY KEY (message_id, tag_id))')
    # Migration: change REAL to DOUBLE PRECISION if needed
    try:
        c.execute('ALTER TABLE messages ALTER COLUMN created_at TYPE DOUBLE PRECISION')
    except Exception:
        pass  # already correct type or table doesn't exist yet
    try:
        c.execute('ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_edited BOOLEAN NOT NULL DEFAULT FALSE')
    except Exception:
        pass
    conn.close()

def get_db():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True
    conn = psycopg2.connect(get_db_url())
    conn.autocommit = True
    return conn

CLOUD_DRIVE_PATTERNS = [r'pan\.baidu\.com', r'quark\.cn', r'www\.alipan\.com', r'aliyundrive\.com', r'pan\.xunlei\.com', r'cloud\.189\.cn']

CODE_PATTERNS = [
    r'#!/',                           # shebang
    r'^\s*(def|class|import|from)\s', # Python
    r'^\s*(function|const|let|var|export)\s', # JS
    r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)\s', # SQL
    r'\\\s*$',                       # shell line continuation
    r'^\s*(echo|grep|awk|sed|curl|wget|chmod|mkdir|cd|ls|cat|pip|npm|git|docker|ssh)\s', # shell commands
    r'^\s*\$\s',                     # shell prompt
    r'^\s*(if|for|while|switch|try|catch)\s*[({]', # control structures
    r'^\s*[{};]\s*$',                # code block markers
    r'=>|->|\?\.|===|!==',           # code operators
    r'^\s*//|^\s*#\s|^\s*/\*',    # comments
    r'<[a-zA-Z][^>]*>',               # HTML tags
    r'\w+\(.*\);',                  # function calls
]

def is_code(content):
    lines = content.strip().split('\n')
    if len(lines) >= 3:
        score = 0
        for line in lines:
            for p in CODE_PATTERNS:
                if re.search(p, line):
                    score += 1
                    break
        if score >= len(lines) * 0.4:
            return True
    single_line_patterns = [
        r'\\\s*$',
        r'#!/',
        r'^\s*(def|class|function|import)\s',
        r'\{.*\}',
        r'\|',
        r'>>|<<',
        r'\$\(',
        r'`[^`]+`',
        r'^\s*(find|grep|awk|sed|xargs|curl|wget|rsync|scp|ssh|tar|unzip|pip|npm|yarn|cargo|go|make|cmake|docker|kubectl|terraform|ansible)\b',
        r'^\s*(git|brew|apt|yum|dnf|pacman|snap)\b',
        r'^\s*(python|node|ruby|perl|php|java|gcc|g\+\+|rustc)\b',
        r'\-\w+\s+\S',
        r'\.\/',
        r'^\s*sudo\b',
    ]
    for p in single_line_patterns:
        if re.search(p, content):
            return True
    return False

def detect_tags(content):
    tags = []
    for p in CLOUD_DRIVE_PATTERNS:
        if re.search(p, content, re.IGNORECASE):
            tags.append("网盘")
            break
    if not tags and is_code(content):
        tags.append("代码")
    if not tags:
        tags.append("日记")
    return tags

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
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

def ensure_tag(conn, name):
    c = conn.cursor()
    c.execute("SELECT id FROM tags WHERE name = %s", (name,))
    row = c.fetchone()
    if row: return row[0]
    c.execute("INSERT INTO tags (name) VALUES (%s) RETURNING id", (name,))
    return c.fetchone()[0]

def get_message_tags(conn, message_id):
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
    is_edited: bool
    tags: List[str]

class PaginatedMessages(BaseModel):
    items: List[Message]
    total: int
    page: int
    page_size: int
    total_pages: int

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/debug")
async def debug():
    info = {"status": "ok"}
    try:
        url = get_db_url()
        info["db_url"] = url[:30] + "..."
    except Exception as e:
        info["db_error"] = str(e)
    try:
        init_db()
        info["db_init"] = "ok"
    except Exception as e:
        info["db_init_error"] = str(e)
    return info

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
    h = hash_password(user.password)
    c.execute("INSERT INTO users (username, password_hash, created_at) VALUES (%s, %s, %s) RETURNING id",
              (user.username, h, time.time()))
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
    c.execute('SELECT t.name, COUNT(mt.message_id) as count FROM tags t JOIN message_tags mt ON t.id = mt.tag_id JOIN messages m ON mt.message_id = m.id WHERE m.user_id = %s GROUP BY t.id ORDER BY count DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"name": r[0], "count": r[1]} for r in rows]

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
    return {"id": msg_id, "user_id": user_id, "username": username, "content": msg.content, "created_at": created_at, "is_processed": False, "is_edited": False, "tags": tag_names}

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
        c.execute('SELECT DISTINCT m.id, m.user_id, u.username, m.content, m.created_at, m.is_processed, m.is_edited FROM messages m JOIN users u ON m.user_id = u.id JOIN message_tags mt ON m.id = mt.message_id JOIN tags t ON mt.tag_id = t.id WHERE m.user_id = %s AND t.name = %s ORDER BY m.created_at DESC, m.id DESC LIMIT %s OFFSET %s', (user_id, tag, page_size, offset))
    else:
        c.execute('SELECT m.id, m.user_id, u.username, m.content, m.created_at, m.is_processed, m.is_edited FROM messages m JOIN users u ON m.user_id = u.id WHERE m.user_id = %s ORDER BY m.created_at DESC, m.id DESC LIMIT %s OFFSET %s', (user_id, page_size, offset))
    rows = c.fetchall()
    items = []
    for r in rows:
        item = {"id": r[0], "user_id": r[1], "username": r[2], "content": r[3], "created_at": r[4], "is_processed": r[5], "is_edited": r[6] if len(r) > 6 else False}
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



class MessageUpdate(BaseModel):
    content: str

@app.put("/api/messages/{message_id}")
async def edit_message(message_id: int, msg: MessageUpdate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM messages WHERE id = %s AND user_id = %s", (message_id, user_id))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="消息不存在")
    c.execute("UPDATE messages SET content = %s, is_edited = TRUE WHERE id = %s", (msg.content, message_id))
    # 重新检测标签
    c.execute("DELETE FROM message_tags WHERE message_id = %s", (message_id,))
    tag_names = detect_tags(msg.content)
    for name in tag_names:
        tag_id = ensure_tag(conn, name)
        c.execute("INSERT INTO message_tags (message_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (message_id, tag_id))
    conn.close()
    return {"status": "updated", "is_edited": True, "tags": tag_names}

@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM messages WHERE id = %s AND user_id = %s", (message_id, user_id))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="消息不存在")
    c.execute("DELETE FROM message_tags WHERE message_id = %s", (message_id,))
    c.execute("DELETE FROM messages WHERE id = %s AND user_id = %s", (message_id, user_id))
    conn.close()
    return {"status": "deleted"}

handler = Mangum(app, lifespan="off")
