#!/usr/bin/env python3
import argparse
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vexai.telemetry import load_replay_records


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button, Slider
    except ImportError as exc:
        raise SystemExit("matplotlib is required for the replay viewer") from exc
    return plt, Slider, Button


def _pose(record, robot_name):
    pose = record.get(robot_name, {}).get("pose", {})
    return pose.get("x_mm", 0.0), pose.get("y_mm", 0.0), pose.get("heading_deg", 0.0)


def _side_panel_text(record):
    planner = record.get("planner", {})
    confidence = record.get("confidence", {})
    field = record.get("field", {})
    thor = record.get("thor", {})
    loki = record.get("loki", {})
    return "\n".join(
        [
            "t = %sms" % record.get("t_ms", "?"),
            "phase = %s" % field.get("phase", "?"),
            "remaining = %s" % field.get("seconds_remaining", "?"),
            "intent = %s" % planner.get("intent_local", "?"),
            "reason = %s" % planner.get("reason_local", "?"),
            "gps conf = %.2f" % confidence.get("gps", 0.0),
            "vision conf = %.2f" % confidence.get("vision", 0.0),
            "thor load = %s" % thor.get("load_state", "?"),
            "thor denial = %s" % thor.get("denial_estimate", "?"),
            "loki load = %s" % loki.get("load_state", "?"),
        ]
    )


def main():
    parser = argparse.ArgumentParser(description="Replay a VEX AI JSONL telemetry log.")
    parser.add_argument("log_path", type=Path, help="Path to a JSONL replay log")
    args = parser.parse_args()

    result = load_replay_records(args.log_path)
    if not result.valid:
        raise SystemExit("No valid records found in %s" % args.log_path)

    plt, Slider, Button = _require_matplotlib()
    records = result.valid
    fig = plt.figure(figsize=(11, 7))
    field_ax = fig.add_axes([0.07, 0.18, 0.62, 0.72])
    info_ax = fig.add_axes([0.73, 0.18, 0.23, 0.72])
    slider_ax = fig.add_axes([0.07, 0.08, 0.62, 0.04])
    play_ax = fig.add_axes([0.73, 0.08, 0.1, 0.05])
    pause_ax = fig.add_axes([0.86, 0.08, 0.1, 0.05])

    field_ax.set_title("VEX AI Replay")
    field_ax.set_xlim(-200, 1600)
    field_ax.set_ylim(-600, 900)
    field_ax.set_xlabel("x (mm)")
    field_ax.set_ylabel("y (mm)")
    field_ax.grid(True, alpha=0.3)
    info_ax.axis("off")

    thor_scatter = field_ax.scatter([], [], c="tab:blue", s=80, label="Thor")
    loki_scatter = field_ax.scatter([], [], c="tab:orange", s=80, label="Loki")
    thor_heading = field_ax.quiver([], [], [], [], color="tab:blue", scale=20)
    loki_heading = field_ax.quiver([], [], [], [], color="tab:orange", scale=20)
    info_text = info_ax.text(0.0, 1.0, "", va="top", family="monospace")
    field_ax.legend(loc="upper right")

    slider = Slider(slider_ax, "Frame", 0, len(records) - 1, valinit=0, valstep=1)
    play_button = Button(play_ax, "Play")
    pause_button = Button(pause_ax, "Pause")

    state = {"playing": False}

    def render(index):
        record = records[int(index)]
        thor_x, thor_y, thor_h = _pose(record, "thor")
        loki_x, loki_y, loki_h = _pose(record, "loki")
        thor_dx = math.cos(math.radians(thor_h))
        thor_dy = math.sin(math.radians(thor_h))
        loki_dx = math.cos(math.radians(loki_h))
        loki_dy = math.sin(math.radians(loki_h))
        thor_scatter.set_offsets([[thor_x, thor_y]])
        loki_scatter.set_offsets([[loki_x, loki_y]])
        thor_heading.set_offsets([[thor_x, thor_y]])
        thor_heading.set_UVC([thor_dx], [thor_dy])
        loki_heading.set_offsets([[loki_x, loki_y]])
        loki_heading.set_UVC([loki_dx], [loki_dy])
        info_text.set_text(_side_panel_text(record))
        fig.canvas.draw_idle()

    def on_slider_change(value):
        render(int(value))

    def on_play(_event):
        state["playing"] = True

    def on_pause(_event):
        state["playing"] = False

    def on_timer():
        if not state["playing"]:
            return
        next_index = int(slider.val) + 1
        if next_index >= len(records):
            state["playing"] = False
            return
        slider.set_val(next_index)

    slider.on_changed(on_slider_change)
    play_button.on_clicked(on_play)
    pause_button.on_clicked(on_pause)

    timer = fig.canvas.new_timer(interval=200)
    timer.add_callback(on_timer)
    timer.start()

    render(0)
    plt.show()


if __name__ == "__main__":
    main()
