import os
import sys
from time import sleep
import pygame
from settings import Settings
from game_stats import GameStats
from ship import Ship
from bullet import Bullet
from alien import Alien
from button import Button
from scoreboard import Scoreboard
from bonus import Bonus

import pickle


import pickle
import pygame
import os
import sys
from time import sleep

def save_game(data, filename="savefile.pkl"):
    """
    Сохраняет данные игры в файл.

    Args:
        data (dict): Данные игры, которые нужно сохранить.
        filename (str, optional): Имя файла для сохранения. По умолчанию "savefile.pkl".
    """
    with open(filename, "wb") as f:
        pickle.dump(data, f)

def load_game(filename="savefile.pkl"):
    """
    Загружает данные игры из файла.

    Args:
        filename (str, optional): Имя файла для загрузки. По умолчанию "savefile.pkl".

    Returns:
        dict: Загруженные данные игры.
    """
    with open(filename, "rb") as f:
        return pickle.load(f)

class AlienInvasion:
    """Класс для управления игрой Alien Invasion."""

    def __init__(self):
        """
        Инициализирует игру и создает игровые ресурсы.
        """
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.width, self.settings.height))
        pygame.display.set_caption("Alien Invasion")

        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        # Определение пути к ресурсам звуков
        resource_path = os.path.join('resources', 'scream.mp3')
        self.alien_hit = pygame.mixer.Sound(resource_path)

        resource_path_2 = os.path.join('resources', 'ship_hit.mp3')
        self.ship_hit = pygame.mixer.Sound(resource_path_2)

        resource_path_3 = os.path.join('resources', 'shoot.mp3')
        self.shoot = pygame.mixer.Sound(resource_path_3)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self.bonus = None

        self._create_fleet()
        self.play_button = Button(self, "Play")

    def run_game(self):
        """
        Запускает основной цикл игры.
        """
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
                if self.bonus:
                    self._update_bonus()

            self._update_screen()

    def _check_events(self):
        """
        Обрабатывает нажатия и события мыши.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_keydown_events(self, event):
        """
        Обрабатывает события нажатия клавиш.

        Args:
            event (pygame.event.Event): Событие нажатия клавиши.
        """
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self.shoot.play()
            self._fire_bullet()
        elif event.key == pygame.K_s:
            game_data = {"level": self.stats.level, "score": self.stats.score, "lives": self.stats.ships_left}
            save_game(game_data)
        elif event.key == pygame.K_l:
            data = load_game()
            self.stats.level = data['level']
            self.sb.prep_level()
            self.stats.score = data['score']
            self.sb.prep_score()
            self.stats.ships_left = data['lives']
            self.sb.prep_ships()
            self._update_screen()

    def _check_keyup_events(self, event):
        """
        Обрабатывает события отпускания клавиш.

        Args:
            event (pygame.event.Event): Событие отпускания клавиши.
        """
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """
        Создает новый снаряд и добавляет его в группу снарядов.
        """
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bonus(self):
        """
        Обновляет бонус и проверяет его коллизию с кораблем.
        """
        self.bonus.update()

        if pygame.Rect.colliderect(self.ship.rect, self.bonus.rect):
            self.stats.ships_left += 1
            self.sb.prep_ships()
            self.bonus = None
        elif self.bonus.rect.top <= 0:
            self.bonus = None

    def _update_bullets(self):
        """
        Обновляет состояние снарядов и проверяет их коллизию с пришельцами.
        """
        self.bullets.update()

        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """
        Проверяет коллизии между снарядами и пришельцами.
        """
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.alien_hit.play()
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()

        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            self.stats.level += 1
            self.sb.prep_level()

            self.bonus = Bonus(self)

    def _create_fleet(self):
        """
        Создает флот пришельцев.
        """
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        ship_height = self.ship.rect.height
        available_space_y = (self.settings.height - (alien_height * 3) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """
        Создает пришельца и добавляет его в группу пришельцев.

        Args:
            alien_number (int): Номер пришельца в ряду.
            row_number (int): Номер ряда.
        """
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _update_aliens(self):
        """
        Обновляет состояние пришельцев и проверяет коллизии с кораблем.
        """
        self._check_fleet_edges()
        self.aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """
        Проверяет, достигли ли пришельцы края экрана.
        """
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """
        Меняет направление флота пришельцев.
        """
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _ship_hit(self):
        """
        Обрабатывает событие, когда пришелец сталкивается с кораблем.
        """
        if self.stats.ships_left > 0:
            self.ship_hit.play()
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            self.aliens.empty()
            self.bullets.empty()

            self._create_fleet()
            self.ship.center_ship()

            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """
        Проверяет, достигли ли пришельцы нижней границы экрана.
        """
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _check_play_button(self, mouse_pos):
        """
        Проверяет, нажата ли кнопка "Играть".

        Args:
            mouse_pos (tuple): Позиция мыши в момент нажатия.
        """
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self.settings.initialize_dynamic_settings()

            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            self.aliens.empty()
            self.bullets.empty()

            self._create_fleet()
            self.ship.center_ship()

            pygame.mouse.set_visible(False)

    def _update_screen(self):
        """
        Обновляет изображение на экране.
        """
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        if self.bonus:
            self.bonus.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        self.sb.show_score()

        if not self.stats.game_active:
            self.play_button.draw_button()

        # Отображение последнего прорисованного экрана
        pygame.display.flip()


if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()
