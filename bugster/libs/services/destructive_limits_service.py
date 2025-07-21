"""
Destructive agent limit logic for Bugster CLI
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict


def apply_destructive_limit(page_agents: List, max_agents: Optional[int] = None) -> Tuple[List, Dict]:
    """
    Apply destructive agent limit logic to select a representative subset of agents.
    
    Args:
        page_agents: List of PageAgent objects with 'page' and 'agents' attributes
        max_agents: Maximum number of agents to run (if None, no limit)
    
    Returns:
        Tuple of (limited list of page agents, agent distribution dict)
    """
    if max_agents is None:
        return page_agents, {}
    
    # Count total individual agents
    total_agents = count_total_agents(page_agents)
    
    if total_agents <= max_agents:
        return page_agents, {}
    
    # Group agents by type
    agent_groups = group_agents_by_type(page_agents)
    
    # Apply distribution logic with prioritization
    selected_page_agents, agent_distribution = select_representative_agents(agent_groups, max_agents)
    
    return selected_page_agents, agent_distribution


def group_agents_by_type(page_agents: List) -> Dict[str, List]:
    """
    Group agents by their type across all pages.
    
    Args:
        page_agents: List of PageAgent objects
    
    Returns:
        Dictionary mapping agent types to lists of (page, agent) tuples
    """
    agent_groups = defaultdict(list)
    
    for page_agent in page_agents:
        page = page_agent.page
        for agent in page_agent.agents:
            agent_groups[agent].append((page, agent))
    
    return dict(agent_groups)


def select_representative_agents(agent_groups: Dict[str, List], max_agents: int) -> Tuple[List, Dict]:
    """
    Select representative agents from groups with prioritization logic.
    UI Crasher agents are prioritized over Form Destroyer agents.
    
    Args:
        agent_groups: Dictionary mapping agent types to lists of (page, agent) tuples
        max_agents: Maximum number of agents to select
    
    Returns:
        Tuple of (list of selected page agents, agent distribution dict)
    """
    if not agent_groups or max_agents <= 0:
        return [], {}
    
    # Define priority order (UI Crasher first, then others)
    priority_agents = ["ui_crasher", "form_destroyer"]
    
    # Separate priority agents from others
    prioritized_groups = {}
    other_groups = {}
    
    for agent_type, agent_list in agent_groups.items():
        if agent_type in priority_agents:
            prioritized_groups[agent_type] = agent_list
        else:
            other_groups[agent_type] = agent_list
    
    # Sort priority agents by priority order
    sorted_priority_agents = []
    for priority_agent in priority_agents:
        if priority_agent in prioritized_groups:
            sorted_priority_agents.append((priority_agent, prioritized_groups[priority_agent]))
    
    # Add other agents sorted by name for consistency
    sorted_other_agents = sorted(other_groups.items())
    
    # Combine all agents in priority order
    all_agent_groups = sorted_priority_agents + sorted_other_agents
    
    selected_agents = []
    agent_distribution = {}
    remaining_slots = max_agents
    
    # First pass: distribute agents evenly across types
    if len(all_agent_groups) > 0:
        agents_per_type = max_agents // len(all_agent_groups)
        extra_slots = max_agents % len(all_agent_groups)
        
        for i, (agent_type, agent_list) in enumerate(all_agent_groups):
            if remaining_slots <= 0:
                break
                
            # Some agent types get one extra slot
            slots_for_type = agents_per_type + (1 if i < extra_slots else 0)
            slots_for_type = min(slots_for_type, len(agent_list), remaining_slots)
            
            if slots_for_type > 0:
                selected_agents.extend(agent_list[:slots_for_type])
                agent_distribution[agent_type] = slots_for_type
                remaining_slots -= slots_for_type
    
    # Convert back to PageAgent objects (define locally to avoid circular imports)
    class PageAgent:
        def __init__(self, page: str, agents: list):
            self.page = page
            self.agents = agents
    
    # Group selected agents by page
    page_agent_map = defaultdict(list)
    for page, agent in selected_agents:
        page_agent_map[page].append(agent)
    
    # Create PageAgent objects
    selected_page_agents = []
    for page, agents in page_agent_map.items():
        selected_page_agents.append(PageAgent(page=page, agents=agents))
    
    return selected_page_agents, agent_distribution


def count_total_agents(page_agents: List) -> int:
    """
    Count total number of individual agents across all pages.
    
    Args:
        page_agents: List of PageAgent objects
    
    Returns:
        Total number of agents
    """
    total = 0
    for page_agent in page_agents:
        total += len(page_agent.agents)
    return total


def get_destructive_limit_from_config() -> Optional[int]:
    """
    Get destructive agent limit from configuration.
    This can be extended to read from config file, environment variable, etc.
    
    Returns:
        Maximum number of agents to run, or None if no limit
    """
    return 5