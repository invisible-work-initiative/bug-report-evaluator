"""`python -m integration` - start the server. Access log is off so request lines are never recorded (INT-9)."""
import uvicorn

from .web import app


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False)


if __name__ == "__main__":
    main()
