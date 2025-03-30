from pytubefix import YouTube
from pytubefix.contrib.search import Search
import os
import time

def search_videos(query, max_results=10):
    search = Search(query)
    results = []
    
    for i, video in enumerate(search.videos):
        if i >= max_results:
            break
            
        results.append({
            "id": video.video_id,
            "title": video.title,
            "thumbnail_url": f"https://i.ytimg.com/vi/{video.video_id}/mqdefault.jpg",
            "watch_url": f"https://www.youtube.com/watch?v={video.video_id}",
            "duration": None  
        })
    
    return results

def get_video_info(url):
    try:
        yt = YouTube(url)
        return {
            "id": yt.video_id,
            "title": yt.title,
            "thumbnail_url": yt.thumbnail_url,
            "duration": yt.length,
            "author": yt.author
        }
    except Exception as e:
        raise Exception(f"Error getting video info: {str(e)}")

def progress_callback(stream, chunk, bytes_remaining, download_id, progress_dict):
    total = stream.filesize
    downloaded = total - bytes_remaining
    percent = (downloaded / total) * 100
    
    progress_dict[download_id]["progress"] = percent
    progress_dict[download_id]["status"] = "downloading"

def download_video(url, output_path, download_id, progress_dict):
    try:
        yt = YouTube(url)
        
        yt.register_on_progress_callback(
            lambda stream, chunk, bytes_remaining: 
            progress_callback(stream, chunk, bytes_remaining, download_id, progress_dict)
        )
        
        stream = yt.streams.get_highest_resolution()
        
        progress_dict[download_id]["status"] = "starting"
        file_path = stream.download(output_path=output_path)
        
        progress_dict[download_id]["status"] = "completed"
        progress_dict[download_id]["progress"] = 100
        progress_dict[download_id]["filename"] = file_path
        
        return file_path
    except Exception as e:
        progress_dict[download_id]["status"] = "error"
        progress_dict[download_id]["error"] = str(e)
        raise Exception(f"Error downloading video: {str(e)}")

def download_audio(url, output_path, download_id, progress_dict):
    try:
        yt = YouTube(url)
        
        yt.register_on_progress_callback(
            lambda stream, chunk, bytes_remaining: 
            progress_callback(stream, chunk, bytes_remaining, download_id, progress_dict)
        )
        
        stream = yt.streams.get_audio_only()
        
        progress_dict[download_id]["status"] = "starting"
        file_path = stream.download(output_path=output_path)
        
        progress_dict[download_id]["status"] = "completed"
        progress_dict[download_id]["progress"] = 100
        progress_dict[download_id]["filename"] = file_path
        
        return file_path
    except Exception as e:
        progress_dict[download_id]["status"] = "error"
        progress_dict[download_id]["error"] = str(e)
        raise Exception(f"Error downloading audio: {str(e)}")

