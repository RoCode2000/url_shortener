import validators
import hashlib

import secrets
import string

from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./url_shortener.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Item(BaseModel):
    url: str
    short_url_key: str | None = None


Base = declarative_base()


class UrlMapping(Base):
    __tablename__ = "url_mappings"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, index=True)
    short_url_key = Column(String, index=True, unique=True)
    clicks = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


Base.metadata.create_all(bind=engine)


app = FastAPI()
templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def create_random_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root(db: Session = Depends(get_db)):
    return {"message": "Hello World"}


@app.get("/url/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/url/submit")
async def get_url(og_url: Item, db: Session = Depends(get_db)):
    original_url = og_url.url

    if validators.url(original_url):
        hash_object = hashlib.md5(original_url.encode())
        hash_str = hash_object.hexdigest()
        short_url_key = create_random_key(6) + "_" + hash_str[:6]
        og_url.short_url_key = short_url_key

        url_mapping = UrlMapping(
            original_url=original_url, short_url_key=short_url_key)
        db.add(url_mapping)
        db.commit()
        db.refresh(url_mapping)

        return og_url
    else:
        return HTTPException(status_code=400, detail="Your provided URL is not valid")


@app.get("/url/{short_url_key}")
async def forward_to_target_url(short_url_key: str, db: Session = Depends(get_db)):
    url_mapping = db.query(UrlMapping).filter(
        UrlMapping.short_url_key == short_url_key).filter(UrlMapping.is_active == True).first()
    if url_mapping:
        url_mapping.clicks += 1
        db.commit()
        return RedirectResponse(url_mapping.original_url)
    else:
        return HTTPException(status_code=404, detail="URL does not exist")


@app.delete("/url/{short_url_key}")
async def disable_target_url(short_url_key: str, db: Session = Depends(get_db)):
    url_mapping = db.query(UrlMapping).filter(
        UrlMapping.short_url_key == short_url_key).filter(UrlMapping.is_active == True).first()
    if url_mapping:
        url_mapping.is_active = False
        db.commit()
        message = f"Successfully deleted shortened URL for key: {short_url_key}"
        return {"detail": message}
    else:
        return HTTPException(status_code=404, detail="URL does not exist")
