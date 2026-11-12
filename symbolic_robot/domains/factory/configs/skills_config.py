# skill name -> (module, function). Checked against the manifest by:
#     python -m robot_agent.contract.check_manifest symbolic_robot.domains.factory --strict
SKILL_CONFIGS: dict = {
    'move': ('symbolic_robot.domains.factory.configs.ra_skills', 'move'),
    'find': ('symbolic_robot.domains.factory.configs.ra_skills', 'find'),
    'pick': ('symbolic_robot.domains.factory.configs.ra_skills', 'pick'),
    'place': ('symbolic_robot.domains.factory.configs.ra_skills', 'place'),
    'put_in': ('symbolic_robot.domains.factory.configs.ra_skills', 'put_in'),
    'open': ('symbolic_robot.domains.factory.configs.ra_skills', 'open'),
    'close': ('symbolic_robot.domains.factory.configs.ra_skills', 'close'),
    'say': ('symbolic_robot.domains.factory.configs.ra_skills', 'say'),
    'ask': ('symbolic_robot.domains.factory.configs.ra_skills', 'ask'),
    'look': ('symbolic_robot.domains.factory.configs.ra_skills', 'look'),
    'grasp_check': ('symbolic_robot.domains.factory.configs.ra_skills', 'grasp_check'),
    'pose': ('symbolic_robot.domains.factory.configs.ra_skills', 'pose'),
}
