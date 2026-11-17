"""Assemble and execute the JobHunt Agent Squad."""
from crewai import Crew, Process

from src.agents import JobHuntAgents
from src.config import MAX_RESUME_CHARS, validate_config
from src.tasks import JobHuntTasks


class JobHuntCrew:
    """Runs the four agents in sequence."""

    def run(self, role: str, resume_text: str, top_n: int) -> str:
        validate_config()

        if not role.strip():
            raise ValueError("Target job role cannot be empty.")
        if not resume_text.strip():
            raise ValueError("Resume text cannot be empty.")
        if top_n < 1:
            raise ValueError("top_n must be at least 1.")

        # Keep the resume short so every request stays under the token limit
        resume_text = resume_text[:MAX_RESUME_CHARS]

        agents = JobHuntAgents()
        tasks = JobHuntTasks(role, resume_text, top_n)

        scraper = agents.scraper()
        matcher = agents.matcher()
        tailor = agents.tailor()
        tracker = agents.tracker()

        scrape_task = tasks.scrape(scraper)
        match_task = tasks.match(matcher, scrape_task)
        tailor_task = tasks.tailor(tailor, match_task)
        track_task = tasks.track(tracker, match_task, tailor_task)

        crew = Crew(
            agents=[scraper, matcher, tailor, tracker],
            tasks=[scrape_task, match_task, tailor_task, track_task],
            process=Process.sequential,
            verbose=True,
            max_rpm=5,  # at most 5 LLM calls per minute, so we stay under the Groq limit
        )
        result = crew.kickoff(inputs={"role": role, "top_n": top_n})
        return str(result)