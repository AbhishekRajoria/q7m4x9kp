from fastapi import FastAPI

from app.api import routes

app = FastAPI(title="WindSight API", version="0.0.1")

app.include_router(routes.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "WindSight API"}
