import socket
from threading import Thread
import json
import random
from log import log as log
from raycaster_fast import Raycaster
import math
import time


class AI(object):
    def __init__(self, name, id, renderer, host="localhost", port=2016):
        self.socket = socket.socket()
        self.socket.connect((host, port))
        self.socket_file = self.socket.makefile()
        self.socket.send(json.dumps({"name": name + "_" + str(id)}) + "\n")
        self.active = True
        self.id = id
        self.renderer = renderer
        self.raycaster = None
        self.last_time = time.time()
        self.lines = []

        self.thread = Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()
        
        self.thread = Thread(target=self.run_ai)
        self.thread.setDaemon(True)
        self.thread.start()
        self.last_state = None

    def run(self):
        while self.active:
            line = self.socket_file.readline().rstrip('\n')
            self.lines.append(line)
            tps = int(10.0/(time.time() - self.last_time))/10.0
            if (self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1)) and (tps < 10 or tps > 20):
                log("Unstable TPS: " + str(tps))
            self.last_time = time.time()   
            if line and not line == "":
                pass
            else:
                self.active = False
                
        if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
            self.renderer.set_lobby(0)
            
    def run_ai(self):
        while self.active:
            if len(self.lines) < 1:
                time.sleep(0.01)
                continue
            line = self.lines[-1]
            self.lines = []
            packet = json.loads(line)
            if "gamestate" in packet:
                player = packet["gamestate"]["player"]
                enemies = packet["gamestate"]["players"]
                projectiles = packet["gamestate"]["projectiles"]
                walls = packet["gamestate"]["walls"]
                ranking = packet["gamestate"]["ranking"]
                remaining_ticks = packet["gamestate"]["remaining_ticks"]
                self.handle(player, enemies, projectiles, walls, ranking, remaining_ticks)
                if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
                    players = list(enemies)
                    players.append(player)
                    self.renderer.set_game(player, players, projectiles, walls, ranking, remaining_ticks)
            else:
                if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
                    if "lobby" in packet:
                        self.renderer.set_lobby(packet["lobby"]["timeout"])
                
        if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
            self.renderer.set_lobby(0)

    def handle(self, player, enemies, projectiles, walls, ranking, remaining_ticks):
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
        speed, turn, aim, shot, enemy = self.obstacle_avoidance(player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)
        speed, turn, aim, shot, enemy = self.find_target(player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)
        speed, turn, aim, shot, enemy = self.short_distance_safety(player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)
        speed, turn, aim, shot, enemy = self.target_verification(player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy)
                  
        #if self.renderer.get_selected_player() == self.id or (self.renderer.get_selected_player() == 0 and self.id == 1):
            #print(json.dumps({"speed": speed, "turn": turn, "shoot": shot, "aim": aim}))
        self.socket.send(json.dumps({"speed": speed, "turn": turn, "shoot": shot, "aim": aim}) + "\n")
        self.last_state = player
        
    def obstacle_avoidance(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
        ray = {"x": player["x"], "y": player["y"], "theta": player["theta"] + math.radians(20),}
        tx, ty, obj = self.raycaster.cast(ray, collision_mode=True)
        dx = tx - player["x"]
        dy = ty - player["y"]
        dpos = dx * dx + dy * dy
            
        ray = {"x": player["x"], "y": player["y"], "theta": player["theta"] - math.radians(20)}
        tx, ty, obj = self.raycaster.cast(ray, collision_mode=True)
        dx = tx - player["x"]
        dy = ty - player["y"]
        dneg = dx * dx + dy * dy
        
        if dneg < 100 or dpos < 100:
            delta = (dpos - dneg)/30
            turn = delta
        return speed, turn, aim, shot, enemy
        
    def short_distance_safety(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
        ray = {"x": player["x"], "y": player["y"], "theta": player["theta"]}
        tx, ty, obj = self.raycaster.cast(ray, collision_mode=True)
        dx = tx - player["x"]
        dy = ty - player["y"]
        
        if dx * dx + dy * dy < 10:
            turn = 1
        if dx * dx + dy * dy < 10 * 10 and shot == 2:
            shot = 1
        if dx * dx + dy * dy > 20 * 20 and shot == 2:
            shot = 1
        return speed, turn, aim, shot, enemy
    
    def find_target(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
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
                
        if enemy is not None:
            dx = enemy["x"] - player["x"]
            dy = enemy["y"] - player["y"]
            dtheta = math.atan2(dy, dx) - player["theta"]
            while dtheta <= -math.pi:
                dtheta += math.pi * 2
            while dtheta > math.pi:
                dtheta -= math.pi * 2
            turn = dtheta / (math.radians(90/30) * 2)
            if abs(turn) < 1.5:
                turn = 0
            turn = max(-0.75, min(0.75, turn))
            
            dtheta = math.atan2(dy, dx) - player["aim"]
            while dtheta <= -math.pi:
                dtheta += math.pi * 2
            while dtheta > math.pi:
                dtheta -= math.pi * 2
            aim = dtheta / (1.5 * math.radians(90/30))
            speed = 0.4
        if enemy is None:
            aim = 1
            
        return speed, turn, aim, shot, enemy
        
    def target_verification(self, player, enemies, projectiles, walls, ranking, remaining_ticks, speed, turn, aim, shot, enemy):
        ray = {"x": player["x"], "y": player["y"], "theta": player["aim"]}
        tx, ty, obj = self.raycaster.cast(ray)
        dx = tx - player["x"]
        dy = ty - player["y"]
        
        if enemy is None or len(obj) < 3:
            shot = 0
        else:
            speed = 0
            turn = 0
            aim = 0
            
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