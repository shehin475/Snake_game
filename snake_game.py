"""
Nokia Snake Game Implementation
Classic snake game with a premium interface and gesture-based controls.
"""

import json
import os
import random
from enum import Enum
from typing import Optional

import pygame


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class SnakeGame:
    def __init__(self, width: int = 780, height: int = 760):
        """Initialize the Nokia Snake game"""
        self.width = width
        self.height = height
        self.board_size = 560
        self.board_x = (self.width - self.board_size) // 2
        self.board_y = 120
        self.grid_size = self.board_size // 24
        self.grid_width = self.board_size // self.grid_size
        self.grid_height = self.board_size // self.grid_size

        self.BLACK = (4, 10, 12)
        self.WHITE = (246, 248, 240)
        self.NOKIA_GREEN = (155, 188, 15)
        self.DARK_GREEN = (109, 132, 18)
        self.LIGHT_GREEN = (205, 255, 78)
        self.RED = (255, 72, 72)
        self.ORANGE = (255, 181, 71)
        self.PANEL = (13, 27, 29)
        self.PANEL_EDGE = (32, 52, 56)
        self.ACCENT = (112, 255, 166)
        self.GOLD = (255, 208, 102)

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Nokia Snake - Gesture Control")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 68)
        self.font = pygame.font.Font(None, 38)
        self.small_font = pygame.font.Font(None, 22)
        self.mini_font = pygame.font.Font(None, 18)

        self.best_score = self.load_best_score()
        self.reset_game()
        self.particles = []

    def load_best_score(self) -> int:
        """Load the highest score from disk."""
        score_path = os.path.join(os.path.dirname(__file__), "best_score.json")
        try:
            if os.path.exists(score_path):
                with open(score_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    if isinstance(data, dict) and "best_score" in data:
                        return int(data["best_score"])
        except (OSError, ValueError, json.JSONDecodeError):
            return 0
        return 0

    def save_best_score(self) -> None:
        """Persist the best score to disk."""
        score_path = os.path.join(os.path.dirname(__file__), "best_score.json")
        payload = {"best_score": max(0, self.best_score)}
        try:
            with open(score_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
        except OSError:
            pass

    def reset_game(self):
        """Reset game to initial state"""
        start_x = self.grid_width // 2
        start_y = self.grid_height // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT

        self.score = 0
        self.game_over = False
        self.speed_boost = False
        self.base_speed = 8
        self.boost_speed = 15
        self.particles = []
        self.spawn_fruit()

    def spawn_fruit(self):
        """Spawn a new fruit at random location"""
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if (x, y) not in self.snake:
                self.fruit = (x, y)
                break

    def add_particle_effect(self, x: int, y: int):
        """Add particle effect when eating fruit"""
        for _ in range(10):
            particle = {
                "x": x * self.grid_size + self.grid_size // 2,
                "y": y * self.grid_size + self.grid_size // 2,
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(-3, 3),
                "life": 34,
                "max_life": 34,
            }
            self.particles.append(particle)

    def update_particles(self):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1

            if particle["life"] <= 0:
                self.particles.remove(particle)

    def change_direction(self, new_direction: str):
        """Change snake direction based on gesture input"""
        if self.game_over:
            return

        direction_map = {
            "UP": Direction.UP,
            "DOWN": Direction.DOWN,
            "LEFT": Direction.LEFT,
            "RIGHT": Direction.RIGHT,
        }

        if new_direction in direction_map:
            new_dir = direction_map[new_direction]
            opposite = {
                Direction.UP: Direction.DOWN,
                Direction.DOWN: Direction.UP,
                Direction.LEFT: Direction.RIGHT,
                Direction.RIGHT: Direction.LEFT,
            }

            if new_dir != opposite.get(self.direction):
                self.next_direction = new_dir

    def set_speed_boost(self, boost: bool):
        """Set speed boost state."""
        self.speed_boost = boost

    def update(self):
        """Update game state."""
        if self.game_over:
            return

        self.direction = self.next_direction

        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)

        if new_head[0] < 0 or new_head[0] >= self.grid_width or new_head[1] < 0 or new_head[1] >= self.grid_height:
            self.game_over = True
            self.best_score = max(self.best_score, self.score)
            self.save_best_score()
            return

        if new_head in self.snake:
            self.game_over = True
            self.best_score = max(self.best_score, self.score)
            self.save_best_score()
            return

        self.snake.insert(0, new_head)

        if new_head == self.fruit:
            self.score += 10
            self.best_score = max(self.best_score, self.score)
            self.save_best_score()
            self.add_particle_effect(new_head[0], new_head[1])
            self.spawn_fruit()
        else:
            self.snake.pop()

        self.update_particles()

    def draw_rounded_rect(self, surface, rect, color, radius=16, border_color=None, border_width=1):
        """Draw a rounded rectangle with optional border."""
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, color, panel.get_rect(), border_radius=radius)
        if border_color is not None:
            pygame.draw.rect(panel, border_color, panel.get_rect(), border_width, border_radius=radius)
        surface.blit(panel, rect)

    def draw_background(self):
        """Draw the premium game background."""
        self.screen.fill(self.BLACK)
        glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(glow, (16, 38, 42, 180), glow.get_rect(), border_radius=24)
        self.screen.blit(glow, (0, 0))

        title_text = self.title_font.render("NOKIA", True, self.LIGHT_GREEN)
        subtitle_text = self.small_font.render("SNAKE // GESTURE EDITION", True, self.WHITE)
        self.screen.blit(title_text, (36, 28))
        self.screen.blit(subtitle_text, (42, 90))

        self.draw_rounded_rect(self.screen, pygame.Rect(28, 24, 280, 86), (16, 30, 32), radius=18, border_color=(78, 104, 76), border_width=2)
        self.draw_rounded_rect(self.screen, pygame.Rect(30, 130, self.board_size + 24, self.board_size + 24), self.PANEL, radius=26, border_color=self.PANEL_EDGE, border_width=3)

    def draw_grid(self, surface):
        """Draw a polished grid background."""
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        self.draw_rounded_rect(surface, board_rect, (11, 18, 20), radius=18, border_color=(68, 94, 66), border_width=2)

        for x in range(0, self.grid_width):
            px = self.board_x + x * self.grid_size
            pygame.draw.line(surface, (32, 41, 44), (px, self.board_y), (px, self.board_y + self.board_size))
        for y in range(0, self.grid_height):
            py = self.board_y + y * self.grid_size
            pygame.draw.line(surface, (32, 41, 44), (self.board_x, py), (self.board_x + self.board_size, py))

    def draw_snake_segment(self, surface, x: int, y: int, is_head: bool = False):
        """Draw a single snake segment with a premium arcade look."""
        pixel_x = self.board_x + x * self.grid_size
        pixel_y = self.board_y + y * self.grid_size
        inner = pygame.Rect(pixel_x + 2, pixel_y + 2, self.grid_size - 4, self.grid_size - 4)

        if is_head:
            pygame.draw.rect(surface, self.LIGHT_GREEN, inner, border_radius=8)
            eye_size = 3
            left_eye = pygame.Rect(pixel_x + 7, pixel_y + 8, eye_size, eye_size)
            right_eye = pygame.Rect(pixel_x + self.grid_size - 10, pixel_y + 8, eye_size, eye_size)
            pygame.draw.rect(surface, self.BLACK, left_eye)
            pygame.draw.rect(surface, self.BLACK, right_eye)
            glow = pygame.Rect(pixel_x + 3, pixel_y + 3, self.grid_size - 6, self.grid_size - 6)
            pygame.draw.rect(surface, (175, 255, 111, 80), glow, border_radius=10)
        else:
            pygame.draw.rect(surface, self.NOKIA_GREEN, inner, border_radius=8)

        pygame.draw.rect(surface, self.DARK_GREEN, inner, 1, border_radius=8)

    def draw_fruit(self, surface):
        """Draw fruit with a glowing effect."""
        x, y = self.fruit
        pixel_x = self.board_x + x * self.grid_size
        pixel_y = self.board_y + y * self.grid_size

        glow = pygame.Rect(pixel_x - 3, pixel_y - 3, self.grid_size + 6, self.grid_size + 6)
        pygame.draw.ellipse(surface, (255, 151, 64, 100), glow)
        pygame.draw.ellipse(surface, self.RED, pygame.Rect(pixel_x + 3, pixel_y + 3, self.grid_size - 6, self.grid_size - 6))
        pygame.draw.rect(surface, self.WHITE, pygame.Rect(pixel_x + 8, pixel_y + 7, 4, 4))

    def draw_particles(self, surface):
        """Draw particle effects."""
        for particle in self.particles:
            alpha = int(255 * (particle["life"] / particle["max_life"]))
            size = max(1, int(3 * (particle["life"] / particle["max_life"])))
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*self.ORANGE, alpha), (size, size), size)
            surface.blit(particle_surface, (int(particle["x"] - size), int(particle["y"] - size)))

    def draw_stat_card(self, title, value, x, y, accent_color):
        """Draw a compact stat panel."""
        rect = pygame.Rect(x, y, 160, 78)
        self.draw_rounded_rect(self.screen, rect, (20, 35, 39), radius=16, border_color=accent_color, border_width=2)
        label = self.mini_font.render(title.upper(), True, (182, 196, 193))
        value_text = self.font.render(str(value), True, self.WHITE)
        self.screen.blit(label, (x + 14, y + 14))
        self.screen.blit(value_text, (x + 14, y + 34))

    def draw_speed_meter(self):
        """Draw a boost meter for the speed state."""
        meter_rect = pygame.Rect(40, 680, 240, 24)
        self.draw_rounded_rect(self.screen, meter_rect, (7, 18, 22), radius=12, border_color=(86, 110, 74), border_width=2)

        fill_width = 240 if self.speed_boost else 120
        target = self.boost_speed if self.speed_boost else self.base_speed
        current = min(1.0, target / self.boost_speed)
        fill_width = int(220 * current)
        fill_rect = pygame.Rect(52, 688, fill_width, 8)
        fill_color = self.LIGHT_GREEN if self.speed_boost else self.ACCENT
        pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=6)

        status_text = self.small_font.render("BOOST" if self.speed_boost else "READY", True, self.WHITE)
        self.screen.blit(status_text, (300, 684))

    def draw_ui(self):
        """Draw the dashboard and overlays."""
        self.draw_stat_card("Score", self.score, 340, 28, self.GOLD)
        self.draw_stat_card("Best", self.best_score, 520, 28, self.ACCENT)
        self.draw_stat_card("Speed", self.get_current_speed(), 630, 28, self.LIGHT_GREEN)

        hint = self.small_font.render("Gesture: swipe to steer • pinch for boost", True, (215, 225, 220))
        self.screen.blit(hint, (40, 660))
        self.draw_speed_meter()

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (4, 10, 12, 180), overlay.get_rect(), border_radius=18)
            self.screen.blit(overlay, (0, 0))

            panel_rect = pygame.Rect(170, 220, 440, 260)
            self.draw_rounded_rect(self.screen, panel_rect, (18, 34, 35), radius=28, border_color=(112, 163, 117), border_width=2)

            game_over_text = self.font.render("GAME OVER", True, self.WHITE)
            final_score_text = self.font.render(f"Final Score: {self.score}", True, self.LIGHT_GREEN)
            restart_text = self.small_font.render("Swipe Up to Restart", True, self.WHITE)

            self.screen.blit(game_over_text, game_over_text.get_rect(center=(self.width // 2, 290)))
            self.screen.blit(final_score_text, final_score_text.get_rect(center=(self.width // 2, 340)))
            self.screen.blit(restart_text, restart_text.get_rect(center=(self.width // 2, 392)))

    def handle_restart(self, gesture: Optional[str]):
        """Handle game restart."""
        if self.game_over and gesture == "UP":
            self.reset_game()

    def get_current_speed(self) -> int:
        """Get current game speed."""
        return self.boost_speed if self.speed_boost else self.base_speed

    def draw(self):
        """Draw the game."""
        self.draw_background()
        self.draw_grid(self.screen)

        if not self.game_over:
            for i, segment in enumerate(self.snake):
                self.draw_snake_segment(self.screen, segment[0], segment[1], i == 0)
            self.draw_fruit(self.screen)
            self.draw_particles(self.screen)

        self.draw_ui()
        pygame.display.flip()

    def quit(self):
        """Quit the game."""
        pygame.quit()