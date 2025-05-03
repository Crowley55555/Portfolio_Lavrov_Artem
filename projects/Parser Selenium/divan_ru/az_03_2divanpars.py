import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Настройка Selenium с Firefox
options = Options()
options.add_argument('--headless')  # Режим без графического интерфейса
driver = webdriver.Firefox(options=options)

try:
    # Открываем страницу с диванами
    driver.get('https://www.divan.ru/category/divany-i-kresla')
    time.sleep(5)  # Ждем загрузки страницы

    # Прокручиваем страницу для загрузки всех товаров
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Находим все элементы с ценами
    price_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="price"]')

    # Извлекаем текст с ценами
    prices = [element.text for element in price_elements]

    # Сохраняем сырые данные в CSV
    with open('raw_prices.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Raw Price'])
        writer.writerows([[price] for price in prices])

    print(f"Собрано {len(prices)} цен. Данные сохранены в raw_prices.csv")

    # Очистка данных
    cleaned_prices = []
    for price in prices:
        # Удаляем все символы, кроме цифр
        cleaned = re.sub(r'[^\d]', '', price)
        if cleaned:  # Если остались цифры
            cleaned_prices.append(int(cleaned))

    # Сохраняем очищенные данные в CSV
    df = pd.DataFrame({'Price': cleaned_prices})
    df.to_csv('cleaned_prices.csv', index=False)

    # Анализ данных
    average_price = df['Price'].mean()
    print(f"Средняя цена на диваны: {average_price:.2f} руб.")

    # Визуализация
    plt.figure(figsize=(15, 5))

    # Гистограмма
    plt.subplot(1, 2, 1)
    plt.hist(df['Price'], bins=30, color='skyblue', edgecolor='black')
    plt.title('Распределение цен на диваны')
    plt.xlabel('Цена (руб)')
    plt.ylabel('Количество')
    plt.axvline(average_price, color='red', linestyle='dashed', linewidth=1, label=f'Средняя: {average_price:.2f} руб.')
    plt.legend()

    # Диаграмма рассеяния (индекс vs цена)
    plt.subplot(1, 2, 2)
    plt.scatter(range(len(df)), df['Price'], alpha=0.6, color='green')
    plt.title('Диаграмма рассеяния цен на диваны')
    plt.xlabel('Индекс товара')
    plt.ylabel('Цена (руб)')
    plt.axhline(average_price, color='red', linestyle='dashed', linewidth=1, label=f'Средняя: {average_price:.2f} руб.')
    plt.legend()

    plt.tight_layout()
    plt.savefig('prices_visualization.png')
    plt.show()
    print("Графики сохранены в prices_visualization.png")

finally:
    driver.quit()