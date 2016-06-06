import socket
from threading import Thread
import json
import random
from log import log as log
from raycaster_fast import Raycaster
import math
import time
from player import Player


class AI(object):
    def __init__(self, name, id, renderer, host="localhost", port=2016):
        # Attributes
        self.active = True
        self.enemies = {}
        self.id = id
        self.renderer = renderer
        self.raycaster = None
        self.last_time = time.time()
        self.lines = []

        # Connect to server and send handshake with name
        self.socket = socket.socket()
        self.socket.connect((host, port))
        self.socket_file = self.socket.makefile()
        self.socket.send(json.dumps({"name": name + "_" + str(id)}) + "\n")

        # Run thread for network retrieving
        self.thread = Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()

        # Run thread for ai calculations
        self.thread = Thread(target=self.run_ai)
        self.thread.setDaemon(True)
        self.thread.start()

    def run(self):
        while self.active:
            # Read line by line and append it to buffer.
            line = self.socket_file.readline().rstrip('\n')
            self.lines.append(line)

            # Track performance
            tps = int(10.0/(time.time() - self.last_time))/10.0
            if (self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1)) and (tps < 10 or tps > 20):
                log("Unstable TPS: " + str(tps))
            self.last_time = time.time()

            # Server is shutting down
            if not line or line == "":
                self.active = False

    def run_ai(self):
        while self.active:
            # Wait for new stuff.
            if len(self.lines) < 1:
                time.sleep(0.01)
                continue
            # read most recent line from network
            line = self.lines[-1]
            self.lines = []
            packet = json.loads(line)

            if "gamestate" in packet:
                # extract info from packet
                player = packet["gamestate"]["player"]
                enemies = packet["gamestate"]["players"]
                projectiles = packet["gamestate"]["projectiles"]
                walls = packet["gamestate"]["walls"]
                ranking = packet["gamestate"]["ranking"]
                remaining_ticks = packet["gamestate"]["remaining_ticks"]

                # handle the packet
                self.handle(player, enemies, projectiles, walls, ranking, remaining_ticks)
            else:
                # If in charge with rendering, update renderer
                if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
                    if "lobby" in packet:
                        self.renderer.set_lobby(packet["lobby"]["timeout"])

        # If in charge with rendering, update renderer
        if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
            self.renderer.set_lobby(0)

    def handle(self, player, enemies, projectiles, walls, ranking, remaining_ticks):
        # Create raycaster if not exists.
        if self.raycaster is None:
            self.raycaster = Raycaster(walls)
        self.raycaster.update(enemies)

        # Defaults
        speed = 1
        turn = 0
        aim = 0
        shot = 2
        enemy = None

        # Processing pipeline.   
        self.track_enemies(enemies)
        speed, turn, aim, shot, enemy = self.obstacle_avoidance(player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)
        speed, turn, aim, shot, enemy = self.find_target(player, self.enemies.values(), projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)
        speed, turn, aim, shot, enemy = self.short_distance_safety(player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)
        speed, turn, aim, shot, enemy = self.target_verification(player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)


        # If in charge with rendering, update renderer
        if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
            players = list(self.enemies.values())
            players.append(player)
            self.renderer.set_game(player, players, projectiles, walls, ranking, remaining_ticks)

        # Send over network
        self.socket.send(json.dumps({"speed": speed, "turn": turn, "shoot": shot, "aim": aim}) + "\n")

    def track_enemies(self, enemies):
        toremove = []
        for enemy in self.enemies:
            e = self.enemies[enemy]
            e["forget_me"] = e["forget_me"] - 1
            if e["forget_me"] <= 0:
                toremove.append(enemy)
            if e["respawn"] == 0:
                Player.move(self.raycaster, e)
            else:
                e["respawn"] = e["respawn"] - 1
                if e["respawn"] == 0:
                    toremove.append(enemy)
            e["aimspeed"] = e["aimspeed"] * 0.8
            e["turnspeed"] = e["turnspeed"] * 0.8
            e["movespeed"] = e["movespeed"] * 0.99
        for x in toremove:
            del self.enemies[x]

        for enemy in enemies:
            self.enemies[enemy["name"]] = enemy
            enemy["forget_me"] = 30 * 5
                
    def obstacle_avoidance(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
        # Check whats left
        ray = {"x": player["x"], "y": player["y"], "theta": player["theta"] + math.radians(20)}
        tx, ty, obj = self.raycaster.cast(ray, collision_mode=True)
        dx = tx - player["x"]
        dy = ty - player["y"]
        dleft = dx * dx + dy * dy
        
        # Check whats right 
        ray = {"x": player["x"], "y": player["y"], "theta": player["theta"] - math.radians(20)}
        tx, ty, obj = self.raycaster.cast(ray, collision_mode=True)
        dx = tx - player["x"]
        dy = ty - player["y"]
        dright = dx * dx + dy * dy
        
        # Calculate how to evade if nescessary.
        if dleft < 100 or dright < 100:
            delta = (dleft - dright) / 30
            turn = delta
            
        return speed, turn, aim, shot, enemy
        
    def short_distance_safety(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
        # Calculate how far it can drive straight
        ray = {"x": player["x"], "y": player["y"], "theta": player["theta"]}
        tx, ty, obj = self.raycaster.cast(ray, collision_mode=True)
        dx = tx - player["x"]
        dy = ty - player["y"]
        
        # If to short turn
        if dx * dx + dy * dy < 10:
            turn = 1
            
        # If too short do not shoot splash!
        if dx * dx + dy * dy < 10 * 10 and shot == 2:
            shot = 1
            
        # If too long use faster primarry weapon
        if dx * dx + dy * dy > 20 * 20 and shot == 2:
            shot = 1
            
        return speed, turn, aim, shot, enemy
    
    def find_target(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
        # Find enemy
        enemy = None
        edist2 = 0
        for e in enemies:
            if e["respawn"] > 0:
                continue
            dx = e["x"] - player["x"]
            dy = e["x"] - player["x"]
            d = dx * dx + dy * dy
            if enemy is None or edist2 > d:
                enemy = e
                edist2 = d
                
        # Calculate turn and aim towards target
        if enemy is not None:
            dx = enemy["x"] - player["x"]
            dy = enemy["y"] - player["y"]
            
            # Calculate and normalize theta angle
            dtheta = math.atan2(dy, dx) - player["theta"]
            while dtheta <= -math.pi:
                dtheta += math.pi * 2
            while dtheta > math.pi:
                dtheta -= math.pi * 2
                
            # Calculate turn. Set to 0 if too small.
            turn = dtheta / (math.radians(90/30) * 2)
            if abs(turn) < 1.5:
                turn = 0
            turn = max(-0.75, min(0.75, turn))
            
            # Calculate and normalize aim angle
            dtheta = math.atan2(dy, dx) - player["aim"]
            while dtheta <= -math.pi:
                dtheta += math.pi * 2
            while dtheta > math.pi:
                dtheta -= math.pi * 2
                
            # Calculate aim.
            aim = dtheta / (1.5 * math.radians(90/30))
            aim = max(-1, min(1, aim))
        
        # Roam if no enemy    
        if enemy is None:
            aim = 1
            
        return speed, turn, aim, shot, enemy
        
    def target_verification(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
        # Calculate the shooting direction
        ray = {"x": player["x"], "y": player["y"], "theta": player["aim"]}
        tx, ty, obj = self.raycaster.cast(ray)
        dx = tx - player["x"]
        dy = ty - player["y"]

        l = max(5.0, math.sqrt(dx * dx + dy * dy))

        # Check if we hit and have an enemy
        if enemy is None or len(obj) < 3 or l > 40:
            shot = 0
        else:
            speed = 0
            turn = 0
            aim = 0

        # Calculate if bloom is too bad
        l = max(5.0, math.sqrt(dx * dx + dy * dy))
        if player["bloom"] > math.asin(0.5/l):
            if enemy is None:
                speed = 0
            else:
                speed = 0.3
            shot = 0
            
        return speed, turn, aim, shot, enemy

    def stop(self):
        self.active = False

    def join(self):
        self.thread.join()