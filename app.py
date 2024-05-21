from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException

import auth
import models
from config import engine

models.base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)

user_dependency = Annotated[dict, Depends(auth.get_current_user)]


@app.get("/")
async def home(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"Hello": "World"}
