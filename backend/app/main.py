from fastapi import FastAPI
from app.routers import projects
from app.routers import safety_docs
from app.routers import subcontractors

app = FastAPI(title="AuditAI SiteShield API")

# include routers
app.include_router(projects.router)
app.include_router(safety_docs.router)
app.include_router(subcontractors.router)

@app.get("/")
def root():
    return {"message": "🚀 Backend running!"}

