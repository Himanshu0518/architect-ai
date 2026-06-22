from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from server.schemas import DesignReview


@CrewBase
class ReviewCrew:
    """Critically reviews the full system design and provides scored, actionable feedback."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def design_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["design_reviewer"],
            verbose=True,
        )

    @task
    def review_design_task(self) -> Task:
        return Task(
            config=self.tasks_config["review_design_task"],
            output_pydantic=DesignReview,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
