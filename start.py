import os
import uvicorn
from data_collector import collect_all_data


def main():
    # Collect or refresh data first (this script exits after completeness)
    collect_all_data()

    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0"

    print(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port)


if __name__ == "__main__":
    main()
