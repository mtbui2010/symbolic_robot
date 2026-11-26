# Glossary

!!! abstract "In this page"
    - Every internal term of this site in one or two plain sentences, in alphabetical order of its anchor.
    - Each term has a stable anchor (`glossary.md#<term>`) and a link to the page that explains it.
    - The meanings were checked against the code at commit `a5cc7a4943aa`.

Names in `code font` are names in the repo. A few terms exist twice, once in the core and once in the household domain (for example the random streams); the entry says which.

<a id="aa-arm"></a>
**A/A arm.** An arm that repeats another arm's settings exactly (arm `A2` repeats `A` in the factory suites). The difference between the two is noise, so it shows how big a difference must be before it means something. See [Factory suites](../modules/factory-suites.md).

<a id="adapter"></a>
**adapter.** The file of a domain's pack (`configs/adapter.py`) that turns one step of robot_agent's plan into a skill call on the simulator. See [Factory pack](../modules/factory-pack.md).

<a id="answer-policy"></a>
**answer policy.** The rule by which the scripted person answers the robot's "where is the object?" question. The standard factory policies are `knows`, `unknown` and `wrong`; the messy ones are listed under [messy policy](#messy-policy). See [Factory tasks and scripted people](../modules/factory-tasks-and-people.md).

<a id="arm"></a>
**arm.** One run configuration of a campaign: a name (`A`, `B`, ...) and a dictionary of run options sent with every run. All arms play the same tasks and seeds, so they can be compared pairwise. See [Campaign runner](../modules/campaign-runner.md).

<a id="assumed-parameter"></a>
**assumed parameter.** A household profile number with `assumed: true`: it has no measured source, and its note says why it was assumed. The validator lists them (`python -m symbolic_robot.domains.home.profiles validate`). See [Household profiles](../modules/home-profiles.md).

<a id="bootstrap-interval"></a>
**bootstrap interval.** The 95 % interval of a paired difference in the factory statistics: 10,000 resamples of the per-task differences, drawn with a fixed seed (0), so it is the same on every run. See [Campaign statistics](../modules/campaign-statistics.md).

<a id="budget"></a>
**budget.** A limit on one household episode: calls (default 60), simulated seconds (1,800) and LLM calls (30). An episode that runs out ends with the status `budget`. See [The environment and the judge](../modules/episode-env-and-judge.md).

<a id="calldraws"></a>
**`CallDraws`.** A core helper that gives every skill call one fixed vector of uniform numbers, keyed by the seed, the skill, its arguments and how many times that call was made. At this commit no domain uses it; only `tests/test_core.py` does. See [Results, time and draws](../modules/results-time-draws.md).

<a id="campaign"></a>
**campaign.** One run of a factory suite: every (task, repeat, arm) is played against a running server, arms interleaved, and each episode is appended to `episodes.jsonl`. A rerun into the same folder skips what is done. See [Campaign runner](../modules/campaign-runner.md).

<a id="common-random-numbers"></a>
**common random numbers.** Two runs that meet the same fault at the same event because each random draw depends on a name (a key or a slot), not on how many draws came before. A planner that acts differently is then compared on equal luck. See [Determinism by seed](../learn/determinism.md).

<a id="delegate-suite"></a>
**delegate suite.** A suite with a `delegate` function: `python -m bench run` hands it every other argument and runs it in the same process. The four household suites are delegate suites; the factory suites are not. See [The bench front end](../modules/bench-front-end.md).

<a id="design-effect"></a>
**design effect.** How much the intervals must widen because episodes of one task are alike: `1 + (m0 - 1) * ICC`, never below 1. It is 1 when there is one episode per task. See [Metrics, report and compare](../modules/home-metrics-and-report.md).

<a id="domain"></a>
**domain.** One simulated world with its robot, registered by name (`factory`, `home`). It answers the hooks of `BaseDomain`: its worlds, profiles, how to make an episode, and so on. See [The domain protocol](../modules/domain-protocol.md).

<a id="effective-sample-size"></a>
**effective sample size.** The number of episodes divided by the design effect: how many independent episodes the data are worth. The headline household interval is a Wilson interval at this size. See [Metrics, report and compare](../modules/home-metrics-and-report.md).

<a id="env"></a>
**ENV.** robot_agent's description of the current world (places, objects, robot) for the planner. The server sets it as an attribute of the pack's `configs.tasks` module and sets it again whenever the world is rebuilt. See [Server glue](../modules/server-and-cli.md).

<a id="episode"></a>
**episode.** One run of one task with one seed in one fresh world, ending in a status and a truth that the judge reads. In the factory a task, repeat and arm make an episode; in the household a task and a seed do. See [How it works](../how-it-works/index.md).

<a id="failure-code"></a>
**failure code.** The reason a skill failed, as a short word. The household values are `absent`, `perception_unavailable`, `unreachable`, `blocked`, `grasp_failed`, `dropped`, `hw_fault`, `estop`, `timeout`, `cancelled` and `software`. See [Household world state](../modules/home-world.md).

<a id="false-success"></a>
**false success.** An episode where the planner claimed `done` and the judge says the goal was not reached. `false_success` counts it over all episodes; `false_success_given_claim` over the episodes that claimed. See [The environment and the judge](../modules/episode-env-and-judge.md).

<a id="floor"></a>
**floor.** The factory's word for a world: a YAML file of zones, benches, bins and a robot start (`assembly_hall`, `small_workshop`). See [Factory world](../modules/factory-world.md).

<a id="freeze-tag"></a>
**freeze tag.** The git tag (`home-sim-freeze-r19`) after which the household simulator may not change behaviour, except `domain.py`. A deliberate change needs a new tag. See [Parity and frozen behaviour](../modules/parity.md).

<a id="goal-atom"></a>
**goal atom.** One checkable fact about the true world, such as `on(object, place)`. A goal is a list of atoms joined by "and", with `not` and `any` allowed. See [Goals and the oracle](../modules/home-goals-and-oracle.md).

<a id="goal-condition-success"></a>
**goal-condition success.** The mean share of goal atoms that hold at the end (`gc`), over the episodes of kind `feasible` or `clarify`. It gives partial credit where `success` is all or nothing. See [Metrics, report and compare](../modules/home-metrics-and-report.md).

<a id="headless-ask"></a>
**headless ask.** The way the server asks a question without a screen: the `ask` skill emits a `listen` event and waits for an answer posted to `/agent/listen/<id>`. The benchmark's scripted person posts it. See [Server glue](../modules/server-and-cli.md).

<a id="help-rate"></a>
**help rate.** The share of household episodes in which the planner called `ask`. `correct_help_rate` is the share of those that were warranted. See [Metrics, report and compare](../modules/home-metrics-and-report.md).

<a id="house"></a>
**house.** The household domain's word for a world: a YAML file of rooms, furniture, objects and a person. There are eight, for example `senior_flat`. See [Household domain and houses](../modules/home-domain-and-houses.md).

<a id="infraerror"></a>
**`InfraError`.** Raised when a household run cannot be scored because the LLM server failed or the planner's code cannot be imported. The run aborts with exit code 3 and writes no summary, so a broken setup never looks like a score of 0 %. See [Household runner](../modules/home-runner.md).

<a id="injected"></a>
**injected.** A failure drawn by the failure model (a chance), as opposed to one caused by the world state (the object is not here). `SkillResult.injected` and the truth record it; the planner does not see it. See [Household failure model](../modules/home-outcomes.md).

<a id="judge"></a>
**judge.** The function that scores an episode against the true world, never against the planner's claim. It returns `success`, `gc`, the goal atoms and whether the order held. See [The environment and the judge](../modules/episode-env-and-judge.md).

<a id="key"></a>
**key.** The text that names a random draw. In the core `Rng` it is the parts of the call turned to text and joined with a vertical bar; in the household `Streams` it is the second constructor argument. The key text is part of the result format: renaming it changes old seeds. See [Results, time and draws](../modules/results-time-draws.md).

<a id="legacy-dict"></a>
**legacy dict.** The dictionary robot_agent skill functions return: `isdone`, `msg`, `code` when set, then the skill's data. `Result.to_legacy()` makes it and leaves `truth` out. See [Results, time and draws](../modules/results-time-draws.md).

<a id="livebackend"></a>
**`LiveBackend`.** The wrapper that holds the one running episode of a domain, logs each skill call with its truth, and lets the world be replaced without restarting the process. See [Live backend and sim commands](../modules/live-backend-and-sim-commands.md).

<a id="manifest"></a>
**manifest.** The `manifest.yaml` of a pack: the skills, capabilities, limits and planner settings of a robot, in robot_agent's format. See [Factory pack](../modules/factory-pack.md).

<a id="mcnemar-test"></a>
**McNemar test.** The paired test the household `compare` uses on (task, seed) pairs that differ between two runs: an exact binomial test when fewer than 25 pairs differ, a chi-square test with continuity correction otherwise. It is also run on per-task majorities. See [Paired tests](../learn/paired-tests.md).

<a id="messy-policy"></a>
**messy policy.** A scripted person who answers badly on purpose: `room_only`, `vague`, `mind_change`, `partial_name` or `silent`. Each task carries a short script of answers. See [Factory tasks and scripted people](../modules/factory-tasks-and-people.md).

<a id="naive"></a>
**`naive`.** The household baseline that replays the oracle's plan from the start state, open loop, with no recovery and no asking. It is privileged and exists to show what feedback is worth. See [Reference planners](../modules/reference-planners.md).

<a id="oracle"></a>
**`oracle`.** The household reference planner that reads the true world and re-solves after every call, retrying, waiting and asking for help. It is privileged: an upper reference, not a fair competitor. See [Reference planners](../modules/reference-planners.md).

<a id="pack"></a>
**pack.** The importable package of a domain that makes it usable by robot_agent: `configs/adapter`, `skills_config`, `tasks` and `manifest.yaml`. See [Packs, manifests and the hub](../learn/packs-and-manifests.md).

<a id="parameter-kind"></a>
**parameter kind.** The type of a profile number: in the core `prob`, `prob_map`, `split`, `range`, `number` or `map`; the household profiles have more (durations, speeds, rates, counts). A kind decides how `ideal` and `stress` treat the number. See [Profiles](../modules/profiles.md).

<a id="parity"></a>
**parity.** A test that replays a recorded run after a change and requires the same bytes. A difference means behaviour moved. See [Parity and frozen behaviour](../modules/parity.md).

<a id="place-id"></a>
**place id (`name@zone`).** The unique name of a place, such as `toolbox@bench_area`: the place name, an at-sign and the zone or room it is in. Skills and goals take place ids. See [Factory world](../modules/factory-world.md).

<a id="pre-registration"></a>
**pre-registration.** Writing the rule for a win down before the first episode and recording its hash with the results. A later run into that folder refuses a changed protocol file. See [The benchmark protocol](../learn/benchmark-protocol.md).

<a id="privileged-planner"></a>
**privileged planner.** A planner allowed to read the true world (`env.truth`). Only `oracle` and `naive` are; every other planner sees what a robot sees. See [Planner interface](../modules/planner-interface.md).

<a id="profile"></a>
**profile.** A named set of fault rates and durations for the simulated robot: `real` (calibrated), `ideal` (no failure) and `stress` (failure probabilities scaled up). Every number carries a source label. See [Declared outcomes and profiles](../learn/declared-outcomes.md).

<a id="protocol-sha256"></a>
**`PROTOCOL_SHA256`.** The file in a results folder that holds the SHA-256 of the suite's protocol file, written before the first episode. `python -m bench verify` compares it. See [Campaign statistics](../modules/campaign-statistics.md).

<a id="rejection-rate"></a>
**rejection rate.** Of the household episodes of kind `refuse`, the share that ended with status `refuse`. A smoke run may have only a few such episodes, so read the count too. See [Metrics, report and compare](../modules/home-metrics-and-report.md).

<a id="replay-miss"></a>
**`replay_miss`.** The status of an episode run with `--llm cache-only` when a prompt had no cached answer. The episode has no result. See [Household runner](../modules/home-runner.md).

<a id="result"></a>
<a id="skill-result"></a>
**`Result` / `SkillResult`.** What one skill call returns: `ok`, a failure code, a message, data, the time it took, and a hidden `truth`. The core `Result` and the household `SkillResult` are two classes with the same idea; the household one adds `injected`. See [Results, time and draws](../modules/results-time-draws.md).

<a id="rng"></a>
**`Rng`.** The core's seeded generator. A draw depends on the seed, a key and how often that key was asked, so unrelated calls do not shift each other's draws. It uses SHA-256, never the clock. See [Results, time and draws](../modules/results-time-draws.md).

<a id="role"></a>
**role.** The part a household profile number plays: `failure`, `recovery`, `nominal`, `user_noise` or `safety_noise`. `ideal` zeroes the noise roles; `stress` scales only `failure`. See [Household profiles](../modules/home-profiles.md).

<a id="scripted-person"></a>
**scripted person.** The simulated human who answers the robot's questions by a fixed rule or script, from outside the server (through `/agent/listen/<id>`). The factory has one; the household has a simulated user model. See [Factory tasks and scripted people](../modules/factory-tasks-and-people.md).

<a id="seed-state"></a>
**`seed_state` (arrangement).** The integer that picks how a household house's objects and people are arranged at the start. `0` is the arrangement written in the house file; other values move people and objects deterministically. See [Household world state](../modules/home-world.md).

<a id="sign-test"></a>
**sign test.** The exact two-sided binomial test on wins against losses, ties dropped. The factory statistics use it per task. See [Paired tests](../learn/paired-tests.md).

<a id="silent-failure"></a>
**silent failure.** A skill that reports `ok` while the world did not change (the truth says `effect: false`). A planner that believes it ends in a false success. See [Household failure model](../modules/home-outcomes.md).

<a id="sim-command"></a>
**`sim_command`.** The server agent that lets a script control the simulator: ops `state`, `truth`, `reset`, `load`, `move_object`, `spawn`. Every answer is a dict with `ok`, `msg` and `isdone`. See [sim_command ops](sim-command.md).

<a id="simclock"></a>
**`SimClock`.** The simulated clock. Time moves only when a skill reports a duration; nothing waits in real time. See [Results, time and draws](../modules/results-time-draws.md).

<a id="size-baseline"></a>
**size baseline.** `tests/size_baseline.json`: the list of functions and files allowed to exceed the limits (80 lines a function, 600 a file). A number in it may only go down. See [Layering and size limits](../modules/layering-tests.md).

<a id="skill"></a>
**skill.** One action the robot can be asked to do (`move`, `find`, `pick`, `ask`, ...). A skill checks its preconditions on the world, draws an outcome, applies the effect, advances the clock and returns a result. See [Symbolic worlds](../learn/symbolic-worlds.md).

<a id="slot"></a>
**slot.** One position of the fixed vector of uniform numbers a skill call draws. Each rule reads its own slot, so one rule's branch does not change another rule's number. The household vector has 14 slots; `CallDraws` has 16 by default. See [Household failure model](../modules/home-outcomes.md).

<a id="smoke-run"></a>
**smoke run.** A household run with `--limit`: a prefix of the task file, not a sample. `summary.json` marks it `smoke: true`. It checks that things work; it is not a result. See [Household runner](../modules/home-runner.md).

<a id="split"></a>
**split.** One of the household task files: `train`, `dev` or `test`. The front end refuses the test split. See [Task data](../modules/task-data.md).

<a id="status"></a>
**status.** How a household episode ended: `done`, `refuse`, `give_up`, `error` or `budget` (and `replay_miss` for a cache miss). A factory episode ends with the `done` event's status, or `none` when none arrived in time. See [The environment and the judge](../modules/episode-env-and-judge.md).

<a id="streams"></a>
**`Streams`.** The household domain's named random streams of one episode. `stream(name)` is one long-lived generator per name; `rng_for(*parts)` is a fresh one keyed by the seed, the key and the parts. See [Household failure model](../modules/home-outcomes.md).

<a id="stub-node"></a>
**stub node.** The stand-in for robot_agent's ROS node that the server installs: three read-only or command agents (`mobile_pose`, `sim_world`, `sim_command`) and do-nothing cancel and stop hooks. See [Server glue](../modules/server-and-cli.md).

<a id="suite"></a>
**suite.** A benchmark described as data plus hooks and registered under a domain: arms, tasks, answer function, distance, analysis, report and protocol file. See [The bench front end](../modules/bench-front-end.md).

<a id="task-sign-flip-test"></a>
**task sign-flip test.** The paired permutation test over tasks that the household `compare` prints when there are several seeds: per-task mean differences, signs flipped at random. It respects that seeds of one task are alike. See [Paired tests](../learn/paired-tests.md).

<a id="truth"></a>
**truth.** What really happened in the simulation: the true world and the record each call leaves. The planner never sees it; the judge and the analysis read it. See [Symbolic worlds](../learn/symbolic-worlds.md).

<a id="wilson-interval"></a>
**Wilson interval.** The score interval for a share of successes. The household headline `success_ci95` is a Wilson interval at the effective sample size (task-clustered); the plain Wilson interval of the episodes is `success_ci95_episode`. See [Metrics, report and compare](../modules/home-metrics-and-report.md).

<a id="world"></a>
**world.** The symbolic state a domain simulates: places, objects, the robot and, in the household, people. The domain's own word for it is a floor or a house. See [Symbolic worlds](../learn/symbolic-worlds.md).

<a id="wrong-done"></a>
**wrong-done.** The factory's false success: the robot said it was done and the object is not at the destination in the true world (`wrong_done` in the episode record). See [Campaign runner](../modules/campaign-runner.md).
