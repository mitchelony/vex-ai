import json
import tempfile
import unittest
from pathlib import Path

from vexai.telemetry import JsonlReplayLogger, load_replay_records


class TelemetryTests(unittest.TestCase):
    def test_jsonl_logger_writes_valid_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "run.jsonl"
            logger = JsonlReplayLogger(path)
            logger.write({"t_ms": 100, "robot_local": "thor", "field": {"phase": "INTERACTION", "seconds_remaining": 60}})
            logger.close()

            lines = path.read_text().strip().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0])["t_ms"], 100)

    def test_loader_tolerates_missing_optional_fields_and_rejects_bad_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "run.jsonl"
            path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "t_ms": 100,
                                "robot_local": "thor",
                                "field": {"phase": "INTERACTION", "seconds_remaining": 60},
                            }
                        ),
                        json.dumps({"robot_local": "thor"}),
                    ]
                )
            )

            records = load_replay_records(path)

            self.assertEqual(len(records.valid), 1)
            self.assertEqual(len(records.invalid), 1)


if __name__ == "__main__":
    unittest.main()
