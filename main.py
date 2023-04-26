from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, HTTPException, Depends

import validators
import hashlib

from keygen import create_random_key
import models
import database
import crud


models.Base.metadata.create_all(bind=database.engine)


app = FastAPI()
templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = database.SessionLocal()
        yield db
    finally:
        db.close()


def shortened_url(url):
    hash_object = hashlib.md5(url.encode())
    hash_str = hash_object.hexdigest()
    short_url_hash = create_random_key(6) + "_" + hash_str[:6]
    short_url_key = hashlib.md5(short_url_hash.encode()).hexdigest()[:6]
    return short_url_key


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "url_shortener": "URL-Shortener", "reverse_shortener": "Reverse-URL-Shortener"})


@app.get("/url/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    all_url_data = crud.get_all_url_data(db=db)
    return templates.TemplateResponse("urlshort.html", {"request": request, "all_short_url": all_url_data})


@app.post("/url/submit")
async def get_url(og_url: database.Item, db: Session = Depends(get_db)):
    original_url = og_url.url
    url_base = og_url.url_base

    if not validators.url(original_url):
        return HTTPException(status_code=400, detail="Your provided URL is not valid")

    short_url_key = shortened_url(original_url)
    short_url = url_base + short_url_key

    url_mapping = crud.create_new_url(
        db=db, original_url=original_url, short_url=short_url, short_url_key=short_url_key)

    return url_mapping


@app.get("/url/{short_url_key}")
async def forward_to_target_url(short_url_key: str, db: Session = Depends(get_db)):
    url_mapping = crud.get_shortUrl_by_key(db=db, short_url_key=short_url_key)
    if url_mapping:
        crud.update_db_clicks(db=db, db_url=url_mapping)
        return RedirectResponse(url_mapping.original_url)
    else:
        return HTTPException(status_code=404, detail="URL does not exist")


@app.delete("/url/{short_url_key}")
async def disable_target_url(short_url_key: str, db: Session = Depends(get_db)):
    url_mapping = crud.get_shortUrl_by_key(db=db, short_url_key=short_url_key)
    if url_mapping:
        crud.deactivate_db(db=db, db_url=url_mapping)
        message = f"Successfully disabled shortened URL for key: {short_url_key}"
        return {"detail": message}
    else:
        return HTTPException(status_code=404, detail="URL have been disabled")
