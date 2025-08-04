from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from rich import print

scheduler = AsyncIOScheduler()

def start_scheduler():
    try:
        scheduler.start()
        print("[bold green][✓][/bold green] Scheduler started.")
    except Exception as e:
        print(f"[bold red]Scheduler failed to start:[/bold red] {e}")

def schedule_task(task_func, seconds=60, job_id=None):
    scheduler.add_job(
        task_func,
        trigger=IntervalTrigger(seconds=seconds),
        next_run_time=datetime.now(),
        id=job_id,
        replace_existing=True,
    )
