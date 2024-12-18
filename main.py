from fastapi import FastAPI

app = FastAPI(
    title="Oasis API",
    description="Backend API for Oasis platform",
    version="0.1.0"
)


@app.get("/",
         summary="Root endpoint",
         description="Returns a welcome message for the Oasis API",
         response_description="Welcome message object")
async def root():
    return {"message": "Welcome to Oasis API"}
