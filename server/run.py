import uvicorn
import os
from main import app

if __name__ == "__main__":
    port = int(os.environ.get("KYC_PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)