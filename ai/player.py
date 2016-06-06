import math

AIMSPEED_PER_TICK = 1.5 * math.radians(90/30)
TURNSPEED_PER_TICK = math.radians(90/30)
MOVESPEED_PER_TICK = 0.2


class Player(object):
    def __init__(self, raycaster):
        pass

    @staticmethod
    def move(raycaster, pose):
        #print(pose)
        movespeed = pose["movespeed"]
        turnspeed = pose["turnspeed"]
        aimspeed = pose["aimspeed"]

        # Move robot
        dx = math.cos(pose["theta"]) * movespeed * MOVESPEED_PER_TICK
        dy = math.sin(pose["theta"]) * movespeed * MOVESPEED_PER_TICK

        # Check how far the robot can move.
        if movespeed >= 0:
            tx, ty, obj = raycaster.cast({"x": pose["x"], "y": pose["y"], "theta": pose["theta"]}, pose["name"], collision_mode=True)
        else:
            tx, ty, obj = raycaster.cast({"x": pose["x"], "y": pose["y"], "theta": pose["theta"] - math.pi}, pose["name"], collision_mode=True)

        # Only if there is an obstacle do something about it...
        if tx is not None and ty is not None and obj is not None:
            dtx = tx - pose["x"]
            dty = ty - pose["y"]
            dlen = dtx * dtx + dty * dty

            # Crop movement if nescesarry
            if dlen <= dx * dx + dy * dy * 1.01:
                dx = 0
                dy = 0

        # Apply motion
        pose["x"] += dx
        pose["y"] += dy
        pose["theta"] += turnspeed * TURNSPEED_PER_TICK
        pose["aim"] += aimspeed * AIMSPEED_PER_TICK + turnspeed * TURNSPEED_PER_TICK

        while pose["theta"] <= -math.pi:
            pose["theta"] += 2 * math.pi
        while pose["theta"] > math.pi:
            pose["theta"] -= 2 * math.pi

        while pose["aim"] <= -math.pi:
            pose["aim"] += 2 * math.pi
        while pose["aim"] > math.pi:
            pose["aim"] -= 2 * math.pi