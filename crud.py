from sqlalchemy.orm import Session


import models


def get_all_url_data(db: Session):
    all_data = db.query(models.UrlMapping).all()

    return all_data


def create_new_url(db: Session, original_url, short_url_key, short_url):
    url_mapping = models.UrlMapping(
        original_url=original_url, short_url=short_url, short_url_key=short_url_key)
    db.add(url_mapping)
    db.commit()
    db.refresh(url_mapping)

    return url_mapping


def get_shortUrl_by_key(db: Session, short_url_key):
    url_mapping = db.query(models.UrlMapping).filter(
        models.UrlMapping.short_url_key == short_url_key).filter(models.UrlMapping.is_active == True).first()

    return url_mapping


def update_db_clicks(db: Session, db_url: models.UrlMapping):
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)

    return db_url


def deactivate_db(db: Session, db_url: models.UrlMapping):
    db_url.is_active = False
    db.commit()
    db.refresh(db_url)

    return db_url
