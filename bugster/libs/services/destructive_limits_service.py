"""
Destructive agent limit logic for Bugster CLI
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict


def apply_destructive_agent_limit(
    page_agents: List[tuple[str, str]], max_agents: Optional[int] = None
) -> tuple[List[tuple[str, str]], dict]:
    """
    Apply destructive agent limit logic to select a prioritized subset of agents.
    
    Args:
        page_agents: List of (page, agent) tuples
        max_agents: Maximum number of agents to run (if None, no limit)
    
    Returns:
        Tuple of (limited list of (page, agent) tuples, agent distribution dict)
    """
    if max_agents is None:
        return page_agents, {}
    
    # Count total agents
    total_agents = len(page_agents)
    
    if total_agents <= max_agents:
        return page_agents, {}
    
    # Group agents by type for prioritization
    agent_groups = group_agents_by_type(page_agents)
    
    # Apply prioritized selection logic
    selected_agents, agent_distribution = select_prioritized_agents(agent_groups, max_agents)
    
    return selected_agents, agent_distribution


def group_agents_by_type(page_agents: List[tuple[str, str]]) -> dict[str, List[tuple[str, str]]]:
    """
    Group page agents by their agent type.
    
    Args:
        page_agents: List of (page, agent) tuples
    
    Returns:
        Dictionary mapping agent types to lists of (page, agent) tuples
    """
    agent_groups = defaultdict(list)
    
    for page, agent in page_agents:
        agent_groups[agent].append((page, agent))
    
    return dict(agent_groups)


def select_prioritized_agents(
    agent_groups: dict[str, List[tuple[str, str]]], max_agents: int
) -> tuple[List[tuple[str, str]], dict]:
    """
    Select prioritized agents based on agent type priority.
    
    UI Crashers (ui_crasher) have highest priority, followed by From Destroyer (form_destroyer),
    then other agent types.
    
    Args:
        agent_groups: Dictionary mapping agent types to (page, agent) tuples
        max_agents: Maximum number of agents to select
    
    Returns:
        Tuple of (list of selected (page, agent) tuples, agent distribution dict)
    """
    # Define priority order - UI Crashers first, then From Destroyer, then others
    priority_order = ['ui_crasher', 'form_destroyer']
    
    selected_agents = []
    agent_distribution = {}
    
    # First, select from priority agents
    for agent_type in priority_order:
        if agent_type in agent_groups and len(selected_agents) < max_agents:
            agents_to_take = min(
                len(agent_groups[agent_type]), 
                max_agents - len(selected_agents)
            )
            
            if agents_to_take > 0:
                selected_from_type = agent_groups[agent_type][:agents_to_take]
                selected_agents.extend(selected_from_type)
                agent_distribution[agent_type] = agents_to_take
    
    # Then, select from remaining agent types if we still have capacity
    remaining_agent_types = [
        agent_type for agent_type in agent_groups.keys() 
        if agent_type not in priority_order
    ]
    
    # Sort remaining types for consistent behavior
    remaining_agent_types.sort()
    
    for agent_type in remaining_agent_types:
        if len(selected_agents) >= max_agents:
            break
            
        agents_to_take = min(
            len(agent_groups[agent_type]), 
            max_agents - len(selected_agents)
        )
        
        if agents_to_take > 0:
            selected_from_type = agent_groups[agent_type][:agents_to_take]
            selected_agents.extend(selected_from_type)
            agent_distribution[agent_type] = agents_to_take
    
    return selected_agents[:max_agents], agent_distribution


def count_total_agents(page_agents: List[tuple[str, str]]) -> int:
    """
    Count total number of agents.
    
    Args:
        page_agents: List of (page, agent) tuples
    
    Returns:
        Total number of agents
    """
    return len(page_agents)


def get_destructive_agent_limit_from_config() -> Optional[int]:
    """
    Get destructive agent limit from configuration.
    This can be extended to read from config file, environment variable, etc.
    
    Returns:
        Maximum number of agents to run, or None if no limit
    """
    return 5


def get_agent_priority_display_name(agent_type: str) -> str:
    """
    Get display name for agent type for console messages.
    
    Args:
        agent_type: The agent type identifier
    
    Returns:
        Human-readable display name
    """
    display_names = {
        'ui_crasher': 'UI Crashers',
        'form_destroyer': 'From Destroyer',
    }
    return display_names.get(agent_type, agent_type)