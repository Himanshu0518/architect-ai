import asyncio
import json
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from server.main import ArchitectFlow

app = FastAPI(title="ArchitectFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    company_name: str
    user_requirements: str = "none"

@app.post("/api/generate")
async def generate_design(request: GenerateRequest):
    progress_queue = asyncio.Queue()

    async def event_generator() -> AsyncGenerator[str, None]:
        # Background task to run the flow
        async def run_flow():
            flow = ArchitectFlow()
            trigger_payload = {
                "company_name": request.company_name,
                "user_requirements": request.user_requirements,
                "progress_queue": progress_queue
            }
            try:
                # kickoff_async is native to CrewAI Flow and runs fully async
                await flow.kickoff_async({"crewai_trigger_payload": trigger_payload})
                # Flow is done
                await progress_queue.put({
                    "status": "complete",
                    "crew": "System",
                    "message": "Generation complete.",
                    "document": flow.state.final_document
                })
            except Exception as e:
                await progress_queue.put({
                    "status": "error",
                    "crew": "System",
                    "message": f"Error during generation: {str(e)}"
                })

        # Start flow in background
        task = asyncio.create_task(run_flow())

        while True:
            try:
                # Wait for the next progress event
                event = await progress_queue.get()
                
                # Yield the event as SSE
                yield json.dumps(event)
                
                if event.get("status") in ["complete", "error"]:
                    break
            except asyncio.CancelledError:
                task.cancel()
                break

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, reload=True)
