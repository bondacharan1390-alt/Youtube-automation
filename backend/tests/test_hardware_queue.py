import asyncio
import pytest
from app.services.hardware_queue import HardwareTaskQueue

@pytest.mark.asyncio
async def test_hardware_task_queue_sequential():
    """
    Verifies that the hardware task queue ensures sequential execution
    and prevents concurrent execution race conditions.
    """
    execution_order = []

    async def mock_heavy_task(task_id: int, delay: float):
        execution_order.append(f"start_{task_id}")
        await asyncio.sleep(delay)
        execution_order.append(f"end_{task_id}")
        return task_id

    # Launch two simulated heavy tasks simultaneously
    t1 = HardwareTaskQueue.run_sequential("Task 1", mock_heavy_task(1, 0.05))
    t2 = HardwareTaskQueue.run_sequential("Task 2", mock_heavy_task(2, 0.02))

    results = await asyncio.gather(t1, t2)
    assert results == [1, 2]

    # Because of sequential lock, Task 1 must finish completely before Task 2 starts!
    assert execution_order == ["start_1", "end_1", "start_2", "end_2"]

def test_hardware_status_check():
    status = HardwareTaskQueue.get_hardware_status()
    assert "total_ram_gb" in status
    assert "free_ram_gb" in status
    assert status["total_ram_gb"] > 0
    assert isinstance(status["queue_locked"], bool)
