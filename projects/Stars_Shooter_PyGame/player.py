import pygame
from settings import PLAYER_SIZE, PLAYER_SPEED, PLAYER_LIVES, FPS, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import load_image
from bullet import Bullet


class Player(pygame.sprite.Sprite):
    """
    Класс Player представляет игрока в игре.
    Игрок может двигаться по горизонтали, стрелять пулями и получать урон от врагов.
    """

    def __init__(self, screen_width, screen_height):
        """
        Инициализирует нового игрока.

        :param screen_width: Ширина экрана (используется для ограничения движения).
        :param screen_height: Высота экрана (используется для установки начальной позиции).

        Логика метода:
        1. Загружает два изображения игрока: нормальное (`original_image`) и поврежденное (`damaged_image`).
        2. Устанавливает начальную позицию игрока внизу экрана по центру.
        3. Инициализирует характеристики игрока: скорость, жизни, таймеры для повреждений и перезарядки.
        """
        super().__init__()

        # Вывод размеров экрана для отладки
        print(f"Screen Width: {screen_width}, Screen Height: {screen_height}")

        # Загрузка изображений игрока
        self.original_image = load_image('player.png', PLAYER_SIZE).convert_alpha()  # Нормальный спрайт игрока
        self.damaged_image = load_image('player_damaged.png', PLAYER_SIZE)  # Поврежденный спрайт игрока
        self.image = self.original_image  # Текущий спрайт игрока

        # Установка начальной позиции игрока
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height - self.rect.height)  # Размещаем игрока внизу экрана

        # Настройка характеристик игрока
        self.speed = PLAYER_SPEED  # Скорость движения игрока
        self.lives = PLAYER_LIVES  # Количество жизней игрока
        self.last_shot_time = 0  # Время последнего выстрела (для контроля перезарядки)
        self.bullet2_cooldown = 0  # Таймер перезарядки специальных пуль
        self.damage_timer = 0  # Таймер показа поврежденного спрайта

        # Сохраняем размеры экрана для ограничения движения
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT

    def update(self):
        """
        Обновляет состояние игрока.

        Логика метода:
        1. Двигает игрока в соответствии с положением мыши.
        2. Ограничивает движение внутри границ экрана.
        3. Обновляет таймер повреждения и перезарядку специальных пуль.

        - `mouse_x`: Текущая координата X мыши.
        - `min_x`: Минимальная координата X (левая граница).
        - `max_x`: Максимальная координата X (правая граница).
        """
        mouse_x, _ = pygame.mouse.get_pos()  # Получаем текущее положение мыши

        # Рассчитываем минимальное и максимальное значение для центра игрока
        min_x = self.rect.width // 2  # Минимальная координата X (левая граница)
        max_x = self.screen_width - self.rect.width // 2  # Максимальная координата X (правая граница)

        # Устанавливаем центр игрока между минимумом и максимумом
        self.rect.centerx = max(min(mouse_x, max_x), min_x)

        # Обработка таймера повреждения
        if self.damage_timer > 0:
            self.damage_timer -= 1 / FPS  # Уменьшаем таймер на одну секунду (в зависимости от FPS)
            if self.damage_timer <= 0:
                self.image = self.original_image  # Возвращаем нормальный спрайт игрока

        # Обработка перезарядки специальных пуль
        if self.bullet2_cooldown > 0:
            self.bullet2_cooldown -= 1 / FPS  # Уменьшаем таймер перезарядки

    def shoot(self, bullet_group, bullet_type):
        """
        Создает пулю, выпущенную игроком.

        :param bullet_group: Группа спрайтов, куда будет добавлена новая пуля.
        :param bullet_type: Тип пули (1 — обычная пуля, 2 — специальная пуля).

        Логика метода:
        1. Если тип пули равен 1, создается обычная пуля без ограничений.
        2. Если тип пули равен 2, создается специальная пуля только если перезарядка завершена.
        """
        now = pygame.time.get_ticks()  # Получаем текущее время в миллисекундах

        if bullet_type == 1:
            # Создаем обычную пулю
            bullet = Bullet(self.rect.centerx, self.rect.top, 1)
            bullet_group.add(bullet)
        elif bullet_type == 2 and self.bullet2_cooldown <= 0:
            # Создаем специальную пулю, если перезарядка завершена
            bullet = Bullet(self.rect.centerx, self.rect.top, 2)
            bullet_group.add(bullet)
            self.bullet2_cooldown = 10  # Устанавливаем таймер перезарядки на 10 секунд

    def take_damage(self):
        """
        Обрабатывает получение урона игроком.

        Логика метода:
        1. Уменьшает количество жизней игрока.
        2. Изменяет спрайт игрока на поврежденный.
        3. Устанавливает таймер показа поврежденного спрайта.

        - `self.lives`: Уменьшается на 1 при получении урона.
        - `self.image`: Меняется на поврежденный спрайт.
        - `self.damage_timer`: Устанавливается на 0.5 секунды.
        """
        self.lives -= 1  # Уменьшаем количество жизней
        self.image = self.damaged_image  # Меняем спрайт на поврежденный
        self.damage_timer = 0.5 * FPS  # Устанавливаем таймер показа поврежденного спрайта (0.5 секунды)