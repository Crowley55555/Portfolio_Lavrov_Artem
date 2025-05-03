import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt

# Настройки для Firefox
options = Options()
options.headless = True  # Запуск в фоновом режиме

# Инициализация драйвера Firefox
driver = webdriver.Firefox(options=options)

try:
    # Открываем страницу
    url = "https://www.cian.ru/snyat-kvartiru-1-komn-ili-2-komn/"
    driver.get(url)

    # Ждем загрузки страницы
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-mark='OfferTitle']"))
    )

    # Прокручиваем страницу для загрузки всех объявлений
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Находим все элементы с ценами
    price_elements = driver.find_elements(By.CSS_SELECTOR, "[data-mark='MainPrice']")

    # Извлекаем текст с ценами
    prices = []
    for element in price_elements:
        price_text = element.text
        prices.append(price_text)

    # Создаем DataFrame и сохраняем в CSV
    df = pd.DataFrame(prices, columns=["Price"])
    df.to_csv("cian_prices.csv", index=False)

    print(f"Сохранено {len(prices)} цен в файл 'cian_prices.csv'")

finally:
    # Закрываем браузер
    driver.quit()


# Функция для очистки цены
def clean_price(price_str):
    # Удаляем "₽/мес" и все нецифровые символы, кроме цифр
    cleaned = re.sub(r"[^\d]", "", price_str)
    return int(cleaned) if cleaned else None


# Читаем CSV файл
df = pd.read_csv("cian_prices.csv")

# Применяем функцию очистки к каждой цене
df["Price"] = df["Price"].apply(clean_price)

# Удаляем строки с None (если такие есть)
df = df.dropna()

# Сохраняем обработанные данные
df.to_csv("cian_prices_processed.csv", index=False)

print("Обработанные данные сохранены в 'cian_prices_processed.csv'")
print("Пример обработанных цен:")
print(df.head())

# Чтение обработанных данных
df = pd.read_csv("cian_prices_processed.csv")

# Преобразуем цены в numpy array
prices = df['Price'].values

# Настройка гистограммы
plt.figure(figsize=(12, 6))
plt.title('Распределение цен на аренду квартир (1-2 комнаты) на ЦИАН', fontsize=14)
plt.xlabel('Цена (руб/мес)', fontsize=12)
plt.ylabel('Количество предложений', fontsize=12)

# Построение гистограммы с автоматическим определением бинов
n, bins, patches = plt.hist(prices, bins='auto', color='skyblue', edgecolor='black')

# Добавляем среднюю цену и медиану
mean_price = np.mean(prices)
median_price = np.median(prices)
plt.axvline(mean_price, color='red', linestyle='dashed', linewidth=1, label=f'Средняя: {int(mean_price):,} руб')
plt.axvline(median_price, color='green', linestyle='dashed', linewidth=1, label=f'Медиана: {int(median_price):,} руб')

# Форматирование оси X (разделители тысяч)
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))

# Легенда и сетка
plt.legend()
plt.grid(axis='y', alpha=0.5)

# Сохранение графика
plt.savefig('cian_prices_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# Вывод статистики
print("\nСтатистика по ценам:")
print(f"Минимальная цена: {np.min(prices):,} руб")
print(f"Максимальная цена: {np.max(prices):,} руб")
print(f"Средняя цена: {mean_price:,.0f} руб")
print(f"Медианная цена: {median_price:,.0f} руб")
print(f"Стандартное отклонение: {np.std(prices):,.0f} руб")