import sys

def run_ai_daily():
    from pipelines.ai_daily.run import main as ai_daily_main
    ai_daily_main()

PIPELINES = {
    "ai_daily": run_ai_daily,
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [pipeline]")
        print("Available:", ", ".join(PIPELINES.keys()))
        return

    for name in sys.argv[1:]:
        if name in PIPELINES:
            print(f"Running: {name}")
            PIPELINES[name]()
        else:
            print(f"Unknown pipeline: {name}")

if __name__ == "__main__":
    main()
