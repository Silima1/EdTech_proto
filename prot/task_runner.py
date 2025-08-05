
import asyncio
import logging
import traceback
import os
from asyncio import Queue, timeout
from typing import Coroutine, Final
import openai
from db import get_next_tasks, report_task_error, fetch_finished_tasks

logger = logging.getLogger(__name__)

MINUTE: Final[int] = 60
TASK_TIMEOUT_SECS: Final[int] = 15 * MINUTE
EXECUTORS: Final[int] = 5

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")


async def grade_with_ai(task_data: dict):
    try:
        prompt = (
            f"Avalie este trabalho de forma objetiva e diga se está de acordo com a área de tecnologia "
            f"(DevOps, programação, redes, etc). Se não estiver, atribua nota baixa e explique.\n\n"
            f"Trabalho:\n{task_data['submission_id']}\n"
        )
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um agente avaliador de trabalhos técnicos."},
                {"role": "user", "content": prompt}
            ]
        )
        feedback = response.choices[0].message.content.strip()

        result = {
            "user_id": task_data["user_id"],
            "assignment_id": task_data["assignment_id"],
            "submission_id": task_data["submission_id"],
            "feedback": feedback,
            "grade": "10" if "tecnologia" in feedback.lower() else "2"
        }
        fetch_finished_tasks().append(result)
    except Exception as e:
        raise RuntimeError(f"Erro ao usar OpenAI: {e}")


async def coro_wrapper(coro: Coroutine, task: dict):
    try:
        async with timeout(TASK_TIMEOUT_SECS):
            await coro
    except Exception as e:
        err_str = (
            f"Task runner failed! Exc: {str(e)} | exc_tb: {traceback.format_exc()}"
        )
        logger.exception(err_str)
        report_task_error(task["task_id"], err_str)


async def task_executor(work_queue: Queue):
    while True:
        task = await work_queue.get()
        await task
        work_queue.task_done()


async def task_feeder(work_queue: Queue):
    while True:
        try:
            if tasks := get_next_tasks(quantity=5):
                for task_ in tasks:
                    task_coro: Coroutine = grade_with_ai(task_)
                    await work_queue.put(coro_wrapper(task_coro, task_))
            else:
                await asyncio.sleep(5)
        except Exception as e:
            logger.exception(f"Task runner failure! Exc: {str(e)}")


async def main():
    work_queue: Queue = Queue(maxsize=50)
    task_executors: list[Coroutine] = [
        task_executor(work_queue) for _ in range(EXECUTORS)
    ]

    await asyncio.gather(*task_executors, task_feeder(work_queue))


if __name__ == "__main__":
    asyncio.run(main())
