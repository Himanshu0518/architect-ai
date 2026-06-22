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


from server.llm.factory import LLMFactory

async def execute_with_fallback(crew_cls, inputs, progress_queue=None):
    """
    Executes a crew's kickoff async. Cycles through all available LLM providers 
    from LLMFactory if rate limits or quota errors occur, to avoid blocking.
    """
    providers = LLMFactory.get_all_providers()
    if not providers:
        # Fallback to default crew setup if no keys are found
        return await crew_cls().crew().kickoff_async(inputs=inputs)

    while True:
        for provider_name, provider_llm in providers:
            print(f"\n[Execute] Routing to provider: {provider_name}...")
            if progress_queue:
                await progress_queue.put({
                    "crew": "System",
                    "message": f"Using AI Provider: {provider_name.upper()}",
                    "status": "info"
                })
            try:
                # Monkey-patch CrewAI's prompt caching which breaks some providers via litellm
                try:
                    import crewai.llms.cache
                    crewai.llms.cache.mark_cache_breakpoint = lambda m: m
                except Exception:
                    pass

                crew_instance = crew_cls().crew()
                for agent in crew_instance.agents:
                    agent.llm = provider_llm
                
                return await crew_instance.kickoff_async(inputs=inputs)
            
            except Exception as e:
                error_msg = str(e).lower()
                # Trigger fallback on: rate limits, quota exhaustion, empty/null responses from provider
                is_retriable = (
                    "429" in error_msg
                    or "exhausted" in error_msg
                    or "quota" in error_msg
                    or "404" in error_msg
                    or "rate limit" in error_msg
                    or "rate_limit" in error_msg
                    or "none or empty" in error_msg
                    or "invalid response from llm" in error_msg
                    or "empty response" in error_msg
                    or "overloaded" in error_msg
                    or "service unavailable" in error_msg
                    or "529" in error_msg
                )
                if is_retriable:
                    msg = f"Provider {provider_name.upper()} returned an unusable response (quota/empty/overload). Switching to next model..."
                    print(f"[Fallback] {msg} | Error: {e}")
                    if progress_queue:
                        await progress_queue.put({
                            "crew": "System",
                            "message": msg,
                            "status": "warning"
                        })
                    continue
                else:
                    raise e
        
        # If we exhausted all providers, wait a bit and restart the cycle
        msg = "All providers hit rate limits! Sleeping for 30 seconds before retrying..."
        print(f"\n[Warning] {msg}")
        if progress_queue:
            await progress_queue.put({"crew": "System", "message": msg, "status": "warning"})
        await asyncio.sleep(30)


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
            self.progress_queue = crewai_trigger_payload.get("progress_queue")
        else:
            self.state.company_name = "Uber"
            self.state.user_requirements = "none"
            self.progress_queue = None

        print(f"\n[ArchitectFlow] Starting for: {self.state.company_name}")
        print(f"  User requirements: {self.state.user_requirements}\n")

    async def report_progress(self, crew_name: str, message: str, status: str = "running"):
        if hasattr(self, "progress_queue") and self.progress_queue:
            await self.progress_queue.put({"crew": crew_name, "message": message, "status": status})

    @listen(gather_input)
    async def analyze_requirements(self):
        """Run RequirementCrew → validate output as RequirementSpec → store JSON."""
        await self.report_progress("RequirementCrew", "Analyzing business and technical requirements...")
        print("[1/5] Analyzing requirements...")
        result = await execute_with_fallback(RequirementCrew, inputs={
            "company_name": self.state.company_name,
            "user_requirements": self.state.user_requirements,
        }, progress_queue=getattr(self, "progress_queue", None))
        # result.pydantic is a RequirementSpec instance (validated by CrewAI)
        self.state.requirements = result.pydantic.model_dump_json()
        print("[1/5] Requirements analysis complete.\n")
        await asyncio.sleep(3)

    @listen(analyze_requirements)
    async def design_architecture(self):
        """Run ArchitectureCrew → validate output as ArchitectureDesign → store JSON."""
        await self.report_progress("ArchitectureCrew", "Designing high-level system architecture and selecting technologies...")
        print("[2/5] Designing architecture...")
        result = await execute_with_fallback(ArchitectureCrew, inputs={
            "requirements": self.state.requirements,
        }, progress_queue=getattr(self, "progress_queue", None))
        self.state.architecture = result.pydantic.model_dump_json()
        print("[2/5] Architecture design complete.\n")
        # Write temp file for mermaid tools to read without needing huge LLM args
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "temp_architecture.json", "w", encoding="utf-8") as f:
            f.write(self.state.architecture)
        await asyncio.sleep(3)

    @listen(design_architecture)
    async def detail_subsystems(self):
        """Run SubsystemCrew → validate output as SubsystemDesign → store JSON."""
        await self.report_progress("SubsystemCrew", "Detailing subsystems, API endpoints, and database schemas...")
        print("[3/5] Detailing subsystems...")
        result = await execute_with_fallback(SubsystemCrew, inputs={
            "requirements": self.state.requirements,
            "architecture": self.state.architecture,
        }, progress_queue=getattr(self, "progress_queue", None))
        self.state.subsystems = result.pydantic.model_dump_json()
        print("[3/5] Subsystem design complete.\n")
        # Write temp file for mermaid tools to read without needing huge LLM args
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "temp_subsystems.json", "w", encoding="utf-8") as f:
            f.write(self.state.subsystems)
        await asyncio.sleep(3)

    # ── ReviewCrew temporarily disabled ──────────────────────────────────────
    # @listen(detail_subsystems)
    # async def review_design(self):
    #     """Run ReviewCrew → validate output as DesignReview → store JSON."""
    #     await self.report_progress("ReviewCrew", "Critiquing the design for scalability, reliability, and security gaps...")
    #     print("[4/5] Reviewing design...")
    #     result = await execute_with_fallback(ReviewCrew, inputs={
    #         "requirements": self.state.requirements,
    #         "architecture": self.state.architecture,
    #         "subsystems": self.state.subsystems,
    #     }, progress_queue=getattr(self, "progress_queue", None))
    #     self.state.review = result.pydantic.model_dump_json()
    #     print("[4/5] Design review complete.\n")
    #     await asyncio.sleep(3)

    @listen(detail_subsystems)  # now chains directly from SubsystemCrew (ReviewCrew disabled)
    async def generate_documentation(self):
        """Run DocumentationCrew → compile final Markdown (no Pydantic output)."""
        await self.report_progress("DocumentationCrew", "Compiling final Markdown document and generating Mermaid diagrams...")
        print("[4/4] Generating documentation...")
        result = await execute_with_fallback(DocumentationCrew, inputs={
            "company_name": self.state.company_name,
            "requirements": self.state.requirements,
            "architecture": self.state.architecture,
            "subsystems": self.state.subsystems,
            "review": "(Review step disabled — skipped for speed)",
        }, progress_queue=getattr(self, "progress_queue", None))
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
