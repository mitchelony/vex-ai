# vex-ai

Starter research-and-development workspace for an AAMU VEX AI programming team.

## What is here
- `research_vex_ai/`: current-season notes and the initial research plan
- `vexai/devices.py`: Thor device names and port map
- `vexai/robots.py`: Thor and Loki hardware-role definitions
- `vexai/state.py`: world-state builder from sensors, mechanism memory, and partner telemetry
- `vexai/planner.py`: two-robot intent planner with task locking and opening-book support
- `vexai/tasks.py`: persistent task state machines and simple approach waypoints
- `vexai/link.py`: compact partner telemetry packet codec
- `vexai/runtime.py`: one-cycle autonomy orchestrator for VEXcode-facing integration
- `vexai/telemetry.py`: in-memory and JSONL replay logging helpers
- `vexai/strategy.py`: legacy compatibility wrapper over the new planner
- `vexai/simulation.py`: stepped match simulation engine and built-in scenarios
- `vexai/sim.py`: laptop-friendly simulator entrypoint
- `tests/test_devices.py`: tests for the Thor device map
- `tests/test_robots.py`: tests for the robot definitions
- `tests/test_simulation.py`: tests for stepped match simulation
- `tests/test_strategy.py`: behavior tests for the planner
- `tests/test_state.py`: world-state build coverage
- `tests/test_planner_v2.py`: new planner behavior coverage
- `tests/test_tasks_v2.py`: task persistence and waypoint coverage
- `tests/test_link_v2.py`: partner packet codec coverage
- `tests/test_telemetry_v2.py`: replay log coverage

## Current bot structure
- `Thor`: large vertical-intake bot with two modes
  storage mode sorts alliance balls into storage and opponent balls into a denial hold
  scoring mode sends alliance balls to either the low goal or high goal
- `Loki`: smaller incline-intake bot with no storage
  picks up, holds, and scores directly into the low goal or high goal

## Sensor layout
- `Thor`: AI sensor front, GPS rear, optical sensor in intake
- `Loki`: AI sensor front, GPS on body, optical sensor in intake
- bench-test optical detection now uses hue ranges plus object/brightness gating instead of relying only on the Optical sensor's named color

## Current Thor port map
- Drive motors
  `left_motor_a` port 1
  `left_motor_b` port 2
  `right_motor_a` port 3
  `right_motor_b` port 4
  VEX `SmartDrive` is configured with drivetrain GPS on port 19
- Intake motors
  `f_1_2` port 5
  `f_3` port 6
  `b_1` port 7
  `b_2_3` port 8
  `b_4` port 9
  `f_4` port 20
- Sensors
  `ai_vision_11` port 11
  `optical_12` port 12
  `gps_13` port 13

## Current Thor storage-mode routing
- optical sensor sits between the front intake group and `b_2_3`
- `f_1_2` and `f_3` spin right
- `b_1` spins left
- `b_2_3` spins right
- `b_4` routes by detected color
  alliance ball: spin left into alliance storage
  opponent ball: spin right faster into the overhead opponent hold
- `f_4` is now wired in bench-test code
  alliance ball path: spin left
  opponent ball path: spin right faster
- alliance color should be switchable in code; current starter examples default to blue

## Current Thor scoring-mode starter
- scoring mode runs while `R2` is held
- `b_1`, `b_2_3`, and `b_4` spin right constantly during scoring
- current starter uses three score targets:
  low: `f_1_2` spins left and `f_3`/`f_4` stay off
  middle: `f_1_2` spins right and `f_3` spins left while `f_4` stays off
  high: `f_1_2` spins right, `f_3` spins right, and `f_4` spins left
- this is a first bench-test assumption until the exact scoring path is tuned on the real robot

## Current bench-test controls
- left joystick
  `Axis3`: forward and backward drive
  `Axis4`: turning
- drive control uses the generated left/right drivetrain motor groups from the VEX 4-motor `SmartDrive` configuration
- `R1`: storage mode while held
- `R2`: scoring mode while held
- `Up`: select high-goal scoring path
- `Left`: select middle-goal scoring path
- `Down`: select low-goal scoring path
- `A`: set alliance color to blue
- `B`: set alliance color to red

## Why start this way
The workspace is intentionally **portable first**. That gives the team a place to design match logic, role assignment, and robot-to-robot coordination before wiring everything into a full VEXcode project on the brain.

This prototype is based on current official VAIRC facts checked on **2026-03-30**:
- 2025-2026 VAIRC game: **Push Back**
- Match structure: **15 second Isolation** plus **1:45 Interaction**
- Two-robot autonomous coordination is core to the event

Official links are recorded in [research_vex_ai/official_notes.md](/Users/MAC/Projects/vex-ai/research_vex_ai/official_notes.md).

## Current planner behaviors
- Split the team into long-goal and center-goal jobs in Isolation
- Score immediately if a robot is already loaded
- Defend control bonus pressure during Interaction
- Force both robots to park in the last 10 seconds
- Recover the disconnected robot while allowing the still-linked partner to continue low-risk local play
- Keep active tasks locked long enough to avoid thrashing between assignments
- Run a small scripted opening during early Isolation before handing off to reactive planning

## New autonomy stack
- `state.py`
  builds `WorldState` from local sensor frames, mechanism memory, and partner telemetry
- `planner.py`
  converts `WorldState` into `RobotIntent` values with explicit reason codes
- `tasks.py`
  persists collect/score/recovery tasks and provides fixed safe-approach waypoints
- `runtime.py`
  runs one full autonomy cycle:
  state build, planning, task selection, partner packet generation, and replay logging
- `telemetry.py`
  writes newline-delimited JSON suitable for SD-card replay and the laptop viewer

## Replay workflow
1. Run autonomy on the Brain and write JSONL snapshots to the SD card.
2. Move the SD card log file onto the laptop.
3. Launch the replay viewer:

```bash
python3 tools/replay_viewer.py /path/to/run.jsonl
```

The viewer renders Thor and Loki poses, field estimates, planner intent, and confidence flags over time.

Set up the local replay-viewer environment:

```bash
python3 -m venv .venv
./.venv/bin/pip install matplotlib
```

Launch the viewer from the virtualenv:

```bash
./.venv/bin/python tools/replay_viewer.py /path/to/run.jsonl
```

## VEXcode logging stub
- `VexAI_test/src/main.py` now supports a minimal competition-mode autonomous logger.
- Bench mode is still the default.
- To run the logging stub on the Brain, set `USE_COMPETITION_TEMPLATE = True`.
- The autonomous callback writes newline-delimited JSON snapshots to `thor_replay.jsonl` on the SD card when one is inserted.

## Local usage
Run tests:

```bash
make test
```

Run the simple simulator:

```bash
make sim
```

Run a different built-in simulation scenario:

```bash
python3 -m vexai.sim --scenario link-loss
```

## Current simulator behavior
- simulates a full 120-second VAIRC-style match in 5-second steps by default
- switches from Isolation to Interaction automatically
- injects configurable control-bonus threat events
- can inject link failures for Thor or Loki
- updates loose blocks, carried blocks, score, parking, and opponent pressure over time
- records a full decision timeline so you can see what Thor and Loki chose at each step

The scoring inside the simulator is intentionally heuristic. It is not an official Push Back scoring calculator. It is there to help compare strategy behavior, not to replace the game manual.

## Recommended next steps
1. Replace the simple `FieldState` with real sensor-fed state:
   GPS pose, heading, block sightings, goal occupancy, partner telemetry.
2. Add a communication packet definition for `message_link`.
3. Build a task layer under the planner:
   intake, path-follow, score, clear, defend, park.
4. Port the planner into a real VEXcode Python project once the hardware ports and devices are finalized.

## Suggested VEXcode Python structure
- `main.py`: match loop, competition callbacks, and top-level mode switching
- `devices.py`: brain, drivetrain, GPS, AI Vision, intake, scoring mechanism, and radio config
- `state.py`: field state and robot state builders from live sensors
- `planner.py`: strategy decisions like the prototype in `vexai/strategy.py`
- `tasks.py`: concrete robot actions such as intake, score, defend, and park
- `link.py`: packet definitions and partner-brain messaging
- `thor.py`: Thor-only storage, sorting, and scoring-mode logic
- `loki.py`: Loki-only direct-intake and scoring logic
