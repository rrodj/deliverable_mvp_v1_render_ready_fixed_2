import os
from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

_engine = None
_SessionLocal = None

def _get_url():
    return current_app.config.get("DATABASE_URL") or os.getenv("DATABASE_URL")

def get_engine():
    global _engine, _SessionLocal
    url = _get_url()
    if not url:
        return None
    if _engine is None:
        _engine = create_engine(url, pool_pre_ping=True)
        _SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=_engine))
    return _engine

def get_session():
    eng = get_engine()
    if not eng:
        return None
    if "db" not in g:
        g.db = _SessionLocal()
    return g.db

def close_session(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
