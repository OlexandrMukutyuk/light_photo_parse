import os
import aiohttp
import asyncio
from PIL import Image
import numpy as np
from datetime import datetime, timedelta
import io
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/process_dates")
async def process_dates():
    todayDate = get_today_date()
    tomorrowDate = get_tomorrow_date()
    dates = [todayDate, tomorrowDate]
    forAPI = {}

    for date in dates:
        loadPath = await loadImage(date)
        if loadPath:
            croppedPath = await cropImage(date)
            fetched = await fetch(date)
            forAPI[date] = fetched

    return forAPI


def get_tomorrow_date():
    # Отримання поточної дати
    today = datetime.now()
    # Обчислення дати наступного дня
    tomorrow = today + timedelta(days=1)
    # Форматування дати у вигляді dd-mm-yy
    formatted_date = tomorrow.strftime("%d-%m-%y")
    return formatted_date

def get_today_date(): 
    # Отримання поточної дати
    current_date = datetime.now()
    # Форматування дати у вигляді dd-mm-yy
    today_date = current_date.strftime("%d-%m-%y")
    return today_date

todayDate = get_today_date()
tomorrowDate = get_tomorrow_date()
dates = [todayDate, tomorrowDate]

forAPI = {}

async def main():
    for date in dates:
        loadPath = await loadImage(date)
        if loadPath:
            croppedPath = await cropImage(date)
            fetched = await fetch(date)
            forAPI[date] = fetched
    print(forAPI)

async def loadImage(date):
    # Заголовки
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    }

    # URL зображення
    image_url = f"https://energy.volyn.ua/spozhyvacham/perervy-u-elektropostachanni/hrafik-vidkliuchen/!img/{date}.jpg"

    # Назва папки
    folder_name = "images"

    # Назва файлу
    image_name = f"downloaded_image_{date}.jpg"

    # Створення папки, якщо її не існує
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Шлях до файлу
    image_path = os.path.join(folder_name, image_name)

    # Асинхронне завантаження зображення
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url, headers=headers) as response:
            if response.status == 200:
                image_data = await response.read()
                image = Image.open(io.BytesIO(image_data))
                image = image.convert("RGB")  # Переконайтеся, що зображення у форматі RGB
                image.save(image_path, format="JPEG")
                print(f"Image successfully downloaded: {image_path}")
                return image_path
            else:
                print(f"Failed to retrieve image. HTTP Status code: {response.status}")
                return None

async def cropImage(date):
    # Завантаження зображення
    image_path = f'images/downloaded_image_{date}.jpg'
    image = Image.open(image_path)

    # Визначення розмірів для обрізки
    top_crop = 135  # Висота обрізки зверху
    left_crop = 85  # Ширина обрізки зліва
    right_crop = 85  # Ширина обрізки справа
    bottom_crop = 125  # Висота обрізки знизу

    # Визначення нових розмірів
    width, height = image.size
    new_width = width - left_crop - right_crop
    new_height = height - top_crop - bottom_crop

    # Обрізка зображення
    cropped_image = image.crop((left_crop, top_crop, left_crop + new_width, top_crop + new_height))

    # Збереження обрізаного зображення
    cropped_image_path = f'images/cropped_image_{date}.jpg'
    cropped_image.save(cropped_image_path, format="JPEG")

    return cropped_image_path

async def fetch(date):
    rows = 6
    cols = 24

    # Load the new image
    image_path_new = f'images/cropped_image_{date}.jpg'
    image_new = Image.open(image_path_new)

    # Convert the image to grayscale for easier processing
    image_gray_new = image_new.convert('L')

    # Convert the image to a numpy array
    image_array_new = np.array(image_gray_new)

    # Define threshold to separate light and dark squares
    threshold_new = 128
    binary_array_new = (image_array_new < threshold_new).astype(int)

    # Resize array to match the grid (6 rows by 24 columns)
    resized_array_new = np.zeros((rows, cols), dtype=int)
    cell_height_new = image_array_new.shape[0] // rows
    cell_width_new = image_array_new.shape[1] // cols

    # Populate the resized array based on the average color value in each cell
    for row in range(rows):
        for col in range(cols):
            cell_new = binary_array_new[row * cell_height_new:(row + 1) * cell_height_new, col * cell_width_new:(col + 1) * cell_width_new]
            resized_array_new[row, col] = int(np.mean(cell_new) > 0.5)

    result = resized_array_new.tolist()
    return result

if __name__ == "__main__":
    # asyncio.run(main())
    uvicorn.run(app, host="0.0.0.0", port=8000)