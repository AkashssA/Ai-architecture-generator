import asyncio
from app.core.config import get_settings
from app.core.cache import InMemoryCache
from app.services.architecture_generator import ArchitectureGeneratorService

async def main():
    settings = get_settings()
    cache = InMemoryCache()
    service = ArchitectureGeneratorService(settings, cache)
    try:
        res = await service._generate_with_llm('A simple blog')
        print(res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
