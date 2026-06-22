from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from server.schemas import SubsystemDesign


@CrewBase
class SubsystemCrew:
    """Produces detailed subsystem and component specifications from the architecture design."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def subsystem_designer(self) -> Agent:
        return Agent(
            config=self.agents_config["subsystem_designer"],
            verbose=True,
        )

    @task
    def design_subsystems_task(self) -> Task:
        return Task(
            config=self.tasks_config["design_subsystems_task"],
            output_pydantic=SubsystemDesign,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
