import httpx

OLLAMA_BASE_URL = "http://localhost:11434"
TIMEOUT_SECONDS = 120.0


class OllamaUnavailableError(Exception):
    """Raised when Ollama is not reachable (connection refused or similar)."""


class OllamaTimeoutError(Exception):
    """Raised when the Ollama request exceeds the timeout."""


async def generate(model: str, prompt: str) -> str:
    """Send a prompt to Ollama and return the text response."""
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            return response.json()["response"]
    except httpx.ConnectError as exc:
        raise OllamaUnavailableError(
            f"Ollama is not running at {OLLAMA_BASE_URL}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise OllamaTimeoutError(
            f"Ollama request timed out after {TIMEOUT_SECONDS}s"
        ) from exc
