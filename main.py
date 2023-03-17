from fastapi import FastAPI
from starlette import status
from starlette.staticfiles import StaticFiles
import models
from database import engine
from router import movie
from starlette.responses import RedirectResponse
app = FastAPI()

app.include_router(movie.router)

@app.get("/")
async def movie():
    return RedirectResponse(url="/movie/read_data", status_code=status.HTTP_302_FOUND)

models.Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static"), name="static")
