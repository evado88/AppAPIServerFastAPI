import httpx

client: httpx.AsyncClient | None = None

async def init_client():
    global client
    client = httpx.AsyncClient(timeout=10.0)

async def close_client():
    global client
    if client:
        await client.aclose()
        
def get_http_client():
    return client