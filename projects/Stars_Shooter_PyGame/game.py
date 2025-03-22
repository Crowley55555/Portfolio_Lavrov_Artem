import pygame
import random
from settings import *
from player import Player
from enemy import Enemy, Asteroid
from powerup import Powerup
from boss import Boss
from utils import load_image, load_sound, load_explosion_frames


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        """
        Инициализирует анимацию взрыва.

        :param center: Центральная точка взрыва.
        :param size: Размер взрыва ('lg' или 'sm').
        """
        super().__init__()
        self.size = size
        self.explosion_anim = {
            'lg': load_explosion_frames('explosion_lg', 9),
            'sm': load_explosion_frames('explosion_sm', 9)
        }
        self.image = self.explosion_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        """
        Обновляет кадр анимации взрыва.
        """
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(self.explosion_anim[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = self.explosion_anim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


class Game:
    def __init__(self):
        """
        Инициализирует основные параметры игры.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Shooter")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)

        self.background = load_image('background.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.player = Player(512, 900)
        self.all_sprites = pygame.sprite.Group(self.player)
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.boss = None

        self.score = 0
        self.level = 1
        self.next_powerup_time = pygame.time.get_ticks() + POWERUP_INTERVAL * 1000

        self.player_bullet_damage = 5
        self.player_bullet_damage_timer = 0
        self.player_speed_boost = 1
        self.player_speed_boost_timer = 0

        # Звуки
        self.shoot_sound1 = load_sound('shoot1.wav')
        self.explosion_sound = load_sound('explosion.wav')
        self.game_over_sound = load_sound('game_over.wav')

        # Музыка
        pygame.mixer.music.load(os.path.join(SOUNDS_DIR, 'background_music.mp3'))
        pygame.mixer.music.play(-1)  # Повторять музыку

        # Флаг для включения/выключения звука
        self.sound_enabled = True

        # Флаги для паузы после взрыва игрока
        self.player_exploded = False
        self.player_respawn_time = None

    def run(self):
        """
        Основной цикл игры.
        """
        self.show_start_screen()
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0
            self.events()
            self.update()
            self.draw()
        pygame.quit()

    def events(self):
        """
        Обрабатывает события игры.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.player.shoot(self.bullets, 1)
                    if self.sound_enabled:
                        self.shoot_sound1.play()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.show_pause_screen()
                elif event.key == pygame.K_m:  # Клавиша M для включения/выключения звука
                    self.toggle_sound()

    def update(self):
        """
        Обновляет состояние всех спрайтов и проверяет столкновения.
        """
        if not self.player_exploded:
            self.all_sprites.update()
            self.enemies.update()
            self.bullets.update()
            self.powerups.update()
            self.explosions.update()

        if self.boss:
            self.boss.update()
            self.boss.shoot(self.bullets)

        self.check_collisions()
        self.spawn_enemies()
        self.spawn_powerups()

        if not self.enemies and not self.boss:
            self.level_up()

        if self.player.lives <= 0:
            self.game_over()

        if self.player_speed_boost_timer > 0:
            self.player_speed_boost_timer -= self.dt
            if self.player_speed_boost_timer <= 0:
                self.player.speed /= self.player_speed_boost
                self.player_speed_boost = 1

        if self.player_exploded and self.player_respawn_time is not None:
            now = pygame.time.get_ticks()
            if now - self.player_respawn_time >= 3000:  # 3 секунды паузы
                self.player_exploded = False
                self.player.image = self.player.original_image
                self.player.rect.center = (512, 900)
                self.player_respawn_time = None

    def draw(self):
        """
        Отрисовывает все элементы игры.
        """
        self.screen.blit(self.background, (0, 0))
        self.all_sprites.draw(self.screen)
        self.enemies.draw(self.screen)
        self.bullets.draw(self.screen)
        self.powerups.draw(self.screen)
        self.explosions.draw(self.screen)
        if self.boss:
            self.screen.blit(self.font.render(f"Boss HP: {self.boss.hp}", True, (255, 255, 255)), (10, 50))
        self.screen.blit(self.font.render(f"Score: {self.score}", True, (255, 255, 255)), (10, 10))
        self.screen.blit(self.font.render(f"Lives: {self.player.lives}", True, (255, 255, 255)), (800, 10))
        pygame.display.flip()

    def check_collisions(self):
        """
        Проверяет столкновения между спрайтами.
        """
        # Проверка столкновений врагов и пуль
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, True)
        for enemy, bullets in hits.items():
            for bullet in bullets:
                enemy.take_damage(self.player_bullet_damage)
                self.score += SCORE_PER_ENEMY[enemy.type]
            if enemy.hp <= 0:
                self.score += SCORE_PER_ENEMY[enemy.type]
                explosion = Explosion(enemy.rect.center, 'sm' if enemy.type != 'strong' else 'lg')
                self.explosions.add(explosion)

        # Проверка столкновений босса и пуль
        if self.boss:
            hits = pygame.sprite.groupcollide({self.boss}, self.bullets, False, True)
            for boss, bullets in hits.items():
                for bullet in bullets:
                    boss.take_damage(self.player_bullet_damage)
                    self.score += SCORE_PER_ENEMY['boss']
                    explosion = Explosion(bullet.rect.center, 'sm')
                    self.explosions.add(explosion)
                if boss.hp <= 0:
                    self.score += SCORE_PER_ENEMY['boss']
                    explosion = Explosion(boss.rect.center, 'lg')
                    self.explosions.add(explosion)


        # Проверка столкновений игрока и врагов
        hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
        for hit in hits:
            self.player.take_damage()
            explosion = Explosion(hit.rect.center, 'sm' if hit.type != 'strong' else 'lg')
            self.explosions.add(explosion)
            if self.player.lives > 0:
                self.player_exploded = True
                self.player_respawn_time = pygame.time.get_ticks()
            else:
                self.game_over()

        # Проверка столкновений игрока и пуль
        hits = pygame.sprite.spritecollide(self.player, self.bullets, True)
        for hit in hits:
            self.player.take_damage()
            explosion = Explosion(hit.rect.center, 'sm')
            self.explosions.add(explosion)
            if self.player.lives > 0:
                self.player_exploded = True
                self.player_respawn_time = pygame.time.get_ticks()
            else:
                self.game_over()

        # Проверка столкновений игрока и усилителей
        hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for hit in hits:
            if hit.type == 'damage':
                self.player_bullet_damage = 5
                self.player_bullet_damage_timer = 30  # 30 секунд усиления
            elif hit.type == 'speed':
                self.player_speed_boost = 1.5
                self.player.speed *= self.player_speed_boost
                self.player_speed_boost_timer = 10  # 10 секунд усиления
            elif hit.type == 'life':
                self.player.lives += 1
            explosion = Explosion(hit.rect.center, 'sm')
            self.explosions.add(explosion)

        # Обновление таймера усиления урона
        if self.player_bullet_damage_timer > 0:
            self.player_bullet_damage_timer -= self.dt
            if self.player_bullet_damage_timer <= 0:
                self.player_bullet_damage = 5

    def spawn_enemies(self):
        """
        Создает новых врагов.
        """
        if random.random() < 0.02:
            enemy_type = random.choice(['weak', 'medium', 'strong', 'asteroid'])
            x = random.randint(50, 974)
            y = random.randint(-100, -50)
            if enemy_type == 'asteroid':
                enemy = Asteroid(x, y)
            else:
                enemy = Enemy(x, y, enemy_type)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

    def spawn_powerups(self):
        """
        Создает новые усилители.
        """
        now = pygame.time.get_ticks()
        if now > self.next_powerup_time:
            x = random.randint(50, 974)
            y = random.randint(-100, -50)
            powerup = Powerup(x, y)
            self.powerups.add(powerup)
            self.all_sprites.add(powerup)
            self.next_powerup_time = now + POWERUP_INTERVAL * 1000

    def level_up(self):
        """
        Переходит к следующему уровню.
        """
        self.level += 1
        if self.level % 3 == 0:
            self.boss = Boss()
            self.all_sprites.add(self.boss)
        else:
            for _ in range(self.level * 2):
                self.spawn_enemies()

    def game_over(self):
        """
        Обрабатывает конец игры.
        """
        if self.sound_enabled:
            self.game_over_sound.play()
        self.screen.fill((0, 0, 0))
        text = self.font.render("Game Over", True, (255, 255, 255))
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2))
        self.screen.blit(score_text,
                         (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 + text.get_height()))
        pygame.display.flip()
        pygame.time.wait(3000)
        self.running = False

    def show_start_screen(self):
        """
        Отображает начальный экран.
        """
        self.screen.fill((0, 0, 0))
        title = self.font.render("Space Shooter", True, (255, 255, 255))
        instructions = self.font.render("Press any key to start", True, (255, 255, 255))
        self.screen.blit(title, (
        SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - title.get_height() // 2 - 50))
        self.screen.blit(instructions, (
        SCREEN_WIDTH // 2 - instructions.get_width() // 2, SCREEN_HEIGHT // 2 + instructions.get_height() // 2 + 50))
        pygame.display.flip()
        self.wait_for_key()

    def show_pause_screen(self):
        """
        Отображает экран паузы.
        """
        self.screen.fill((0, 0, 0))
        title = self.font.render("Paused", True, (255, 255, 255))
        instructions = self.font.render("Press any key to continue", True, (255, 255, 255))
        self.screen.blit(title, (
        SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - title.get_height() // 2 - 50))
        self.screen.blit(instructions, (
        SCREEN_WIDTH // 2 - instructions.get_width() // 2, SCREEN_HEIGHT // 2 + instructions.get_height() // 2 + 50))
        pygame.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        """
        Ждет нажатия любой клавиши.
        """
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pygame.KEYUP:
                    waiting = False

    def toggle_sound(self):
        """
        Включает или выключает звук.
        """
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()


# Исправляем предупреждения
if __name__ == "__main__":
    game = Game()
    game.run()