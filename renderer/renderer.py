import pygame
import math
from player import Player
from raycaster import Raycaster
from projectile import Projectile
from map import Map
import operator

FOV_IN_DEGREE = 120
FOV = math.radians(FOV_IN_DEGREE)
EPSILON = math.radians(0.001)
INIT_TIMEOUT = 30 * 30


class Renderer(object):
    def __init__(self):
        self.player = None
        self.players = None
        self.projectiles = None
        self.walls = None
        self.ranking = None
        self.selected_player = 0
        self.lobby = True
        self.remaining_ticks = 0
        self.timeout = INIT_TIMEOUT
        
    def set_lobby(self, timeout):
        self.lobby = True
        self.timeout = timeout
        
    def set_game(self, player, players, projectiles, walls, ranking, remaining_ticks):
        self.lobby = False
        self.player = player
        self.players = players
        self.projectiles = projectiles
        self.walls = walls
        self.ranking = ranking
        self.remaining_ticks = remaining_ticks

    def select_player(self, number):
        self.selected_player = number
        
    def get_selected_player(self):
        return self.selected_player
     
    def render(self, screen, width, height):
        if not self.lobby:
            self.render_game(screen, width, height)
        else:
            self.render_lobby(screen, width, height)
    
    def quit(self):
        pass
        
    def render_lobby(self, screen, width, height, game_over=True):
        centerX = width // 2
        centerY = height// 2
        ranking = self.ranking

        if ranking is not None:
            myfont = pygame.font.SysFont("Arial", 44)
            label = myfont.render("Into Darkness", 1, (255, 255, 255))
            screen.blit(label, (centerX - label.get_width() // 2, 10))

            panelHeight = 42 + 22 * 1.1 * len(ranking.items())
            if game_over:
                myfont = pygame.font.SysFont("Arial", 32)
                label = myfont.render("Game Over", 1, (255, 255, 255))
                screen.blit(label, (centerX - label.get_width() // 2, centerY - panelHeight))
            else:
                myfont = pygame.font.SysFont("Arial", 32)
                label = myfont.render("Ranking", 1, (255, 255, 255))
                screen.blit(label, (centerX - label.get_width() // 2, centerY - panelHeight))
                
            myfont = pygame.font.SysFont("Arial", 22)
            sorted_x = sorted(ranking.items(), key=operator.itemgetter(1), reverse=True)

            label = myfont.render(sorted_x[0][0], 1, (255, 255, 255))
            label2 = myfont.render(str(sorted_x[0][1]), 1, (255, 255, 255))
            panelWidth = label.get_width() + 40 + label2.get_width()

            i = 0
            label = myfont.render("Player", 1, (255, 255, 255))
            label2 = myfont.render("Points", 1, (255, 255, 255))
            screen.blit(label,
                        (centerX - 20 - panelWidth / 2, centerY - panelHeight + 56 + label.get_height() * 1.1 * i))
            screen.blit(label2, (centerX + 20 + panelWidth / 2 - label2.get_width(),
                                 centerY - panelHeight + 56 + label.get_height() * 1.1 * i))
            i += 1
            for key, value in sorted_x:
                label = myfont.render(key, 1, (255, 255, 255))
                label2 = myfont.render(str(value), 1, (255, 255, 255))
                screen.blit(label, (centerX - 20 - panelWidth / 2, centerY - panelHeight + 64 + label.get_height() * 1.1 * i))
                screen.blit(label2, (centerX + 20 + panelWidth / 2 - label2.get_width(), centerY - panelHeight + 64 + label.get_height() * 1.1 * i))
                i += 1
        else:
            myfont = pygame.font.SysFont("Arial", 76)
            label = myfont.render("Into Darkness", 1, (255, 255, 255))
            screen.blit(label, (centerX - label.get_width() // 2, height // 4 - label.get_height() // 2))

            myfont = pygame.font.SysFont("Arial", 56)
            label = myfont.render("Penguinmenac3 AI View", 1, (255, 255, 0))
            screen.blit(label, (centerX - label.get_width() // 2, 3 * height // 4 - label.get_height() // 2))
          
        if not self.lobby:  
            myfont = pygame.font.SysFont("Arial", 22)
            label = myfont.render("Ticks remaining: " + str(self.remaining_ticks) + " ticks", 1, (0, 255, 0))
            screen.blit(label, (centerX - label.get_width() // 2, height - 5 - label.get_height()))
        else:
            myfont = pygame.font.SysFont("Arial", 22)
            if self.timeout < INIT_TIMEOUT:
                label = myfont.render("Start in: " + str(self.timeout) + " ticks", 1, (0, 255, 0))
                screen.blit(label, (centerX - label.get_width() // 2, height - 5 - label.get_height()))
            else:
                label = myfont.render("Waiting for more players...", 1, (255, 0, 0))
                screen.blit(label, (centerX - label.get_width() // 2, height - 5 - label.get_height()))
        
    def render_game(self, screen, width, height):
        if self.selected_player == 0:
            self.render_lobby(screen, width, height, False)
            return
        raycaster = Raycaster(self.players, self.walls)
        raycaster.update()
        map_size = raycaster.get_map_size() + 1.0

        #self.render_vision(raycaster, self.player, screen, width, height, map_size)
            

        Map.render(self.walls, screen, width, height, map_size)
        #Map.render(raycaster.get_lines(), screen, width, height, map_size)
        for p in self.players:
            Player.render(p, raycaster, screen, width, height, map_size)
        for projectile in self.projectiles:
            Projectile.render(projectile, screen, width, height, map_size)
        for p in self.players:
            Player.render_font(p, screen, width, height, map_size)


        myfont = pygame.font.SysFont("Arial", 22)
        label = myfont.render("Ticks remaining: " + str(self.remaining_ticks), 1, (255, 255, 255))
        s = pygame.Surface((label.get_width() + 20, label.get_height() + 20), pygame.SRCALPHA)  # per-pixel alpha
        s.fill((45, 45, 45, 200))
        screen.blit(s, (width // 2 - label.get_width() // 2 - 10, 0))
        screen.blit(label, (width // 2 - label.get_width() // 2, 10))

        myfont = pygame.font.SysFont("Arial", 16)
        label = myfont.render("test", 1, (255, 255, 255))
        line_height = label.get_height()
        myfont = pygame.font.SysFont("Arial", 32)
        label = myfont.render("Ranking-----", 1, (255, 255, 255))
        line_width = label.get_width()
        s = pygame.Surface((line_width + 20, line_height * (len(self.ranking) + 2) + 40), pygame.SRCALPHA)  # per-pixel alpha
        s.fill((45, 45, 45, 200))
        screen.blit(s, (0, 0))

        myfont = pygame.font.SysFont("Arial", 32)
        label = myfont.render("Ranking", 1, (255, 255, 255))
        screen.blit(label, (10, 10))
        myfont = pygame.font.SysFont("Arial", 16)
        i = 2
        sorted_x = sorted(self.ranking.items(), key=operator.itemgetter(1), reverse=True)
        for key, value in sorted_x:
            label = myfont.render(key + ": " + str(value), 1, (255, 255, 255))
            screen.blit(label, (10, 10 + label.get_height() * 1.1 * i))
            i += 1

        #myfont = pygame.font.SysFont("Arial", 32)
        #label = myfont.render(host + ":" + str(port), 1, (255, 255, 0))
        #s = pygame.Surface((label.get_width() + 20, label.get_height() + 20), pygame.SRCALPHA)  # per-pixel alpha
        #s.fill((45, 45, 45, 200))
        #screen.blit(s, (width // 2 - label.get_width() // 2 - 10, height - label.get_height() - 20))
        #screen.blit(label, (width // 2 - label.get_width() // 2, height - label.get_height() - 10))

    def render_vision(self, raycaster, player, screen, width, height, map_size):
        if player["respawn"] > 0:
            return

        scale = height / map_size

        x = int(player["x"] * scale)
        y = int(player["y"] * scale)
        offset_x = width // 2
        offset_y = height // 2

        points = [(x + offset_x, -y + offset_y)]
        helper_points = []

        lines = raycaster.get_lines()

        tx, ty, _ = raycaster.cast(
            {"x": player["x"], "y": player["y"], "theta": player["aim"] - FOV / 2}, player["name"])
        if tx is not None:
            points.append((int(tx * scale) + offset_x, - int(ty * scale) + offset_y))
        for line in lines:
            for i in range(2):
                p = line[i]
                dx = p["x"] - player["x"]
                dy = p["y"] - player["y"]
                d = math.atan2(dy, dx)
                dth = d - player["aim"]
                while dth > math.pi:
                    dth -= 2 * math.pi
                while dth < -math.pi:
                    dth += 2 * math.pi

                if abs(dth) > FOV / 2.0:
                    continue

                for j in range(3):
                    tx, ty, _ = raycaster.cast(
                        {"x": player["x"], "y": player["y"], "theta": d + (j-1) * EPSILON}, player["name"])
                    if tx is not None and ty is not None:
                        helper_points.append((int(tx * scale) + offset_x, - int(ty * scale) + offset_y,
                                              dth + (j-1) * EPSILON))

        helper_points = sorted(helper_points, key=lambda tup: tup[2])
        for i in range(len(helper_points)):
            points.append((helper_points[i][0], helper_points[i][1]))

        tx, ty, _ = raycaster.cast(
            {"x": player["x"], "y": player["y"], "theta": player["aim"] + FOV / 2}, player["name"])
        if tx is not None:
            points.append((int(tx * scale) + offset_x, - int(ty * scale) + offset_y))

        if len(points) > 2:
            s = pygame.Surface((width, height), pygame.SRCALPHA)  # per-pixel alpha
            pygame.draw.polygon(s, (250, 250, 200, 128), points, 0)
            screen.blit(s, (0, 0))