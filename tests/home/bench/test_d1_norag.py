"""The D arm with an empty seed pool (the RAG ablation) differs from sage_s8n_ft_d1 only in the pool."""
from bench.suites.home import planners


def test_d1_norag_differs_from_d1_only_in_the_seed_pool_off():
    rag, norag = planners.planner_class("robot_agent:sage_s8n_ft_d1"), planners.planner_class("robot_agent:sage_s8n_ft_d1_norag")
    assert rag.seed_pool is True and norag.seed_pool is False
    assert norag.loop_options == rag.loop_options and norag.skill_attempts == rag.skill_attempts
    assert norag.manifest_overlay == rag.manifest_overlay
