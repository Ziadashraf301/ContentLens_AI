import asyncio

ollama_gpu_limit = asyncio.Semaphore(4)
request_limit = asyncio.Semaphore(2)