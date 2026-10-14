"""Tiny SQLite store. Each packet is one JSON blob so the schema never needs migrations."""
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import List, Optional

from .schemas import Packet, PacketIn, new_id, now_iso

DB_PATH = Path(os.getenv("CONTEXT_BRIDGE_DB", str(Path(__file__).resolve().parents[1] / "contextbridge.db")))


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init() -> None:
    with closing(_conn()) as c, c:
        c.execute("CREATE TABLE IF NOT EXISTS packets (id TEXT PRIMARY KEY, data TEXT NOT NULL, updated TEXT NOT NULL)")


def _row(r: sqlite3.Row) -> Packet:
    return Packet(**json.loads(r["data"]))


def list_packets() -> List[Packet]:
    with closing(_conn()) as c:
        return [_row(r) for r in c.execute("SELECT * FROM packets ORDER BY updated DESC")]


def get(pid: str) -> Optional[Packet]:
    with closing(_conn()) as c:
        r = c.execute("SELECT * FROM packets WHERE id = ?", (pid,)).fetchone()
        return _row(r) if r else None


def create(p: PacketIn) -> Packet:
    t = now_iso()
    pkt = Packet(id=new_id(), created=t, updated=t, **p.model_dump())
    with closing(_conn()) as c, c:
        c.execute("INSERT INTO packets VALUES (?, ?, ?)", (pkt.id, pkt.model_dump_json(), pkt.updated))
    return pkt


def update(pid: str, p: PacketIn) -> Optional[Packet]:
    old = get(pid)
    if not old:
        return None
    pkt = Packet(id=pid, created=old.created, updated=now_iso(), **p.model_dump())
    with closing(_conn()) as c, c:
        c.execute("UPDATE packets SET data = ?, updated = ? WHERE id = ?", (pkt.model_dump_json(), pkt.updated, pid))
    return pkt


def delete(pid: str) -> bool:
    with closing(_conn()) as c, c:
        return c.execute("DELETE FROM packets WHERE id = ?", (pid,)).rowcount > 0


def count() -> int:
    with closing(_conn()) as c:
        return c.execute("SELECT COUNT(*) FROM packets").fetchone()[0]
