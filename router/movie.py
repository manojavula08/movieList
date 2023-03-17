import os
import sys
from typing import Optional

import aiofiles
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

sys.path.append("...")
import secrets
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import models
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from fastapi.templating import Jinja2Templates

router = APIRouter( tags=["Movies"])
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


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


@router.get("/read_data", response_class=HTMLResponse)
async def read_data(request: Request, db: Session = Depends(get_db)):
    movie_model = db.query(models.Movie).all()
    return templates.TemplateResponse("index.html", {"request": request, "movies": movie_model})


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

    # # pillow
    # Image.MAX_IMAGE_PIXELS = 1000000000
    # img = Image.open(path)
    # img = img.resize(size=(200, 200))
    # img.save(path)
    # output = "127.0.0.1:8000/" + path
    return new_file_name


async def delete_img(url):
    path = "static/movie/images/" + url
    if os.path.exists(path):
        os.remove(path)


@router.get("/create")
async def update_movie(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})


@router.post("/create")
async def create_movie(file: UploadFile = File(...), title: str = Form(...), year: int = Form(...),
                       rating: int = Form(...), description: str = Form(...), ranking: int = Form(...), review: str = Form(...),
                       db: Session = Depends(get_db)):
    movie_model = models.Movie()
    movie_model.title = title
    movie_model.year = year
    movie_model.rating = rating
    movie_model.description = description
    movie_model.ranking = ranking
    movie_model.review = review
    if file:
        output = await m_upload_file(file)
        movie_model.img_url = output
    else:
        movie_model.img_url = None

    db.add(movie_model)
    db.commit()
    return RedirectResponse(url="/read_data", status_code=status.HTTP_302_FOUND)


@router.get("/update/{movie_id}")
async def update_movie(request: Request, movie_id: int, db: Session = Depends(get_db)):
    movie_model = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    return templates.TemplateResponse("edit.html", {"request": request, "movies": movie_model})


@router.post("/update/{movie_id}", status_code=status.HTTP_201_CREATED)
async def update_movie(request: Request, movie_id: int, file: Optional[UploadFile] = File(...), title: str = Form(...), year: int = Form(...),
                       rating: int = Form(...), description: str = Form(...), ranking: int = Form(...), review: str = Form(...),
                       db: Session = Depends(get_db)):
    movie_model = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    movie_model.title = title
    movie_model.year = year
    movie_model.rating = rating
    movie_model.description = description
    movie_model.ranking = ranking
    movie_model.review = review
    if movie_model.img_url is not None:
        await delete_img(movie_model.img_url)
    movie_model.img_url = await m_upload_file(file=file)

    db.add(movie_model)
    db.commit()

    return templates.TemplateResponse("edit.html", {"request": request, "movies": movie_model})


@router.get("/delete_movie/{movie_id}")
async def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie_model = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if movie_model is None:
        return RedirectResponse(url="/movie/read_data", status_code=status.HTTP_302_FOUND)
    if movie_model.img_url is not None:
        await delete_img(movie_model.img_url)
    db.query(models.Movie).filter(models.Movie.id == movie_id).delete()
    db.commit()
    return RedirectResponse(url="/read_data", status_code=status.HTTP_302_FOUND)
