"""Tests for destructive limits service."""

import pytest
from bugster.libs.services.destructive_limits_service import (
    apply_destructive_agent_limit,
    group_agents_by_type,
    select_prioritized_agents,
    count_total_agents,
    get_agent_priority_display_name,
)


class TestDestructiveLimitsService:
    """Test cases for destructive limits service."""

    def test_apply_destructive_agent_limit_no_limit(self):
        """Test that no limit returns all agents."""
        page_agents = [
            ("page1", "ui_crasher"),
            ("page2", "form_destroyer"),
            ("page3", "ui_crasher"),
        ]
        
        result, distribution = apply_destructive_agent_limit(page_agents, None)
        
        assert result == page_agents
        assert distribution == {}

    def test_apply_destructive_agent_limit_under_limit(self):
        """Test that under limit returns all agents."""
        page_agents = [
            ("page1", "ui_crasher"),
            ("page2", "form_destroyer"),
        ]
        
        result, distribution = apply_destructive_agent_limit(page_agents, 5)
        
        assert result == page_agents
        assert distribution == {}

    def test_apply_destructive_agent_limit_with_prioritization(self):
        """Test that agents are properly prioritized and limited."""
        page_agents = [
            ("page1", "form_destroyer"),
            ("page2", "ui_crasher"),
            ("page3", "form_destroyer"),
            ("page4", "ui_crasher"),
            ("page5", "other_agent"),
            ("page6", "ui_crasher"),
            ("page7", "form_destroyer"),
        ]
        
        result, distribution = apply_destructive_agent_limit(page_agents, 5)
        
        # Should have exactly 5 agents
        assert len(result) == 5
        
        # UI crashers should be prioritized first
        agent_types = [agent for _, agent in result]
        ui_crasher_count = agent_types.count('ui_crasher')
        form_destroyer_count = agent_types.count('form_destroyer')
        
        # Should get all 3 ui_crashers and 2 form_destroyers
        assert ui_crasher_count == 3
        assert form_destroyer_count == 2
        
        # Distribution should be correct
        assert distribution == {'ui_crasher': 3, 'form_destroyer': 2}

    def test_group_agents_by_type(self):
        """Test grouping agents by type."""
        page_agents = [
            ("page1", "ui_crasher"),
            ("page2", "form_destroyer"),
            ("page3", "ui_crasher"),
        ]
        
        groups = group_agents_by_type(page_agents)
        
        expected = {
            'ui_crasher': [("page1", "ui_crasher"), ("page3", "ui_crasher")],
            'form_destroyer': [("page2", "form_destroyer")],
        }
        assert groups == expected

    def test_select_prioritized_agents_ui_crasher_priority(self):
        """Test that UI crashers are selected first."""
        agent_groups = {
            'form_destroyer': [("page1", "form_destroyer"), ("page2", "form_destroyer")],
            'ui_crasher': [("page3", "ui_crasher"), ("page4", "ui_crasher")],
            'other_agent': [("page5", "other_agent")],
        }
        
        result, distribution = select_prioritized_agents(agent_groups, 3)
        
        # Should get all ui_crashers first, then form_destroyer
        agent_types = [agent for _, agent in result]
        assert agent_types == ['ui_crasher', 'ui_crasher', 'form_destroyer']
        assert distribution == {'ui_crasher': 2, 'form_destroyer': 1}

    def test_count_total_agents(self):
        """Test counting total agents."""
        page_agents = [
            ("page1", "ui_crasher"),
            ("page2", "form_destroyer"),
            ("page3", "ui_crasher"),
        ]
        
        count = count_total_agents(page_agents)
        assert count == 3

    def test_get_agent_priority_display_name(self):
        """Test getting display names for agent types."""
        assert get_agent_priority_display_name('ui_crasher') == 'UI Crashers'
        assert get_agent_priority_display_name('form_destroyer') == 'From Destroyer'
        assert get_agent_priority_display_name('unknown_agent') == 'unknown_agent'

    def test_priority_order_consistency(self):
        """Test that priority order is consistent."""
        # Create a scenario with many agents to ensure UI crashers always come first
        page_agents = []
        for i in range(10):
            page_agents.append((f"page{i}", "form_destroyer"))
        for i in range(10, 20):
            page_agents.append((f"page{i}", "ui_crasher"))
        for i in range(20, 30):
            page_agents.append((f"page{i}", "other_agent"))
        
        result, distribution = apply_destructive_agent_limit(page_agents, 5)
        
        # Should get all 5 as ui_crashers since they have priority
        agent_types = [agent for _, agent in result]
        assert all(agent == 'ui_crasher' for agent in agent_types)
        assert distribution == {'ui_crasher': 5}