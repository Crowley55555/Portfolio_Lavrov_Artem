import pygame
from settings import BOSS_SIZE, BOSS_HP, BOSS_SHOOT_INTERVAL
from utils import load_image
from bullet import Bullet


class Boss(pygame.sprite.Sprite):
    """
    Класс Boss представляет босса в игре.
    Босс — это особый противник, который движется по экрану, стреляет пулями и может получать урон от игрока.
    """

    def __init__(self):
        """
        Инициализирует нового босса.

        - Загружает изображение босса и задает его размеры.
        - Устанавливает начальную позицию босса на экране.
        - Определяет скорость движения босса.
        - Задает начальное количество здоровья (HP).
        - Устанавливает интервал между выстрелами.
        - Инициализирует таймер последнего выстрела для контроля частоты стрельбы.
        """
        super().__init__()

        # Загрузка изображения босса и установка его размеров
        self.image = load_image('boss.png',
                                BOSS_SIZE)  # Загружаем изображение босса и масштабируем его до нужного размера
        self.rect = self.image.get_rect(center=(512, 100))  # Размещаем босса в центре верхней части экрана

        # Настройка характеристик босса
        self.speed = 2  # Скорость движения босса по вертикали
        self.hp = BOSS_HP  # Количество здоровья босса (из settings.py)
        self.shoot_interval = BOSS_SHOOT_INTERVAL  # Интервал между выстрелами (в секундах, из settings.py)
        self.last_shot_time = 0  # Время последнего выстрела (используется для контроля частоты стрельбы)

    def update(self):
        """
        Обновляет положение босса на экране.

        - Двигает босса вниз по экрану с заданной скоростью.
        - Если босс выходит за нижнюю границу экрана, он удаляется из игры.
        """
        self.rect.y += self.speed  # Двигаем босса вниз по оси Y

        # Проверяем, не вышел ли босс за пределы экрана
        if self.rect.y > 1024:  # Если координата Y больше высоты экрана (1024 пикселей)
            self.kill()  # Удаляем босса из игры

    def take_damage(self, damage):
        """
        Наносит урон боссу.

        :param damage: Количество урона, которое получает босс.
        Если здоровье босса становится меньше или равно нулю, он удаляется из игры.
        """
        self.hp -= damage  # Уменьшаем HP босса на указанное количество урона

        # Если здоровье босса достигло нуля или ниже, удаляем его
        if self.hp <= 0:
            self.kill()  # Удаляем босса из игры

    def shoot(self, bullet_group):
        """
        Создает пулю, выпущенную боссом.

        :param bullet_group: Группа спрайтов, куда будет добавлена новая пуля.

        - Проверяет, прошло ли достаточно времени с момента последнего выстрела.
        - Если время выстрела еще не пришло, ничего не делает.
        - Если время выстрела пришло, создает новую пулю и добавляет ее в группу спрайтов.
        """
        now = pygame.time.get_ticks()  # Получаем текущее время в миллисекундах

        # Проверяем, прошло ли достаточно времени с момента последнего выстрела
        if now - self.last_shot_time > self.shoot_interval * 1000:  # Переводим интервал в миллисекунды
            # Создаем новую пулю
            bullet = Bullet(self.rect.centerx, self.rect.bottom, 1)  # Создаем пулю внизу босса

            # Добавляем пулю в группу спрайтов
            bullet_group.add(bullet)

            # Обновляем время последнего выстрела
            self.last_shot_time = now