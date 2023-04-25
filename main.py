from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
# from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException, Depends
import validators
import hashlib

from keygen import create_random_key
import models
import database


models.Base.metadata.create_all(bind=database.engine)


app = FastAPI()
templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = database.SessionLocal()
        yield db
    finally:
        db.close()


# origins = [
#     "http://localhost",
#     "http://localhost:8080",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "url_shortener": "URL-Shortener", "reverse_shortener": "Reverse-URL-Shortener"})


@app.get("/url/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    all_short_url = db.query(models.UrlMapping).all()
    for items in all_short_url:
        print(items)
    return templates.TemplateResponse("urlshort.html", {"request": request, "all_short_url": all_short_url})


@app.post("/url/submit")
async def get_url(og_url: database.Item, db: Session = Depends(get_db)):
    original_url = og_url.url
    url_base = og_url.url_base

    if not validators.url(original_url):
        return HTTPException(status_code=400, detail="Your provided URL is not valid")

    hash_object = hashlib.md5(original_url.encode())
    hash_str = hash_object.hexdigest()
    short_url_hash = create_random_key(6) + "_" + hash_str[:6]
    short_url_key = hashlib.md5(short_url_hash.encode()).hexdigest()[:6]
    short_url = url_base + short_url_key

    url_mapping = models.UrlMapping(
        original_url=original_url, short_url_key=short_url_key, short_url=short_url)
    db.add(url_mapping)
    db.commit()
    db.refresh(url_mapping)

    return url_mapping


@app.get("/url/{short_url_key}")
async def forward_to_target_url(short_url_key: str, db: Session = Depends(get_db)):
    print(short_url_key)
    url_mapping = db.query(models.UrlMapping).filter(
        models.UrlMapping.short_url_key == short_url_key).filter(models.UrlMapping.is_active == True).first()
    if url_mapping:
        url_mapping.clicks += 1
        db.commit()
        return RedirectResponse(url_mapping.original_url)
    else:
        return HTTPException(status_code=404, detail="URL does not exist")


@app.delete("/url/{short_url_key}")
async def disable_target_url(short_url_key: str, db: Session = Depends(get_db)):
    print(short_url_key)
    url_mapping = db.query(models.UrlMapping).filter(
        models.UrlMapping.short_url_key == short_url_key).filter(models.UrlMapping.is_active == True).first()
    if url_mapping:
        url_mapping.is_active = False
        db.commit()
        message = f"Successfully disabled shortened URL for key: {short_url_key}"
        return {"detail": message}
    else:
        return HTTPException(status_code=404, detail="URL have been disabled")
