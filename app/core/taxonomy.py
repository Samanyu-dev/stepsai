"""
Steps AI Job Competencies Taxonomy Module.

This module defines standard requirements for primary role domains (Software Engineer,
Data Analyst, Product Manager) and implements the programmatical skill gap analyzer.
"""

from typing import Dict, List

# Core technical competencies taxonomy for hackathon evaluation
ROLE_TAXONOMY: Dict[str, List[str]] = {
    "software engineer": [
        "python", "javascript", "sql", "git", "docker", "system design", "algorithms",
        "fastapi", "django", "react", "postgresql", "rest api", "testing", "cloud"
    ],
    "data analyst": [
        "sql", "python", "pandas", "tableau", "excel", "statistics", "data visualization",
        "power bi", "pandas", "numpy", "data cleaning", "etl", "reporting", "r"
    ],
    "product manager": [
        "product strategy", "agile", "scrum", "roadmapping", "analytics", "a/b testing",
        "wireframing", "jira", "sql", "metrics", "user research", "stakeholder management"
    ]
}

def analyze_skill_gaps(job_role: str, candidate_skills: List[str]) -> List[str]:
    """
    Compares candidate skills against industry standards taxonomy for the job role
    and calculates programmatically any gaps (missing skills).
    """
    normalized_role = job_role.lower()
    
    # Resolve target matching role template
    target_role = "software engineer"
    if "analyst" in normalized_role or "data" in normalized_role:
        target_role = "data analyst"
    elif "product" in normalized_role or "manager" in normalized_role or "pm" in normalized_role:
        target_role = "product manager"
        
    required_skills = ROLE_TAXONOMY.get(target_role, ROLE_TAXONOMY["software engineer"])
    
    # Normalize candidate skills
    normalized_candidate_skills = {s.lower().strip() for s in candidate_skills}
    
    # Calculate missing core skills
    gap_skills = []
    for skill in required_skills:
        if skill not in normalized_candidate_skills:
            gap_skills.append(skill.title())
            
    # Return max 5 relevant missing skills for guidance suggestions
    return gap_skills[:5]
