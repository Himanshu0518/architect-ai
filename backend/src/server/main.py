#!/usr/bin/env python
"""
ArchitectFlow — generates a complete system design document for any company/product.

Flow:
  1. RequirementCrew  → analyzes company name + optional user requirements → RequirementSpec
  2. ArchitectureCrew → designs high-level architecture                    → ArchitectureDesign
  3. SubsystemCrew    → details each component                             → SubsystemDesign
  4. ReviewCrew       → critiques and scores the design                    → DesignReview
  5. DocumentationCrew → compiles everything into final Markdown + Mermaid → final_document

Each crew's output is validated against a Pydantic schema defined in server/schemas/.
The validated JSON is then passed as the input to the next crew, forming a typed pipeline.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from crewai import LLM
from crewai.flow import Flow, listen, start

from server.crews.requirement_crew.requirement_crew import RequirementCrew
from server.crews.architecture_crew.architecture_crew import ArchitectureCrew
from server.crews.subsystem_crew.subsystem_crew import SubsystemCrew
from server.crews.review_crew.review_crew import ReviewCrew
from server.crews.documentation_crew.documentation_crew import DocumentationCrew


async def execute_with_fallback(crew_cls, inputs):
    """
    Executes a crew's kickoff async. If the primary LLM fails due to quota or rate limits,
    it automatically falls back to Groq.
    """
    try:
        return await crew_cls().crew().kickoff_async(inputs=inputs)
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "exhausted" in error_msg or "quota" in error_msg or "404" in error_msg:
            print(f"\n[Warning: Fallback Triggered] Primary LLM failed: {e}")
            print("Routing request to Groq (llama-3.3-70b-versatile)...")

            # Monkey-patch CrewAI's prompt caching which breaks Groq via litellm
            try:
                import crewai.llms.cache
                crewai.llms.cache.mark_cache_breakpoint = lambda m: m
            except Exception:
                pass

            groq_key = os.environ.get("GROQ_API_KEY")
            if not groq_key:
                raise ValueError("GROQ_API_KEY is not set in .env. Cannot fallback.") from e

            groq_llm = LLM(
                model="groq/llama-3.3-70b-versatile",
                api_key=groq_key
            )

            while True:
                try:
                    crew_instance = crew_cls().crew()
                    for agent in crew_instance.agents:
                        agent.llm = groq_llm
                    return await crew_instance.kickoff_async(inputs=inputs)
                except Exception as groq_err:
                    groq_error_msg = str(groq_err).lower()
                    if "rate limit" in groq_error_msg or "429" in groq_error_msg or "rate_limit" in groq_error_msg:
                        print(f"\nGroq rate limit hit. Sleeping for 60 seconds before retrying...")
                        await asyncio.sleep(60)
                        continue
                    raise groq_err
        raise e


class DesignState(BaseModel):
    """
    Flow state. All inter-crew payloads are stored as validated JSON strings,
    serialized from each crew's Pydantic output model.
    """
    company_name: str = Field(default="", description="Name of the company or product to design")
    user_requirements: str = Field(default="none", description="Optional user-provided requirements")
    # Serialized Pydantic outputs — each is the JSON of its respective schema
    requirements: str = Field(default="", description="JSON of RequirementSpec from RequirementCrew")
    architecture: str = Field(default="", description="JSON of ArchitectureDesign from ArchitectureCrew")
    subsystems: str = Field(default="", description="JSON of SubsystemDesign from SubsystemCrew")
    review: str = Field(default="", description="JSON of DesignReview from ReviewCrew")
    final_document: str = Field(default="", description="Final Markdown document from DocumentationCrew")


class ArchitectFlow(Flow[DesignState]):
    """
    Orchestrates a pipeline of AI crews to generate a complete system design
    document for any company or product name.

    Inter-crew contract: each crew writes a Pydantic model (defined in
    server/schemas/). The model is serialized to JSON and stored in DesignState,
    then passed as a string input to the next crew.
    """

    @start()
    def gather_input(self, crewai_trigger_payload: Optional[dict] = None):
        """Seed the flow state from the trigger payload or use defaults."""
        if crewai_trigger_payload:
            self.state.company_name = crewai_trigger_payload.get("company_name", "Uber")
            self.state.user_requirements = crewai_trigger_payload.get("user_requirements", "none")
        else:
            self.state.company_name = "Uber"
            self.state.user_requirements = "none"

        print(f"\n[ArchitectFlow] Starting for: {self.state.company_name}")
        print(f"  User requirements: {self.state.user_requirements}\n")

    @listen(gather_input)
    async def analyze_requirements(self):
        """Run RequirementCrew → validate output as RequirementSpec → store JSON."""
        print("[1/5] Analyzing requirements...")
        result = await execute_with_fallback(RequirementCrew, inputs={
            "company_name": self.state.company_name,
            "user_requirements": self.state.user_requirements,
        })
        # result.pydantic is a RequirementSpec instance (validated by CrewAI)
        self.state.requirements = result.pydantic.model_dump_json()
        print("[1/5] Requirements analysis complete.\n")
        await asyncio.sleep(5)

    @listen(analyze_requirements)
    async def design_architecture(self):
        """Run ArchitectureCrew → validate output as ArchitectureDesign → store JSON."""
        print("[2/5] Designing architecture...")
        result = await execute_with_fallback(ArchitectureCrew, inputs={
            "requirements": self.state.requirements,
        })
        self.state.architecture = result.pydantic.model_dump_json()
        print("[2/5] Architecture design complete.\n")
        await asyncio.sleep(5)

    @listen(design_architecture)
    async def detail_subsystems(self):
        """Run SubsystemCrew → validate output as SubsystemDesign → store JSON."""
        print("[3/5] Detailing subsystems...")
        result = await execute_with_fallback(SubsystemCrew, inputs={
            "requirements": self.state.requirements,
            "architecture": self.state.architecture,
        })
        self.state.subsystems = result.pydantic.model_dump_json()
        print("[3/5] Subsystem design complete.\n")
        await asyncio.sleep(5)

    @listen(detail_subsystems)
    async def review_design(self):
        """Run ReviewCrew → validate output as DesignReview → store JSON."""
        print("[4/5] Reviewing design...")
        result = await execute_with_fallback(ReviewCrew, inputs={
            "requirements": self.state.requirements,
            "architecture": self.state.architecture,
            "subsystems": self.state.subsystems,
        })
        self.state.review = result.pydantic.model_dump_json()
        print("[4/5] Design review complete.\n")
        await asyncio.sleep(5)

    @listen(review_design)
    async def generate_documentation(self):
        """Run DocumentationCrew → compile final Markdown (no Pydantic output)."""
        print("[5/5] Generating documentation...")
        result = await execute_with_fallback(DocumentationCrew, inputs={
            "company_name": self.state.company_name,
            "requirements": self.state.requirements,
            "architecture": self.state.architecture,
            "subsystems": self.state.subsystems,
            "review": self.state.review,
        })
        # DocumentationCrew produces raw Markdown — use result.raw
        self.state.final_document = result.raw

        # Save output to file
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        safe_name = self.state.company_name.lower().replace(" ", "_")
        output_path = output_dir / f"{safe_name}_system_design.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.state.final_document)

        print(f"\n[DONE] System design saved to: {output_path}\n")


# ──────────────────────────────────────────────────────────────────────────────
# Entry points (registered in pyproject.toml [project.scripts])
# ──────────────────────────────────────────────────────────────────────────────

def kickoff():
    """Run the flow with default inputs (for local testing)."""
    flow = ArchitectFlow()
    flow.kickoff()


def plot():
    """Generate a visual plot of the flow graph."""
    flow = ArchitectFlow()
    flow.plot()


def run_with_trigger():
    """
    Run the flow with named CLI flags (PowerShell-friendly).

    Usage:
        uv run run_with_trigger --company Airbnb
        uv run run_with_trigger --company Uber --requirements "handle 1M rides/day"
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a full system design document for a company."
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help='Name of the company or product (e.g. "Airbnb")',
    )
    parser.add_argument(
        "--requirements",
        type=str,
        default="none",
        help='Optional requirements string. Defaults to "none" (uses AI-generated assumptions).',
    )
    args = parser.parse_args()

    trigger_payload = {
        "company_name": args.company,
        "user_requirements": args.requirements,
    }

    flow = ArchitectFlow()
    result = flow.kickoff({"crewai_trigger_payload": trigger_payload})
    return result


if __name__ == "__main__":
    kickoff()
