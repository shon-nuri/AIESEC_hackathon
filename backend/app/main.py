from fastapi import FastAPI
from documents.router import router as router_documents

app = FastAPI()

app.include_router(router_documents)