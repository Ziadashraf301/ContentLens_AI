import asyncio

ollama_gpu_limit = asyncio.Semaphore(6)
request_limit = asyncio.Semaphore(3)
