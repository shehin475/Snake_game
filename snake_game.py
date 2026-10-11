"""
Nokia Snake Game Implementation
Classic snake game with a premium interface and gesture-based controls.
"""

import json
import os
import random
import sys
from enum import Enum
from typing import Optional, TypedDict

import pygame


class LeaderboardEntry(TypedDict):
    name: str
    score: int


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class SnakeGame:
    MIN_SPEED = 6
    MAX_SPEED = 20
    SPEED_INCREASE_SCORE = 50

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

        self.player_name = ""
        self.awaiting_player_name = True
        self.changing_player = False
        self.player_setup_mode = "choice"
        self.selected_player_index = 0
        self.player_search_query = ""
        self.player_entry_error = ""
        self.best_score, self.leaderboard = self.load_score_data()
        self.reset_game()
        self.particles = []

    def score_file_path(self) -> str:
        """Return the path used to persist scores and leaderboard entries."""
        if getattr(sys, "frozen", False):
            data_directory = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            return os.path.join(data_directory, "NokiaSnake", "best_score.json")
        return os.path.join(os.path.dirname(__file__), "best_score.json")

    def load_score_data(self) -> tuple[int, list[LeaderboardEntry]]:
        """Load the global best score and name-keyed leaderboard from disk."""
        score_path = self.score_file_path()
        best_score = 0
        leaderboard_by_name: dict[str, LeaderboardEntry] = {}
        try:
            if os.path.exists(score_path):
                with open(score_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if isinstance(data, dict):
                    try:
                        best_score = max(0, int(data.get("best_score", 0)))
                    except (TypeError, ValueError):
                        best_score = 0

                    entries = data.get("leaderboard", [])
                    if isinstance(entries, list):
                        for entry in entries:
                            if not isinstance(entry, dict):
                                continue
                            name = entry.get("name")
                            try:
                                score = int(entry.get("score", 0))
                            except (TypeError, ValueError):
                                continue
                            if not isinstance(name, str) or not name.strip() or score < 0:
                                continue
                            name = name.strip()[:16]
                            key = name.casefold()
                            previous = leaderboard_by_name.get(key)
                            if previous is None or score > previous["score"]:
                                leaderboard_by_name[key] = {
                                    "name": name,
                                    "score": score,
                                }
        except (OSError, json.JSONDecodeError) as error:
            print(f"Warning: Could not load saved scores: {error}")

        leaderboard = sorted(
            leaderboard_by_name.values(),
            key=lambda entry: (-entry["score"], entry["name"].casefold()),
        )
        return best_score, leaderboard

    def save_score_data(self) -> None:
        """Persist global and per-player best scores."""
        payload = {
            "best_score": max(0, self.best_score),
            "leaderboard": self.leaderboard,
        }
        score_path = self.score_file_path()
        try:
            os.makedirs(os.path.dirname(score_path), exist_ok=True)
            with open(score_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
        except OSError as error:
            print(f"Warning: Could not save scores: {error}")

    def record_score(self) -> None:
        """Update the global best and this player's name-keyed best score."""
        self.best_score = max(self.best_score, self.score)
        if self.player_name:
            key = self.player_name.casefold()
            for entry in self.leaderboard:
                if entry["name"].casefold() == key:
                    entry["name"] = self.player_name
                    entry["score"] = max(entry["score"], self.score)
                    break
            else:
                self.leaderboard.append({"name": self.player_name, "score": self.score})

            self.leaderboard.sort(
                key=lambda entry: (-entry["score"], entry["name"].casefold())
            )
        self.save_score_data()

    def matching_players(self) -> list[LeaderboardEntry]:
        """Return saved players whose IDs contain the current search text."""
        query = self.player_search_query.strip().casefold()
        if not query:
            return self.leaderboard
        return [
            entry
            for entry in self.leaderboard
            if query in entry["name"].casefold()
        ]

    def handle_name_input(self, event) -> bool:
        """Handle player choice or name entry; return True when a game starts."""
        if not self.awaiting_player_name:
            return False

        if event.type == pygame.TEXTINPUT and self.player_setup_mode == "existing":
            if len(self.player_search_query) + len(event.text) <= 16:
                self.player_search_query += event.text
                self.selected_player_index = 0
                self.player_entry_error = ""
        elif event.type == pygame.TEXTINPUT and self.player_setup_mode == "new":
            for character in event.text:
                if character.isprintable() and len(self.player_name) < 16:
                    self.player_name += character
        elif event.type == pygame.KEYDOWN:
            if self.player_setup_mode == "choice":
                if event.key == pygame.K_n:
                    self.player_setup_mode = "new"
                    self.player_name = ""
                    self.player_entry_error = ""
                    pygame.key.start_text_input()
                elif event.key == pygame.K_e:
                    if self.leaderboard:
                        self.player_setup_mode = "existing"
                        self.selected_player_index = 0
                        self.player_search_query = ""
                        self.player_entry_error = ""
                        pygame.key.start_text_input()
                    else:
                        self.player_entry_error = "No existing players yet. Choose New Player."
            elif self.player_setup_mode == "existing":
                matches = self.matching_players()
                if event.key == pygame.K_BACKSPACE:
                    self.player_search_query = self.player_search_query[:-1]
                    self.selected_player_index = 0
                    self.player_entry_error = ""
                elif event.key in (pygame.K_UP, pygame.K_w) and matches:
                    self.selected_player_index = (
                        self.selected_player_index - 1
                    ) % len(matches)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if matches:
                        self.selected_player_index = (
                            self.selected_player_index + 1
                        ) % len(matches)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if matches:
                        self.player_name = matches[self.selected_player_index]["name"]
                        self.awaiting_player_name = False
                        self.changing_player = False
                        self.player_setup_mode = "choice"
                        pygame.key.stop_text_input()
                        self.reset_game()
                        return True
                    self.player_entry_error = "No players match that search."
                elif event.key == pygame.K_ESCAPE:
                    self.player_setup_mode = "choice"
                    self.player_entry_error = ""
                    self.player_search_query = ""
                    pygame.key.stop_text_input()
            elif event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.player_name = self.player_name.strip()
                if self.player_name:
                    existing_names = {
                        entry["name"].casefold() for entry in self.leaderboard
                    }
                    if self.player_name.casefold() in existing_names:
                        self.player_entry_error = (
                            "That player ID is already used. Choose Existing Player."
                        )
                    else:
                        self.leaderboard.append(
                            {"name": self.player_name, "score": 0}
                        )
                        self.leaderboard.sort(
                            key=lambda entry: (
                                -entry["score"],
                                entry["name"].casefold(),
                            )
                        )
                        self.save_score_data()
                        self.awaiting_player_name = False
                        self.changing_player = False
                        self.player_setup_mode = "choice"
                        self.player_entry_error = ""
                        pygame.key.stop_text_input()
                        self.reset_game()
                        return True
        return False

    def start_player_change(self) -> None:
        """Open the new/existing player choice from the game-over screen."""
        if not self.game_over or self.awaiting_player_name:
            return
        self.player_name = ""
        self.awaiting_player_name = True
        self.changing_player = True
        self.player_setup_mode = "choice"
        self.player_entry_error = ""

    def reset_game(self):
        """Reset game to initial state"""
        start_x = self.grid_width // 2
        start_y = self.grid_height // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT

        self.score = 0
        self.game_over = False
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
        if self.game_over or self.awaiting_player_name:
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

            if (
                new_dir != opposite.get(self.direction)
                and new_dir != opposite.get(self.next_direction)
            ):
                self.next_direction = new_dir

    def update(self):
        """Update game state."""
        if self.game_over or self.awaiting_player_name:
            return

        self.direction = self.next_direction

        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)

        if new_head[0] < 0 or new_head[0] >= self.grid_width or new_head[1] < 0 or new_head[1] >= self.grid_height:
            self.game_over = True
            self.record_score()
            return

        if new_head in self.snake:
            self.game_over = True
            self.record_score()
            return

        self.snake.insert(0, new_head)

        if new_head == self.fruit:
            self.score += 10
            self.record_score()
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

    def draw_ui(self):
        """Draw the dashboard and overlays."""
        self.draw_stat_card("Score", self.score, 340, 28, self.GOLD)
        self.draw_stat_card("Best", self.best_score, 520, 28, self.ACCENT)
        self.draw_stat_card("Speed", self.get_current_speed(), 630, 28, self.LIGHT_GREEN)

        if self.player_name:
            player_text = self.mini_font.render(
                f"PLAYER: {self.player_name}",
                True,
                (182, 196, 193),
            )
            self.screen.blit(player_text, (42, 116))

        hint = self.small_font.render(
            "Swipe to steer • speed increases every 50 points",
            True,
            (215, 225, 220),
        )
        self.screen.blit(hint, (40, 660))

        if self.awaiting_player_name or self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (4, 10, 12, 180), overlay.get_rect(), border_radius=18)
            self.screen.blit(overlay, (0, 0))

            panel_rect = pygame.Rect(130, 145, 520, 470)
            self.draw_rounded_rect(self.screen, panel_rect, (18, 34, 35), radius=28, border_color=(112, 163, 117), border_width=2)

            if self.awaiting_player_name:
                if self.player_setup_mode == "choice":
                    title_text = "CHANGE PLAYER" if self.changing_player else "PLAYER SETUP"
                    title = self.font.render(title_text, True, self.WHITE)
                    prompt = self.small_font.render(
                        "Choose how to continue", True, self.LIGHT_GREEN
                    )
                    options = self.small_font.render(
                        "N  -  New Player", True, self.WHITE
                    )
                    existing = self.small_font.render(
                        "E  -  Existing Player", True, self.WHITE
                    )
                    self.screen.blit(title, title.get_rect(center=(self.width // 2, 205)))
                    self.screen.blit(prompt, prompt.get_rect(center=(self.width // 2, 250)))
                    self.screen.blit(options, options.get_rect(center=(self.width // 2, 295)))
                    self.screen.blit(existing, existing.get_rect(center=(self.width // 2, 330)))
                elif self.player_setup_mode == "new":
                    title = self.font.render("NEW PLAYER", True, self.WHITE)
                    prompt = self.small_font.render(
                        "Enter a unique ID (up to 16 characters), then press Enter",
                        True,
                        self.LIGHT_GREEN,
                    )
                    name_text = self.font.render(self.player_name + "|", True, self.WHITE)
                    self.screen.blit(title, title.get_rect(center=(self.width // 2, 205)))
                    self.screen.blit(prompt, prompt.get_rect(center=(self.width // 2, 255)))
                    self.screen.blit(name_text, name_text.get_rect(center=(self.width // 2, 300)))
                else:
                    title = self.font.render("EXISTING PLAYER", True, self.WHITE)
                    prompt = self.small_font.render(
                        "Type to search • Up/Down to select • Enter to continue",
                        True,
                        self.LIGHT_GREEN,
                    )
                    self.screen.blit(title, title.get_rect(center=(self.width // 2, 195)))
                    self.screen.blit(prompt, prompt.get_rect(center=(self.width // 2, 235)))
                    search_text = self.small_font.render(
                        f"Search: {self.player_search_query}|",
                        True,
                        self.WHITE,
                    )
                    self.screen.blit(
                        search_text,
                        search_text.get_rect(center=(self.width // 2, 265)),
                    )
                    matching_players = self.matching_players()
                    visible_count = 8
                    first_visible = max(
                        0, min(
                            self.selected_player_index - visible_count // 2,
                            len(matching_players) - visible_count,
                        )
                    )
                    for index in range(
                        first_visible,
                        min(first_visible + visible_count, len(matching_players)),
                    ):
                        entry = matching_players[index]
                        marker = ">" if index == self.selected_player_index else " "
                        row = self.small_font.render(
                            f"{marker} {entry['name']}  -  {entry['score']}",
                            True,
                            self.GOLD if index == self.selected_player_index else self.WHITE,
                        )
                        self.screen.blit(
                            row,
                            row.get_rect(center=(self.width // 2, 300 + (index - first_visible) * 30)),
                        )
                if self.player_entry_error:
                    error_text = self.mini_font.render(
                        self.player_entry_error, True, self.RED
                    )
                    self.screen.blit(
                        error_text,
                        error_text.get_rect(
                            center=(
                                self.width // 2,
                                555 if self.player_setup_mode == "existing" else 340,
                            )
                        ),
                    )
                if (
                    self.awaiting_player_name
                    and self.player_setup_mode == "existing"
                    and not self.matching_players()
                    and not self.player_entry_error
                ):
                    no_matches_text = self.mini_font.render(
                        "No players match that search.", True, self.RED
                    )
                    self.screen.blit(
                        no_matches_text,
                        no_matches_text.get_rect(center=(self.width // 2, 555)),
                    )
            else:
                game_over_text = self.font.render("GAME OVER", True, self.WHITE)
                final_score_text = self.font.render(f"Final Score: {self.score}", True, self.LIGHT_GREEN)
                restart_text = self.small_font.render(
                    "Swipe Up or press Enter to Restart", True, self.WHITE
                )
                self.screen.blit(game_over_text, game_over_text.get_rect(center=(self.width // 2, 185)))
                self.screen.blit(final_score_text, final_score_text.get_rect(center=(self.width // 2, 228)))
                self.screen.blit(restart_text, restart_text.get_rect(center=(self.width // 2, 575)))
                change_player_text = self.small_font.render(
                    "Press P to Change Player", True, self.LIGHT_GREEN
                )
                self.screen.blit(
                    change_player_text,
                    change_player_text.get_rect(center=(self.width // 2, 601)),
                )

            if not self.awaiting_player_name or self.player_setup_mode != "existing":
                is_name_entry = self.awaiting_player_name
                leaderboard_y = 405 if is_name_entry else 300
                first_row_y = 435 if is_name_entry else 338
                row_spacing = 26 if is_name_entry else 28
                leaderboard_title = self.font.render("LEADERBOARD", True, self.GOLD)
                self.screen.blit(
                    leaderboard_title,
                    leaderboard_title.get_rect(center=(self.width // 2, leaderboard_y)),
                )
                for rank, entry in enumerate(self.leaderboard[:5], start=1):
                    row = self.small_font.render(
                        f"{rank}.  {entry['name']}  -  {entry['score']}",
                        True,
                        self.WHITE,
                    )
                    self.screen.blit(
                        row,
                        row.get_rect(center=(self.width // 2, first_row_y + rank * row_spacing)),
                    )
                if not self.leaderboard:
                    empty = self.small_font.render(
                        "No scores yet", True, (182, 196, 193)
                    )
                    self.screen.blit(
                        empty,
                        empty.get_rect(center=(self.width // 2, first_row_y + row_spacing)),
                    )

    def handle_restart(self, gesture: Optional[str]):
        """Handle game restart."""
        if self.game_over and gesture == "UP":
            self.reset_game()

    def get_current_speed(self) -> int:
        """Increase game speed from its minimum as the score grows, up to the cap."""
        return min(
            self.MIN_SPEED + self.score // self.SPEED_INCREASE_SCORE,
            self.MAX_SPEED,
        )

    def draw(self):
        """Draw the game."""
        self.draw_background()
        self.draw_grid(self.screen)

        if not self.game_over and not self.awaiting_player_name:
            for i, segment in enumerate(self.snake):
                self.draw_snake_segment(self.screen, segment[0], segment[1], i == 0)
            self.draw_fruit(self.screen)
            self.draw_particles(self.screen)

        self.draw_ui()
        pygame.display.flip()

    def quit(self):
        """Quit the game."""
        pygame.quit()