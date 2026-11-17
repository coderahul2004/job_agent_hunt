"""Task definitions for the JobHunt Agent Squad."""
from crewai import Task
from src.config import JOB_SEARCH_LIMIT, TAILORED_APPLICATIONS_PATH
class JobHuntTasks:
    def __init__(self, role: str, resume_text: str, top_n: int):
        self.role = role
        self.resume_text = resume_text
        self.top_n = top_n
    def scrape(self, agent) -> Task:
        return Task(
            description=(
                f"Search for genuine current remote job listings related to "
                f"'{self.role}'. Use the Remote Job Search tool exactly once "
                "with the role exactly as provided. The tool searches related "
                "titles internally and returns JSON. Inspect the returned "
                "status carefully. If status is api_error, report an API "
                "failure and do not claim that no vacancies exist. If status "
                "is no_jobs_found, report that no relevant listings were "
                "retrieved. If status is success, report the exact "
                "jobs_retrieved count and preserve each real listing's title, "
                "company, URL and description. Never invent listings or URLs."
            ),
            expected_output=(
                "The tool's search status, exact number of retrieved jobs, "
                "and the genuine job listing data returned by the tool."
            ),
            agent=agent,
        )
    def match(self, agent, scrape_task: Task) -> Task:
        return Task(
            description=(
                "Candidate resume:\n"
                f"{self.resume_text}\n\n"
                "Use only the genuine job listings returned by the previous "
                "scrape task. The scraper output is a JSON object containing "
                "a status and, when successful, a jobs array. If the scraper "
                "status is api_error or no_jobs_found, return an empty JSON "
                "array and explain the scraper status. Do not invent jobs. "
                "For each actual listing, score resume fit from 0 to 100 "
                "based on required skills, projects, experience, seniority "
                "and role relevance. Do not reject a job merely because the "
                "candidate lacks a preferred rather than required skill. "
                f"Select no more than {self.top_n} strongest matches. "
                "Return a JSON array; each object must contain title, "
                "company, url, description, match_score and reason. "
                "Keep each reason under 30 words. Do not invent candidate "
                "qualifications or job requirements."
            ),
            expected_output=(
                f"A JSON array containing at most {self.top_n} genuine "
                "matched jobs, each with match_score and reason. Return [] "
                "when there are no genuine jobs to evaluate."
            ),
            agent=agent,
            context=[scrape_task],
        )
    def tailor(self, agent, match_task: Task) -> Task:
        return Task(
            description=(
                "Candidate resume:\n"
                f"{self.resume_text}\n\n"
                "For every job in the previous matching task, create: "
                "(1) a specific cover letter of at most 150 words, and "
                "(2) three tailored resume bullet suggestions. "
                "Use only facts supported by the resume. Do not imply that "
                "the candidate has already applied. Include the job title, "
                "company, job URL and match score. If there are no matched "
                "jobs, explain that there are no applications to tailor."
            ),
            expected_output=(
                "A Markdown report with a separate section for each "
                "matched job, or a clear no-matches explanation."
            ),
            agent=agent,
            context=[match_task],
            output_file=str(TAILORED_APPLICATIONS_PATH),
        )
    def track(self, agent, match_task: Task, tailor_task: Task) -> Task:
        return Task(
            description=(
                "Read the selected jobs from the matching task. Convert "
                "them into a valid JSON array. Each object must contain "
                "title, company, url and match_score. Call the Application "
                "Tracker tool exactly once with that JSON. Do not log jobs "
                "if the matching task returned an empty list. Report the "
                "exact number of records the tool confirms."
            ),
            expected_output=(
                "A confirmation stating how many records were saved, "
                "or that none were saved."
            ),
            agent=agent,
            context=[match_task],
        )
 