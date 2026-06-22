from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from server.tools.custom_tool import (
    ArchitectureDiagramTool,
    SequenceDiagramTool,
    MermaidValidatorTool,
)


@CrewBase
class DocumentationCrew:
    """Compiles all design data into a publication-ready Markdown document with Mermaid diagrams."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def technical_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_writer"],
            tools=[
                ArchitectureDiagramTool(),
                SequenceDiagramTool(),
                MermaidValidatorTool(),
            ],
            verbose=True,
        )

    @task
    def generate_documentation_task(self) -> Task:
        return Task(
            config=self.tasks_config["generate_documentation_task"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
