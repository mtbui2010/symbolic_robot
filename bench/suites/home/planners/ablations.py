"""Ablation variants of the D arm, kept out of robot_agent_adapter.py (that file may not grow)."""
from .robot_agent_adapter import SageS8nFtD1Planner


class SageS8nFtD1NoRagPlanner(SageS8nFtD1Planner):
    """``sage_s8n_ft_d1`` with an empty seed pool (zero-shot SAGE): the only difference, the RAG ablation of the D arm."""
    name = "robot_agent:sage_s8n_ft_d1_norag"
    seed_pool = False
