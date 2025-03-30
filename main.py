from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from typing import List, Optional
import uvicorn
from utils.youtube import search_videos, download_video, download_audio, get_video_info
from starlette.background import BackgroundTask

app = FastAPI(title="YouTube Downloader API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
VIDEO_DIR = os.path.join(DOWNLOAD_DIR, "videos")
AUDIO_DIR = os.path.join(DOWNLOAD_DIR, "audio")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

download_progress = {}

class SearchQuery(BaseModel):
    query: str

class VideoInfo(BaseModel):
    id: str
    title: str
    thumbnail_url: str
    watch_url: str
    duration: Optional[int] = None

class DownloadRequest(BaseModel):
    video_url: str
    download_type: str  # "audio" or "video"

@app.get("/")
def read_root():
    return {"message": "YouTube Downloader API"}

@app.post("/search", response_model=List[VideoInfo])
async def search(query: SearchQuery):
    try:
        results = search_videos(query.query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download")
async def download(request: DownloadRequest, background_tasks: BackgroundTasks):
    download_id = str(uuid.uuid4())
    download_progress[download_id] = {"progress": 0, "status": "starting", "filename": None}
    
    try:
        if request.download_type == "audio":
            background_tasks.add_task(
                download_audio,
                request.video_url,
                AUDIO_DIR,
                download_id,
                download_progress
            )
        else:
            background_tasks.add_task(
                download_video,
                request.video_url,
                VIDEO_DIR,
                download_id,
                download_progress
            )
        
        return {"download_id": download_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{download_id}/progress")
async def get_progress(download_id: str):
    if download_id not in download_progress:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return download_progress[download_id]

@app.get("/download/{download_id}/file")
async def get_file(download_id: str):
    if download_id not in download_progress:
        raise HTTPException(status_code=404, detail="Download not found")
    
    progress_info = download_progress[download_id]
    
    if progress_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Download not completed yet")
    
    if not progress_info["filename"] or not os.path.exists(progress_info["filename"]):
        raise HTTPException(status_code=404, detail="File not found")
    
    task = BackgroundTask(os.remove, progress_info["filename"])
    
    return FileResponse(
        path=progress_info["filename"],
        filename=os.path.basename(progress_info["filename"]),
        media_type="application/octet-stream",
        background=task
    )

@app.get("/video-info")
async def video_info(url: str):
    try:
        info = get_video_info(url)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

