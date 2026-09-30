import random
import time
import pygame
from game.text_box import TextBox

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.words = ["PYTHON", "PYGAME", "PLANET", "ROCKET", "GALAXY", "STREAM", "PUZZLE", "ALGORITHM"]
        self.secret_word = ""
        self.scrambled_word = ""

        self.revealed_letters = []

        self.tile_letters = []
        self.selected_tile = None
        self.tile_rects = []

        self.score = 0
        self.hint_points = 4

        self.time_limit = 20
        self.start_time = time.time()
        self.time_up = False
        self.time_up_time = 0

        self.feedback_msg = "Unscramble the letters above!"
        self.feedback_color = (210, 215, 225)

        self.input_box = TextBox(width // 2 - 130, 250, 160, 46)
        self.submit_btn = pygame.Rect(width // 2 + 45, 250, 95, 46)
        self.hint_btn = pygame.Rect(width // 2 + 150, 250, 95, 46)

        self.font_title = pygame.font.SysFont(None, 40)
        self.font_word = pygame.font.SysFont(None, 52)
        self.font_msg = pygame.font.SysFont(None, 26)
        self.font_btn = pygame.font.SysFont(None, 24)

        self.next_round()

    def scramble_string(self, word):
        letters = list(word)

        while True:
            random.shuffle(letters)
            shuffled = "".join(letters)

            if shuffled != word or len(word) <= 1:
                return shuffled

    def next_round(self):
        self.secret_word = random.choice(self.words)
        self.scrambled_word = self.scramble_string(self.secret_word)
        self.revealed_letters = []

        self.tile_letters = list(self.scrambled_word)
        self.selected_tile = None
        self.tile_rects = []

        self.input_box.clear()
        self.start_time = time.time()
        self.time_up = False

    def use_hint(self):
        if self.hint_points <= 0:
            self.feedback_msg = "No hints available!"
            self.feedback_color = (240, 80, 80)
            return

        for i in range(len(self.secret_word)):
            if i not in self.revealed_letters:
                self.revealed_letters.append(i)
                self.hint_points -= 1
                self.score = max(0, self.score - 1)
                self.feedback_msg = f"Hint revealed letter {i + 1}!"
                self.feedback_color = (255, 220, 80)
                return

        self.feedback_msg = "All letters are already revealed!"
        self.feedback_color = (240, 170, 50)

    def submit_guess(self):
        guess = self.input_box.text.strip().upper()

        if not guess:
            guess = "".join(self.tile_letters)

        if not guess:
            self.feedback_msg = "Arrange the letters before submitting!"
            self.feedback_color = (240, 170, 50)
            return

        is_correct = (guess == self.secret_word)

        if is_correct:
            self.score += 1
            self.hint_points += 1
            self.feedback_msg = f"CORRECT! '{self.secret_word}' is right."
            self.feedback_color = (80, 230, 110)
            self.next_round()
        else:
            self.feedback_msg = "WRONG GUESS! Try again."
            self.feedback_color = (240, 80, 80)
            self.input_box.clear()

    def handle_event(self, event):
        self.input_box.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.submit_guess()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.submit_btn.collidepoint(event.pos):
                self.submit_guess()
                return

            if self.hint_btn.collidepoint(event.pos):
                self.use_hint()
                return

            for i, rect in enumerate(self.tile_rects):
                if rect.collidepoint(event.pos):
                    if self.selected_tile is None:
                        self.selected_tile = i
                    else:
                        self.tile_letters[self.selected_tile], self.tile_letters[i] = (
                            self.tile_letters[i],
                            self.tile_letters[self.selected_tile]
                        )
                        self.selected_tile = None
                    return

    def update(self):
        if self.time_up:
            if time.time() - self.time_up_time >= 1:
                self.next_round()
            return

        elapsed_time = time.time() - self.start_time
        remaining_time = self.time_limit - elapsed_time

        if remaining_time <= 0:
            self.time_up = True
            self.time_up_time = time.time()
            self.feedback_msg = f"TIME'S UP! The word was {self.secret_word}."
            self.feedback_color = (240, 80, 80)

    def render(self, screen):
        screen.fill((26, 30, 38))

        title_surf = self.font_title.render("Word Scramble Arena", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 25))

        score_surf = self.font_msg.render(f"Score: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 70))

        hint_surf = self.font_msg.render(f"Hints: {self.hint_points}", True, (255, 220, 80))
        screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, 100))

        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, self.time_limit - elapsed_time)

        timer_surf = self.font_msg.render(f"Time: {int(remaining_time)}", True, (255, 255, 255))
        screen.blit(timer_surf, (self.width // 2 - timer_surf.get_width() // 2, 125))

        tile_width = 50
        tile_height = 50
        tile_gap = 8

        total_width = (
            len(self.tile_letters) * tile_width
            + (len(self.tile_letters) - 1) * tile_gap
        )

        start_x = self.width // 2 - total_width // 2
        tile_y = 165

        self.tile_rects = []

        for i, letter in enumerate(self.tile_letters):
            tile_x = start_x + i * (tile_width + tile_gap)

            tile_rect = pygame.Rect(
                tile_x,
                tile_y,
                tile_width,
                tile_height
            )

            self.tile_rects.append(tile_rect)

            if self.selected_tile == i:
                tile_color = (255, 180, 70)
            else:
                tile_color = (50, 120, 180)

            pygame.draw.rect(
                screen,
                tile_color,
                tile_rect,
                border_radius=6
            )

            pygame.draw.rect(
                screen,
                (220, 220, 220),
                tile_rect,
                width=2,
                border_radius=6
            )

            letter_surf = self.font_msg.render(letter, True, (255, 255, 255))

            screen.blit(
                letter_surf,
                (
                    tile_rect.centerx - letter_surf.get_width() // 2,
                    tile_rect.centery - letter_surf.get_height() // 2
                )
            )

        hint_display = "  ".join(
            self.secret_word[i] if i in self.revealed_letters else "_"
            for i in range(len(self.secret_word))
        )

        hint_display_surf = self.font_msg.render(
            hint_display,
            True,
            (255, 220, 80)
        )

        screen.blit(
            hint_display_surf,
            (
                self.width // 2 - hint_display_surf.get_width() // 2,
                225
            )
        )

        self.input_box.render(screen)

        pygame.draw.rect(
            screen,
            (50, 150, 85),
            self.submit_btn,
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            (220, 220, 220),
            self.submit_btn,
            width=2,
            border_radius=6
        )

        btn_text = self.font_btn.render("SUBMIT", True, (255, 255, 255))

        screen.blit(
            btn_text,
            (
                self.submit_btn.centerx - btn_text.get_width() // 2,
                self.submit_btn.centery - btn_text.get_height() // 2
            )
        )

        pygame.draw.rect(
            screen,
            (70, 100, 180),
            self.hint_btn,
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            (220, 220, 220),
            self.hint_btn,
            width=2,
            border_radius=6
        )

        hint_text = self.font_btn.render("HINT", True, (255, 255, 255))

        screen.blit(
            hint_text,
            (
                self.hint_btn.centerx - hint_text.get_width() // 2,
                self.hint_btn.centery - hint_text.get_height() // 2
            )
        )

        feedback_surf = self.font_msg.render(
            self.feedback_msg,
            True,
            self.feedback_color
        )

        screen.blit(
            feedback_surf,
            (
                self.width // 2 - feedback_surf.get_width() // 2,
                325
            )
        )