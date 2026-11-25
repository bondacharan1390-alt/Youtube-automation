import asyncio
import ctypes
import gc
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


def get_system_ram_gb() -> Tuple[float, float]:
    """Detect system RAM using Windows kernel32 GlobalMemoryStatusEx with fallback."""
    total_gb = 16.0
    free_gb = 4.0
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            total_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
            free_gb = round(stat.ullAvailPhys / (1024 ** 3), 2)
    except Exception:
        pass
    return total_gb, free_gb


class HardwareTaskQueue:
    """
    Sequential Hardware Guard for Windows 11 with 8 GB RAM baseline.
    Ensures heavy tasks (Voice synthesis, Stable Diffusion image rendering, Video encoding)
    never run concurrently to prevent RAM exhaustion and GPU VRAM collisions.
    Supports re-entrant execution for nested task hierarchies.
    """
    _lock = asyncio.Lock()
    _owner_task: Any = None

    @classmethod
    async def run_sequential(cls, task_name: str, coroutine):
        current = asyncio.current_task()
        if cls._owner_task is not None and cls._owner_task == current:
            # Re-entrant call from within the same asyncio task hierarchy
            return await coroutine

        async with cls._lock:
            cls._owner_task = current
            # 1. Hardware memory check before running task
            total_ram, free_ram = get_system_ram_gb()
            logger.info(f"Executing '{task_name}' - RAM: {free_ram} GB free / {total_ram} GB total")
            
            # If free memory is critically low (< 1.0 GB), trigger explicit garbage collection
            if free_ram < 1.0:
                gc.collect()

            try:
                result = await coroutine
                return result
            finally:
                cls._owner_task = None
                # Immediate memory cleanup after each heavy task
                gc.collect()

    @classmethod
    def get_hardware_status(cls) -> Dict[str, Any]:
        total_ram, free_ram = get_system_ram_gb()
        return {
            "total_ram_gb": total_ram,
            "free_ram_gb": free_ram,
            "is_memory_safe": free_ram >= 1.5,
            "queue_locked": cls._lock.locked(),
        }
