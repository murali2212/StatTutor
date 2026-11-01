"""Study materials: upload notes/textbooks, split into chunks, search with SQLite FTS5
(BM25 ranking, works offline, no extra packages). Material text is untrusted data."""
import re
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from . import academic, db

router = APIRouter(prefix="/api")
KINDS = {"notes", "textbook", "other", "syllabus", "papers"}
MAX_BYTES, MAX_TEXT = 15 * 1024 * 1024, 600000
STOP = set("a an the of and or to in on for is are was were be by with from at as it this that what how why do does did me my i you your can please tell explain teach about give show find".split())

def chunk_text(text, size=900, overlap=150):
    text = re.sub(r"[ \t]+", " ", text.replace("\r", "")).strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=[A-Z0-9])", text) if p.strip()]
    pieces = []
    for p in paras:
        while len(p) > size:                       # break a very long paragraph at a sentence end or a space
            cut = max(p.rfind(". ", 0, size), p.rfind(" ", 0, size))
            if cut < size // 2:
                cut = size
            pieces.append(p[:cut + 1].strip())
            p = p[max(cut + 1 - overlap, 1):].strip()
        pieces.append(p)
    chunks, cur = [], ""
    for p in pieces:
        if cur and len(cur) + 1 + len(p) > size:
            chunks.append(cur)
            cur = p
        else:
            cur = (cur + "\n" + p) if cur else p
    if cur:
        chunks.append(cur)
    return [c for c in chunks if len(c) > 20]

def add_material(title, kind, text):
    parts = chunk_text(text[:MAX_TEXT])
    if not parts:
        raise ValueError("No readable text found in this material.")
    with db.conn() as c:
        mid = c.execute("INSERT INTO materials(title, kind, chars) VALUES (?,?,?)", (title[:200], kind, len(text))).lastrowid
        for i, t in enumerate(parts):
            cid = c.execute("INSERT INTO chunks(material_id, position, text) VALUES (?,?,?)", (mid, i, t)).lastrowid
            c.execute("INSERT INTO chunk_fts(text, chunk_id, material_id) VALUES (?,?,?)", (t, cid, mid))
    return mid, len(parts)

def search(query, k=4):
    toks = [t for t in re.findall(r"[A-Za-z0-9']+", query.lower()) if len(t) > 1 and t not in STOP][:12]
    if not toks:
        return []
    q = " OR ".join('"' + t.replace('"', "") + '"' for t in toks)
    with db.conn() as c:
        rows = c.execute("""SELECT f.chunk_id, f.material_id, m.title, k.text, bm25(chunk_fts) AS score
                            FROM chunk_fts f JOIN chunks k ON k.id = f.chunk_id JOIN materials m ON m.id = f.material_id
                            WHERE chunk_fts MATCH ? ORDER BY score LIMIT ?""", (q, k)).fetchall()
    return [{"chunk_id": r["chunk_id"], "material_id": r["material_id"], "title": r["title"], "text": r["text"]} for r in rows]

@router.post("/materials")
async def upload_material(title: str = Form(""), kind: str = Form("notes"), text: Optional[str] = Form(None),
                          file: Optional[UploadFile] = File(None)):
    if kind not in KINDS:
        raise HTTPException(400, "Unknown material type.")
    if file is not None and file.filename:
        data = await file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "File is larger than 15 MB.")
        try:
            body = academic.extract_text(file.filename, data)
        except ValueError as e:
            raise HTTPException(400, str(e))
        name = (title.strip() or file.filename)
    elif text and text.strip():
        body, name = text.strip(), (title.strip() or "Pasted notes")
    else:
        raise HTTPException(400, "Choose a file or paste the text.")
    try:
        mid, n = add_material(name, kind, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": mid, "title": name, "chunks": n, "chars": len(body), "truncated": len(body) > MAX_TEXT}

@router.get("/materials")
def list_materials():
    with db.conn() as c:
        return [dict(r) for r in c.execute("""SELECT m.id, m.title, m.kind, m.chars, COUNT(k.id) AS chunks
                                              FROM materials m LEFT JOIN chunks k ON k.material_id = m.id
                                              GROUP BY m.id ORDER BY m.id""")]

@router.delete("/materials/{mid}")
def delete_material(mid: int):
    with db.conn() as c:
        c.execute("DELETE FROM chunk_fts WHERE material_id = ?", (mid,))
        c.execute("DELETE FROM materials WHERE id = ?", (mid,))
    return {"ok": True}

@router.get("/materials/search")
def search_route(q: str, k: int = 4):
    return [{"title": h["title"], "text": h["text"]} for h in search(q[:300], max(1, min(k, 8)))]
