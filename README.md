# vex-ai

Starter research-and-development workspace for an AAMU VEX AI programming team.

## What is here
- `research_vex_ai/`: current-season notes and the initial research plan
- `vexai/robots.py`: Thor and Loki hardware-role definitions
- `vexai/strategy.py`: first-pass two-robot autonomy planner
- `vexai/sim.py`: laptop-friendly simulator entrypoint
- `tests/test_robots.py`: tests for the robot definitions
- `tests/test_strategy.py`: behavior tests for the planner

## Current bot structure
- `Thor`: large vertical-intake bot with two modes
  storage mode sorts alliance balls into storage and opponent balls into a denial hold
  scoring mode sends alliance balls to either the low goal or high goal
- `Loki`: smaller incline-intake bot with no storage
  picks up, holds, and scores directly into the low goal or high goal

## Sensor layout
- `Thor`: AI sensor front, GPS rear, optical sensor in intake
- `Loki`: AI sensor front, GPS on body, optical sensor in intake

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
- Stop aggressive play and recover the link if one robot loses communication

## Local usage
Run tests:

```bash
make test
```

Run the simple simulator:

```bash
make sim
```

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
