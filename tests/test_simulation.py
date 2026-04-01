import unittest

from vexai.strategy import Action, MatchPhase

from vexai.simulation import SimulationConfig, simulate_match


class SimulationTests(unittest.TestCase):
    def test_simulator_runs_full_match_and_reaches_endgame(self):
        report = simulate_match(
            SimulationConfig(
                step_seconds=5,
                initial_long_blocks=4,
                initial_center_blocks=4,
                control_bonus_threat_times=(95, 60),
            )
        )

        self.assertGreater(len(report.timeline), 5)
        self.assertEqual(report.timeline[0].field.phase, MatchPhase.ISOLATION)
        self.assertEqual(report.timeline[-1].field.seconds_remaining, 0)
        self.assertEqual(report.timeline[-1].alpha_plan.action, Action.PARK)
        self.assertEqual(report.timeline[-1].beta_plan.action, Action.PARK)
        self.assertGreater(report.final_score, 0)

    def test_link_failure_forces_recovery_then_restores_link(self):
        report = simulate_match(
            SimulationConfig(
                step_seconds=5,
                initial_long_blocks=3,
                initial_center_blocks=3,
                alpha_link_fail_times=(50,),
            )
        )

        recovery_steps = [step for step in report.timeline if step.alpha_plan.action == Action.VERIFY_LINK]
        self.assertTrue(recovery_steps)

        recovered_after = False
        for step in report.timeline:
            if step.field.seconds_remaining < 50 and step.alpha.linked:
                recovered_after = True
                break
        self.assertTrue(recovered_after)

    def test_collect_then_score_changes_robot_inventory_and_score(self):
        report = simulate_match(
            SimulationConfig(
                step_seconds=5,
                initial_long_blocks=2,
                initial_center_blocks=2,
            )
        )

        collected = any(step.alpha.carried_blocks > 0 or step.beta.carried_blocks > 0 for step in report.timeline)
        scored = any(step.alliance_score > 0 for step in report.timeline)

        self.assertTrue(collected)
        self.assertTrue(scored)


if __name__ == "__main__":
    unittest.main()
