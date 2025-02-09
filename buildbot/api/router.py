from fastapi.routing import APIRouter

from buildbot.api import docs, health, job, task

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(docs.router)
api_router.include_router(task.router, prefix="/task", tags=["task"])
api_router.include_router(job.router, prefix="/job", tags=["job"])
