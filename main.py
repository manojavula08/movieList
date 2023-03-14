from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
import models
from database import engine
from router import movie
app = FastAPI()

app.include_router(movie.router)

models.Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static"), name="static")
