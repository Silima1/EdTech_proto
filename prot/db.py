from typing import List, Dict

# Simulando banco de dados em memória
TASKS = []
FINISHED_TASKS = []
TASK_ID_COUNTER = 5000


def create_new_task(user_id: str, submission_id: str, assignment_id: str) -> int:
    global TASK_ID_COUNTER
    task = {
        "task_id": TASK_ID_COUNTER,
        "user_id": user_id,
        "submission_id": submission_id,
        "assignment_id": assignment_id,
        "status": "pending"
    }
    TASKS.append(task)
    TASK_ID_COUNTER += 1
    return task["task_id"]


def get_next_tasks(quantity: int = 5) -> List[Dict]:
    return TASKS[:quantity]


def report_task_error(task_id: int, error_string: str) -> None:
    for task in TASKS:
        if task["task_id"] == task_id:
            task["status"] = "error"
            task["error"] = error_string
            break


def fetch_finished_tasks() -> List[Dict]:
    return FINISHED_TASKS