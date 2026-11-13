# symbolic_robot: simulated robots (domains) served as the HEADLESS BACKEND OF BENCHMARK RUNS, and the benchmark suites (bench/) that run on them.
#
#   make list                                   domains, floors / houses, profiles, suites
#   make run ROBOT=<home|factory> [PORT=8091]   start the benchmark backend in the background and wait until it answers
#   make terminate [PORT=8091]                  stop the instance `make run` started on $(PORT) (by its pid file only: never by name)
#   make status | logs | test [ROBOT=..] | help
#   make bench ROBOT=<domain> SUITE=<name> [ARGS=...]   run a benchmark suite (bench/); starts and stops its own server on a free
#                                               test port (BENCH_PORTS, default 8120-8129); results in results/<domain>_<suite>/
#   make bench ROBOT=home SUITE=<planners|run|compare|report> [ARGS=...]   the household benchmark, in process (no server): ARGS go to its CLI
#   make test [ROBOT=home]                      all tests; ROBOT=home only the household ones
#
# Variables: ROBOT=factory  PORT=8091  HOST=0.0.0.0  PROFILE=real|ideal|stress  SEED=0
#   ASK_MODE=headless  DIALOGUE=human|sim  OPTS="--floor assembly_hall"  PY=python3  RUN_ROOT=run
# This machine's values (PY, ROBOT_AGENT_DIR, ...) go in env.local.mk (not committed). A second instance: make run PORT=8121 ROBOT=home

-include env.local.mk
PY         ?= python3
ROBOT      ?= factory
PORT       ?= 8091
HOST       ?= 0.0.0.0
PROFILE    ?= real
SEED       ?= 0
ASK_MODE   ?= headless
DIALOGUE   ?= human
OPTS       ?=
RUN_ROOT   ?= run
BENCH_PORTS ?= 8120-8129
SUITE      ?=
ARGS       ?=
ROBOT_AGENT_DIR ?=
HERE       := $(CURDIR)
export PYTHONPATH := $(HERE)$(if $(ROBOT_AGENT_DIR),:$(ROBOT_AGENT_DIR))$(if $(PYTHONPATH),:$(PYTHONPATH))
export ROBOT_AGENT_ROS := off

PID_FILE   := $(RUN_ROOT)/.server-$(PORT).pid
LOG_FILE   := $(RUN_ROOT)/server-$(PORT).log
SITE_DIR   := $(RUN_ROOT)/site-$(PORT)
LAN_IP     := $(shell hostname -I 2>/dev/null | awk '{print $$1}')

.PHONY: run terminate status logs test bench list help

# one shell per recipe, so `exit` ends the whole recipe
SHELL := /bin/bash
.ONESHELL:
.SILENT:

help:
	sed -n '1,15p' Makefile | sed 's/^# \{0,1\}//'

list:
	"$(PY)" -m symbolic_robot list
	"$(PY)" -m bench list

run:
	command -v "$(PY)" >/dev/null 2>&1 || { echo "python not found: $(PY) (set PY=... or env.local.mk)"; exit 1; }
	mkdir -p "$(RUN_ROOT)"
	if [ -f "$(PID_FILE)" ] && kill -0 "$$(cat $(PID_FILE))" 2>/dev/null; then
	  echo "already running: pid $$(cat $(PID_FILE)) on port $(PORT) (make terminate PORT=$(PORT) to stop it)"; exit 0; fi
	if ss -ltn 2>/dev/null | grep -q ":$(PORT) "; then
	  echo "port $(PORT) is already in use by another process (not started by this Makefile): choose another PORT=..."; exit 1; fi
	setsid nohup "$(PY)" -m symbolic_robot run --robot $(ROBOT) --host $(HOST) --port $(PORT) --run-dir "$(SITE_DIR)" \
	    --profile $(PROFILE) --seed $(SEED) --ask-mode $(ASK_MODE) --dialogue $(DIALOGUE) $(OPTS) \
	    > "$(LOG_FILE)" 2>&1 & echo $$! > "$(PID_FILE)"
	echo "starting $(ROBOT): pid $$(cat $(PID_FILE)), port $(PORT), profile $(PROFILE), seed $(SEED) (log: $(LOG_FILE)) ..."
	for i in $$(seq 1 90); do
	  if ! kill -0 "$$(cat $(PID_FILE))" 2>/dev/null; then echo "the server exited; last log lines:"; tail -n 15 "$(LOG_FILE)"; exit 1; fi
	  if curl -s -m 2 -o /dev/null -f "http://127.0.0.1:$(PORT)/agent/mobile_pose/get"; then
	    echo "up: http://127.0.0.1:$(PORT)"
	    if [ "$(HOST)" = "0.0.0.0" ]; then echo "    from the network: http://$(LAN_IP):$(PORT)"; fi
	    echo "    benchmark backend (headless). Stop: make terminate$(if $(filter-out 8091,$(PORT)), PORT=$(PORT))"; exit 0; fi
	  sleep 1; done
	echo "no answer after 90 s: see $(LOG_FILE)"; exit 1

terminate:
	if [ ! -f "$(PID_FILE)" ]; then echo "no pid file for port $(PORT) ($(PID_FILE)): nothing started by this Makefile"
	  ss -ltnp 2>/dev/null | grep ":$(PORT) " | sed 's/^/    but something listens: /'; exit 0; fi
	pid=$$(cat "$(PID_FILE)")
	if kill -0 $$pid 2>/dev/null; then
	  kill $$pid; for i in $$(seq 1 20); do kill -0 $$pid 2>/dev/null || break; sleep 0.5; done
	  if kill -0 $$pid 2>/dev/null; then echo "still alive: sending SIGKILL"; kill -9 $$pid; fi
	  echo "stopped pid $$pid (port $(PORT))"
	else echo "pid $$pid was not running"; fi
	rm -f "$(PID_FILE)"

status:
	if [ -f "$(PID_FILE)" ] && kill -0 "$$(cat $(PID_FILE))" 2>/dev/null; then
	  echo "running: pid $$(cat $(PID_FILE)), port $(PORT), site folder $(SITE_DIR)"
	  curl -s -m 3 "http://127.0.0.1:$(PORT)/agent/mobile_pose/get" || true; echo
	else echo "not running (port $(PORT))"; ss -ltnp 2>/dev/null | grep ":$(PORT) " | sed 's/^/    but something listens: /'; fi

logs:
	tail -n 40 -f "$(LOG_FILE)"

test:
	"$(PY)" -m pytest -q -p no:warnings tests $(if $(filter-out factory,$(ROBOT)),-k $(ROBOT))

bench:
	if [ -z "$(SUITE)" ]; then echo "usage: make bench ROBOT=<domain> SUITE=<name> [ARGS=...]   (suites: make list)"; exit 1; fi
	"$(PY)" -m bench run --domain $(ROBOT) --suite $(SUITE) --python "$(PY)" --ports $(BENCH_PORTS) \
	    --out "results/$(ROBOT)_$(SUITE)" $(ARGS)
