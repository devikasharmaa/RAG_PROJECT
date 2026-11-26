"""Stop oversized request bodies while they are still arriving.

Checking the file size inside the /upload function is too late: by then FastAPI
has already received the whole body and saved it to a temp file. This middleware
counts bytes as they come in and rejects the request with 413 as soon as it goes
over the limit, so a huge upload can't fill the disk or memory.
"""
from fastapi import HTTPException
from starlette.responses import JSONResponse


class MaxBodySizeMiddleware:
    def __init__(self, app, max_bytes, paths):
        self.app = app
        self.max_bytes = max_bytes
        self.paths = set(paths)

    def _too_large(self):
        mb = self.max_bytes // (1024 * 1024)
        return HTTPException(status_code=413,
                             detail=f"File too large. The limit is {mb} MB.")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] not in self.paths:
            await self.app(scope, receive, send)
            return

        # Fast path: the client told us the size up front
        length = dict(scope["headers"]).get(b"content-length")
        if length is not None and length.isdigit() and int(length) > self.max_bytes:
            error = self._too_large()
            await JSONResponse({"detail": error.detail}, status_code=413)(scope, receive, send)
            return

        # No (or a dishonest) Content-Length: count the bytes as they arrive
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise self._too_large()
            return message

        await self.app(scope, limited_receive, send)
