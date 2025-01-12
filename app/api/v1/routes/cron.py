from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Optional, List
from app.core.security import get_api_key
from app.core.config import settings
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import requests
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Store job configurations
job_configs = {}

# Default schedule settings
DEFAULT_SCHEDULES = [
    {
        "endpoint": "/api/v1/audio/all",
        "minutes": 5,
        "description": "Periodically fetch all audio files"
    }
]

def execute_scheduled_task(endpoint: str):
    """Execute a scheduled API task with proper error handling"""
    try:
        response = requests.get(
            f"{settings.API_BASE_URL}{endpoint}",
            headers={"x-api-key": settings.API_KEY}
        )
        logger.info(f"Cron job executed for endpoint {endpoint} with status {response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected error executing task for endpoint {endpoint}: {str(e)}")

def initialize_default_schedules():
    """Initialize default schedules when server starts"""
    try:
        # Remove all existing jobs
        scheduler.remove_all_jobs()
        job_configs.clear()
        
        # Set up default schedules
        for idx, schedule in enumerate(DEFAULT_SCHEDULES, 1):
            job_id = f"default_job_{idx}"
            
            # Add job
            scheduler.add_job(
                execute_scheduled_task,
                'interval',
                minutes=schedule['minutes'],
                id=job_id,
                args=[schedule['endpoint']],
                replace_existing=True
            )
            
            # Save configuration
            job_configs[job_id] = {
                "endpoint": schedule['endpoint'],
                "minutes": schedule['minutes'],
                "description": schedule['description'],
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "is_default": True
            }
            
            logger.info(f"Default schedule initialized: {job_id} - {schedule['endpoint']}")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing default schedules: {str(e)}")
        return False

@router.post("/initialize")
async def init_default_schedules(
    _api_key: str = Depends(get_api_key)
):
    """Endpoint to manually initialize default schedules"""
    if initialize_default_schedules():
        return {
            "message": "Default schedules initialized successfully",
            "jobs": job_configs
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize default schedules"
        )

@router.post("/jobs")
async def create_cron_job(
    endpoint: str,
    minutes: int,
    _api_key: str = Depends(get_api_key)
):
    """Create a new cron job"""
    try:
        job_id = f"job_{len(job_configs) + 1}"
        
        # Remove existing job if exists
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        # Add new job
        scheduler.add_job(
            execute_scheduled_task,
            'interval',
            minutes=minutes,
            id=job_id,
            args=[endpoint],
            replace_existing=True
        )
        
        # Save configuration
        job_configs[job_id] = {
            "endpoint": endpoint,
            "minutes": minutes,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        return {
            "job_id": job_id,
            "message": f"Cron job created successfully. Endpoint {endpoint} will be called every {minutes} minutes",
            "config": job_configs[job_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs")
async def list_jobs(
    _api_key: str = Depends(get_api_key)
):
    """List all cron jobs"""
    return {
        "jobs": job_configs,
        "total": len(job_configs)
    }

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    _api_key: str = Depends(get_api_key)
):
    """Get a specific cron job"""
    if job_id not in job_configs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = scheduler.get_job(job_id)
    next_run = job.next_run_time.isoformat() if job else None
    
    return {
        **job_configs[job_id],
        "next_run": next_run
    }

@router.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    minutes: int,
    _api_key: str = Depends(get_api_key)
):
    """Update cron job interval"""
    if job_id not in job_configs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found in scheduler")
        
        # Modify interval
        scheduler.modify_job(
            job_id,
            trigger='interval',
            minutes=minutes
        )
        
        # Update configuration
        job_configs[job_id]["minutes"] = minutes
        job_configs[job_id]["updated_at"] = datetime.now().isoformat()
        
        return {
            "message": f"Job interval updated to {minutes} minutes",
            "config": job_configs[job_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    _api_key: str = Depends(get_api_key)
):
    """Pause a cron job"""
    if job_id not in job_configs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        scheduler.pause_job(job_id)
        job_configs[job_id]["status"] = "paused"
        return {"message": f"Job {job_id} paused successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    _api_key: str = Depends(get_api_key)
):
    """Resume a paused cron job"""
    if job_id not in job_configs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        scheduler.resume_job(job_id)
        job_configs[job_id]["status"] = "active"
        return {"message": f"Job {job_id} resumed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    _api_key: str = Depends(get_api_key)
):
    """Delete a cron job"""
    if job_id not in job_configs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        scheduler.remove_job(job_id)
        del job_configs[job_id]
        return {"message": f"Job {job_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 