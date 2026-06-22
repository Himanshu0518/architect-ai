from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    SerperDevTool
)
from server.schemas import ArchitectureDesign
from server.tools.custom_tool import ArchitectureDiagramTool
from dotenv import load_dotenv

load_dotenv()

@CrewBase
class ArchitectureCrew:
    """Designs a high-level system architecture from a RequirementSpec."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def system_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["system_architect"],
            tools=[ArchitectureDiagramTool(),SerperDevTool()],
            verbose=True,
        )

    @task
    def design_architecture_task(self) -> Task:
        return Task(
            config=self.tasks_config["design_architecture_task"],
            output_pydantic=ArchitectureDesign,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
