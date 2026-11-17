"""Definitions for the four JobHunt agents."""
from crewai import Agent, LLM

from src.config import GROQ_API_KEY, MAX_OUTPUT_TOKENS, MODEL
from src.tools.job_scraper import JobSearchTool
from src.tools.tracker import ApplicationTrackerTool


class JobHuntAgents:
    """Build the agents used in the sequential crew."""

    def __init__(self):
        # The key is passed directly, so the key from .env is always the one used.
        self.llm = LLM(
            model=MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.2,
            timeout=120,
            max_tokens=MAX_OUTPUT_TOKENS,
        )

    def scraper(self) -> Agent:
        return Agent(
            role="Job Scraper",
            goal="Find genuine, currently listed jobs matching {role}.",
            backstory=(
                "You are a careful job researcher. Use the Remote Job Search tool "
                "only once. Never invent companies, job titles, descriptions or URLs. "
                "Return structured job information."
            ),
            tools=[JobSearchTool()],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3,  # stops the agent from calling the tool again and again
        )

    def matcher(self) -> Agent:
        return Agent(
            role="Resume Matcher",
            goal="Compare each retrieved job with the candidate resume and select the best {top_n}.",
            backstory=(
                "You are a technical recruiter. Evaluate actual skills, experience, "
                "projects, seniority and role requirements. Do not invent candidate skills."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )

    def tailor(self) -> Agent:
        return Agent(
            role="Application Tailor",
            goal="Create honest, job-specific resume bullets and cover letters.",
            backstory=(
                "You are an ATS-aware career coach. Tailor applications using only "
                "the candidate's real background. Never claim experience or skills "
                "that are not supported by the resume."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )

    def tracker(self) -> Agent:
        return Agent(
            role="Application Tracker",
            goal="Save the selected job opportunities and their match scores to the CSV tracker.",
            backstory=(
                "You are an accurate application coordinator. Use the Application "
                "Tracker tool with valid JSON records. Do not claim a record was saved "
                "unless the tool confirms it."
            ),
            tools=[ApplicationTrackerTool()],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )