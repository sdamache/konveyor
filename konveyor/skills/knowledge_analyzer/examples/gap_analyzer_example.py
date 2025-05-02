"""
Example script to demonstrate the usage of the KnowledgeGapAnalyzerSkill.

This script shows how to use the KnowledgeGapAnalyzerSkill to analyze questions,
track user knowledge, and identify knowledge gaps.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path to allow importing the module
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

from konveyor.skills.knowledge_analyzer.knowledge_gap_analyzer import (
    KnowledgeGapAnalyzerSkill,
)
from konveyor.skills.knowledge_analyzer.taxonomy import KnowledgeTaxonomyLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run the example script."""
    logger.info("Starting Knowledge Gap Analyzer Example")

    # Create the analyzer
    try:
        analyzer = KnowledgeGapAnalyzerSkill()
        logger.info("Successfully created KnowledgeGapAnalyzerSkill")
    except Exception as e:
        logger.error(f"Failed to create KnowledgeGapAnalyzerSkill: {e}")
        return

    # Define a test user
    user_id = "test_user_1"

    # Simulate a series of questions from the user
    questions = [
        "How do I set up the CI/CD pipeline with GitHub Actions?",
        "What's the architecture of our microservices?",
        "How do we use Semantic Kernel in our project?",
        "What's our Git branching strategy?",
        "How do we handle monitoring and alerting?",
    ]

    print("\n=== Simulating User Questions ===")
    for i, question in enumerate(questions):
        print(f"\nQuestion {i+1}: {question}")

        # Analyze the question
        analysis_json = analyzer.analyze_question(question, user_id)
        analysis = json.loads(analysis_json)

        print("Relevant Domains:")
        for domain in analysis["relevant_domains"]:
            print(f"- {domain['name']} (Confidence: {domain['confidence']:.2f})")

    # Get the user's knowledge profile
    print("\n=== User Knowledge Profile ===")
    profile_json = analyzer.get_knowledge_profile(user_id)
    profile = json.loads(profile_json)

    for area in profile["knowledge_areas"]:
        print(f"- {area['name']}: {area['confidence']:.2f}")

    # Identify knowledge gaps
    print("\n=== Knowledge Gaps ===")
    gaps_json = analyzer.identify_gaps(user_id)
    gaps = json.loads(gaps_json)

    if gaps["knowledge_gaps"]:
        for gap in gaps["knowledge_gaps"]:
            print(f"- {gap['name']} (Confidence: {gap['confidence']:.2f})")
            print("  Suggested Resources:")
            for resource in gap["suggested_resources"]:
                print(f"  * {resource['title']} ({resource['url']})")
    else:
        print("No significant knowledge gaps identified.")

    # Get a learning path
    print("\n=== Learning Path for New Developer ===")
    path_json = analyzer.get_learning_path("new_developer", user_id)
    path = json.loads(path_json)

    print(f"Path: {path['path_name']}")
    print(f"Description: {path['path_description']}")
    print("Domains (in order of priority):")

    # Sort domains by priority (high, medium, low) and whether they're gaps
    sorted_domains = sorted(
        path["domains"],
        key=lambda d: (
            0 if d["priority"] == "high" else 1 if d["priority"] == "medium" else 2,
            0 if d["is_gap"] else 1,
            d["confidence"],
        ),
    )

    for domain in sorted_domains:
        domain_id = domain["id"]
        # Get the domain name from the taxonomy
        taxonomy = KnowledgeTaxonomyLoader()
        domain_obj = taxonomy.get_domain_by_id(domain_id)
        domain_name = domain_obj["name"] if domain_obj else domain_id

        gap_marker = "⚠️ GAP" if domain["is_gap"] else ""
        print(
            f"- {domain_name} (Priority: {domain['priority']}, Confidence: {domain['confidence']:.2f}) {gap_marker}"
        )


if __name__ == "__main__":
    main()
