import asyncio

ollama_gpu_limit = asyncio.Semaphore(10)
