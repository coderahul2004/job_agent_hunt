"""CLI entry point.

Usage:
    python main.py "python developer" data/resume_sample.txt
"""
import argparse

from src.config import TOP_N
from src.crew import JobHuntCrew
from src.tools.resume_reader import read_resume


def main() -> None:
    parser = argparse.ArgumentParser(description="JobHunt Agent Squad")
    parser.add_argument("role", nargs="?", default="python developer")
    parser.add_argument("resume", nargs="?", default="data/resume_sample.txt")
    args = parser.parse_args()

    resume_text = read_resume(args.resume)
    if not resume_text:
        raise ValueError("The resume is empty or could not be read.")

    print(f"\nJobHunt Agent Squad searching for: {args.role}\n")
    result = JobHuntCrew().run(args.role, resume_text, TOP_N)
    print("\n===== FINAL REPORT =====\n")
    print(result)


if __name__ == "__main__":
    main()
