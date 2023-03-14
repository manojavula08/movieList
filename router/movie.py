import os
import sys
from typing import Optional

import aiofiles

sys.path.append("...")
import secrets
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import models
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import SessionLocal, engine

router = APIRouter(prefix="/movie", tags=["Movies"])
models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Movie(BaseModel):
    title: str
    year: int
    description: str
    rating: int = Field(gt=-1, lt=6, description="The rating between 0-5")
    ranking: int = Field(gt=-1, lt=6, description="The ranking between 0-5")
    review: str


@router.get("/read_data")
async def read_data(db: Session = Depends(get_db)):
    movie_model = db.query(models.Movie).all()
    return movie_model


async def m_upload_file(file):
    FILEPATH = "static/movie/images/"
    if not os.path.exists(FILEPATH):
        os.makedirs(FILEPATH)
    file_name = file.filename
    extension = file_name.split(".")[1]

    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Only .jpeg or .png  files allowed")
    new_file_name = secrets.token_hex(10) + "." + extension

    path = FILEPATH + new_file_name
    file_content = await file.read()

    async with aiofiles.open(path, "wb") as file1:
        await file1.write(file_content)

    # pillow
    Image.MAX_IMAGE_PIXELS = 1000000000
    img = Image.open(path)
    img = img.resize(size=(200, 200))
    img.save(path)
    output = "127.0.0.1:8000/" + path
    return new_file_name


async def delete_img(url):
    path = "static/movie/images/" + url
    if os.path.exists(path):
        os.remove(path)

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_movie(file: Optional[UploadFile] = File(...), movie: Movie = Depends(), db: Session = Depends(get_db)):
    movie_model = models.Movie()
    movie_model.title = movie.title
    movie_model.year = movie.year
    movie_model.rating = movie.rating
    movie_model.description = movie.description
    movie_model.ranking = movie.ranking
    movie_model.review = movie.review
    if file:
        output = await m_upload_file(file)
        movie_model.img_url = output
    else:
        movie_model.img_url = None

    db.add(movie_model)
    db.commit()

    return movie_model


@router.put("/update/{movie_id}", status_code=status.HTTP_201_CREATED)
async def update_movie(movie_id: int, movie: Movie = Depends(), file: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    movie_model = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    movie_model.title = movie.title
    movie_model.year = movie.year
    movie_model.rating = movie.rating
    movie_model.description = movie.description
    movie_model.ranking = movie.ranking
    movie_model.review = movie.review
    if movie_model.img_url is not None:
        await delete_img(movie_model.img_url)
    movie_model.img_url = await m_upload_file(file=file)

    db.add(movie_model)
    db.commit()

    return movie_model

@router.delete("/delete_movie/{movie_id}")
async def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie_model = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if movie_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="related movie not found")
    if movie_model.img_url is not None:
        await delete_img(movie_model.img_url)
    db.query(models.Movie).filter(models.Movie.id == movie_id).delete()
    db.commit()
    return HTTPException(status_code=status.HTTP_302_FOUND, detail="successfully deleted")
