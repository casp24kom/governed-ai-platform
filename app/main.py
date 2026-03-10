from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth import ApiAuthMiddleware
from app.routers import core_router, debug_router, dq_router, eval_metrics_router, rag_router

app = FastAPI(title="Governed AI Platform", version="1.0")
app.add_middleware(ApiAuthMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(core_router)
app.include_router(eval_metrics_router)
app.include_router(rag_router)
app.include_router(dq_router)
app.include_router(debug_router)
