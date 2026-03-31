import os
import uvicorn
from data_collector import collect_all_data


def main():
    # Skip data collection in Railway to speed up startup and avoid network issues
    if os.environ.get("SKIP_DATA_COLLECTION") != "true":
        collect_all_data()

    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0"

    print(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port)


if __name__ == "__main__":
    main()
