from vexai.strategy import FieldState, MatchPhase, RobotState, choose_plan


def main() -> None:
    opening = FieldState(
        phase=MatchPhase.ISOLATION,
        seconds_remaining=70,
        loose_blocks_long=6,
        loose_blocks_center=4,
        control_bonus_threatened=False,
    )
    alpha = RobotState(linked=True, carrying_blocks=False, parked=False)
    beta = RobotState(linked=True, carrying_blocks=False, parked=False)
    plan = choose_plan(opening, alpha, beta)

    print(f"Phase: {opening.phase.name}")
    print(f"Alpha -> {plan.alpha.action.name} @ {plan.alpha.zone.name}")
    print(f"Beta  -> {plan.beta.action.name} @ {plan.beta.zone.name}")


if __name__ == "__main__":
    main()
