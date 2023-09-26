import httpx
import logging
import time

import ascifight.routers.states
import ascifight.client_lib.basic as basic
from ascifight.board.computations import Directions

logger = logging.getLogger()

SERVER = "http://127.0.0.1:8000/"
TEAM = "Team 1"
PASSWORD = "1"


def execute():
    # put your execution code here
    state = get_game_state()
    teams = state.teams.copy()
    # remove our own team from the teams to target
    teams.remove(TEAM)
    # this teams flag we want to get
    target_team = teams[0]
    # this is the base we need to go to, assuming their flag is there?
    target_base = [base for base in state.bases if base.team == target_team][0]
    # these are the bases coordinates
    target_coordinates = target_base.coordinates
    # this is our base
    home_base = [base for base in state.bases if base.team == TEAM][0]
    # we need the coordinates when we want to go home
    home_coordinates = home_base.coordinates
    # we will just use the first of our actors we have
    # assuming that it will be able to grab the flag
    actor = [actor for actor in state.actors if actor.team == TEAM][0]
    # thats where the actor currently is
    actor_coordinates = actor.coordinates
    # if it doesn't have the flag it needs to go to the enemy base
    if not actor.flag:
        # we can calculate the direction of the enemy base or get it from the server
        direction = basic.destination_direction(
            origin=actor_coordinates, destination=target_coordinates
        )[0]
        # we need to stop if we are standing right next to the base
        if (
            basic.distance(origin=actor_coordinates, destination=target_coordinates)
            == 1
        ):
            # and grab the flag, the direction is the one we would have walked to
            issue_order(order="grabput", actor_id=actor.ident, direction=direction)
        # if we are not there yet we need to go
        else:
            issue_order(order="move", actor_id=actor.ident, direction=direction)
    # if it has the flag we need to head home
    else:
        # where is home?
        direction = basic.destination_direction(
            origin=actor_coordinates, destination=home_coordinates
        )[0]

        # if we are already just 1 space apart we are there
        if basic.distance(origin=actor_coordinates, destination=home_coordinates) == 1:
            # we put the flag on our base
            issue_order(order="grabput", actor_id=actor.ident, direction=direction)
        else:
            # if we are not there we slog on home
            issue_order(order="move", actor_id=actor.ident, direction=direction)


def get_game_state() -> ascifight.routers.states.StateResponse:
    url = SERVER + "states/game_state"
    response = httpx.get(url)
    return ascifight.routers.states.StateResponse.model_validate(response.json())


def get_timing() -> ascifight.routers.states.TimingResponse:
    url = SERVER + "states/timing"
    response = httpx.get(url)
    return ascifight.routers.states.TimingResponse.model_validate(response.json())


def issue_order(order: str, actor_id: int, direction: Directions):
    httpx.post(
        url=f"{SERVER}orders/{order}/{actor_id}",
        params={"direction": direction.value},
        auth=(TEAM, PASSWORD),
    )


def game_loop():
    current_tick = -1
    while True:
        try:
            timing = get_timing()
            # if the game tarted a new tick we need to issue orders
            if timing.tick != current_tick:
                if timing.tick < current_tick:
                    # the game may have restarted, reset tick
                    current_tick = timing.tick
                execute()
                current_tick = timing.tick
                logger.info(f"Issued orders for tick {current_tick}.")
            # sleep the time the server says it will take till next tick
            sleep_duration_time = timing.time_to_next_execution
            logger.info(f"sleeping for {sleep_duration_time} seconds.")
            if sleep_duration_time >= 0:
                time.sleep(sleep_duration_time)
        except httpx.ConnectError:
            logger.info("Server not started. Sleeping 5 seconds.")
            current_tick = -1
            time.sleep(5)
            continue


if __name__ == "__main__":
    game_loop()
