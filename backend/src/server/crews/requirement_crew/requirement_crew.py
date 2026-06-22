from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    SerperDevTool
)
from server.schemas import RequirementSpec
from dotenv import load_dotenv

load_dotenv()

@CrewBase
class RequirementCrew:
    """Analyzes a company name and produces a structured RequirementSpec."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def requirement_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["requirement_analyst"],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @task
    def analyze_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_requirements_task"],
            output_pydantic=RequirementSpec,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
