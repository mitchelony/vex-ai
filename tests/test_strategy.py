import unittest

from vexai.strategy import Action, FieldState, MatchPhase, RobotState, TeamPlan, Zone, choose_plan


class StrategyTests(unittest.TestCase):
    def assertAssignment(self, assignment, action, zone):
        self.assertEqual(assignment.action, action)
        self.assertEqual(assignment.zone, zone)

    def test_isolation_splits_robot_zones(self):
        field = FieldState(
            phase=MatchPhase.ISOLATION,
            seconds_remaining=70,
            loose_blocks_long=6,
            loose_blocks_center=4,
            control_bonus_threatened=False,
        )
        alpha = RobotState(linked=True, carrying_blocks=False, parked=False)
        beta = RobotState(linked=True, carrying_blocks=False, parked=False)

        plan = choose_plan(field, alpha, beta)

        self.assertAssignment(plan.alpha, Action.COLLECT_BLOCKS, Zone.LONG_GOAL)
        self.assertAssignment(plan.beta, Action.COLLECT_BLOCKS, Zone.CENTER_GOAL)

    def test_scoring_beats_collecting_when_loaded(self):
        field = FieldState(
            phase=MatchPhase.ISOLATION,
            seconds_remaining=55,
            loose_blocks_long=6,
            loose_blocks_center=4,
            control_bonus_threatened=False,
        )
        alpha = RobotState(linked=True, carrying_blocks=True, parked=False)
        beta = RobotState(linked=True, carrying_blocks=False, parked=False)

        plan = choose_plan(field, alpha, beta)

        self.assertAssignment(plan.alpha, Action.SCORE_GOAL, Zone.LONG_GOAL)
        self.assertAssignment(plan.beta, Action.COLLECT_BLOCKS, Zone.CENTER_GOAL)

    def test_interaction_prioritizes_bonus_defense(self):
        field = FieldState(
            phase=MatchPhase.INTERACTION,
            seconds_remaining=40,
            loose_blocks_long=2,
            loose_blocks_center=5,
            control_bonus_threatened=True,
        )
        alpha = RobotState(linked=True, carrying_blocks=False, parked=False)
        beta = RobotState(linked=True, carrying_blocks=False, parked=False)

        plan = choose_plan(field, alpha, beta)

        self.assertAssignment(plan.alpha, Action.DEFEND_CONTROL_BONUS, Zone.LONG_GOAL)
        self.assertAssignment(plan.beta, Action.COLLECT_BLOCKS, Zone.CENTER_GOAL)

    def test_endgame_prioritizes_parking(self):
        field = FieldState(
            phase=MatchPhase.INTERACTION,
            seconds_remaining=8,
            loose_blocks_long=3,
            loose_blocks_center=3,
            control_bonus_threatened=False,
        )
        alpha = RobotState(linked=True, carrying_blocks=True, parked=False)
        beta = RobotState(linked=True, carrying_blocks=False, parked=False)

        plan = choose_plan(field, alpha, beta)

        self.assertAssignment(plan.alpha, Action.PARK, Zone.PARK_ZONE)
        self.assertAssignment(plan.beta, Action.PARK, Zone.PARK_ZONE)

    def test_link_failures_stop_aggressive_plans(self):
        field = FieldState(
            phase=MatchPhase.INTERACTION,
            seconds_remaining=50,
            loose_blocks_long=3,
            loose_blocks_center=3,
            control_bonus_threatened=True,
        )
        alpha = RobotState(linked=False, carrying_blocks=False, parked=False)
        beta = RobotState(linked=True, carrying_blocks=False, parked=False)

        plan = choose_plan(field, alpha, beta)

        self.assertAssignment(plan.alpha, Action.VERIFY_LINK, Zone.LINK_STATION)
        self.assertAssignment(plan.beta, Action.HOLD_POSITION, Zone.CENTER_GOAL)


if __name__ == "__main__":
    unittest.main()
