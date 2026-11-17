"""Append matched job opportunities to a CSV tracker."""
import csv
import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.config import APPLICATIONS_LOG_PATH, OUTPUT_DIR

HEADERS = ["title", "company", "url", "match_score", "status"]


class TrackerInput(BaseModel):
    records_json: str = Field(
        ...,
        description="JSON array of records with title, company, url and match_score",
    )


class ApplicationTrackerTool(BaseTool):
    name: str = "Application Tracker"
    description: str = (
        "Save matched job opportunities to a CSV file. Input must be a JSON array "
        "with title, company, url and match_score."
    )
    args_schema: type[BaseModel] = TrackerInput

    def _run(self, records_json: str) -> str:
        try:
            records = json.loads(records_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON supplied to tracker: {exc}") from exc

        if not isinstance(records, list):
            raise ValueError("Tracker input must be a JSON array.")

        valid_records = []
        for record in records:
            if not isinstance(record, dict):
                continue
            if not all(record.get(key) for key in ("title", "company", "url")):
                continue
            valid_records.append(record)

        if not valid_records:
            return "No valid job records to save."

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        file_exists = APPLICATIONS_LOG_PATH.exists()

        with APPLICATIONS_LOG_PATH.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=HEADERS)
            if not file_exists or APPLICATIONS_LOG_PATH.stat().st_size == 0:
                writer.writeheader()

            for record in valid_records:
                writer.writerow(
                    {
                        "title": record.get("title", ""),
                        "company": record.get("company", ""),
                        "url": record.get("url", ""),
                        "match_score": record.get("match_score", ""),
                        "status": "shortlisted",
                    }
                )

        return (
            f"Successfully saved {len(valid_records)} job records to "
            f"{APPLICATIONS_LOG_PATH}."
        )
