import pandas as pd
import random

rows = 1000
data = []

crops = ["rice", "wheat", "maize", "cotton"]

for _ in range(rows):
    crop = random.choice(crops)

    if crop == "rice":
        N = random.randint(80, 110)
        P = random.randint(40, 60)
        K = random.randint(40, 60)
        temperature = round(random.uniform(20, 30), 2)
        humidity = round(random.uniform(70, 90), 2)
        ph = round(random.uniform(5.5, 7.0), 2)
        rainfall = round(random.uniform(200, 300), 2)

    elif crop == "wheat":
        N = random.randint(60, 90)
        P = random.randint(35, 55)
        K = random.randint(30, 50)
        temperature = round(random.uniform(15, 25), 2)
        humidity = round(random.uniform(55, 75), 2)
        ph = round(random.uniform(6.0, 7.5), 2)
        rainfall = round(random.uniform(100, 200), 2)

    elif crop == "maize":
        N = random.randint(50, 80)
        P = random.randint(40, 60)
        K = random.randint(40, 60)
        temperature = round(random.uniform(22, 32), 2)
        humidity = round(random.uniform(50, 70), 2)
        ph = round(random.uniform(5.8, 7.5), 2)
        rainfall = round(random.uniform(120, 220), 2)

    elif crop == "cotton":
        N = random.randint(70, 100)
        P = random.randint(35, 55)
        K = random.randint(35, 55)
        temperature = round(random.uniform(25, 35), 2)
        humidity = round(random.uniform(50, 75), 2)
        ph = round(random.uniform(5.5, 7.0), 2)
        rainfall = round(random.uniform(140, 250), 2)

    data.append([
        N, P, K,
        temperature,
        humidity,
        ph,
        rainfall,
        crop
    ])

df = pd.DataFrame(data, columns=[
    "N", "P", "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
    "label"
])

df.to_csv("dataset_1000.csv", index=False)

print("✅ dataset_1000.csv generated successfully!")
