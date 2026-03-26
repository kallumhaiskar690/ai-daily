import sys

def run_ai_daily():
    from pipelines.ai_daily.run import main as ai_daily_main
    ai_daily_main()

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [pipeline]")
        print("Available pipelines: ai_daily")
        return

    pipeline = sys.argv[1]

    if pipeline == "ai_daily":
        run_ai_daily()
    else:
        print(f"Unknown pipeline: {pipeline}")

if __name__ == "__main__":
    main()
