import matplotlib
matplotlib.use('Agg')

import warnings
warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'

import numpy as np
from sklearn.datasets import make_blobs
import pandas as pd
from sklearn.cluster import KMeans
from yellowbrick.cluster import KElbowVisualizer
from collections import Counter
import seaborn as sns

print("=" * 70)
print("ЛАБОРАТОРНАЯ РАБОТА №6 - ИНДИВИДУАЛЬНОЕ ЗАДАНИЕ")
print("Вариант 29 (как у Очировой) / Вариант 2 из списка")
print("3 параметра: [0.01-1], [1-300], [Самара, Тольятти, Москва]")
print("=" * 70)

n_samples = 200

# Генерация базовых данных (2 числовых параметра для кластеризации)
dataset, _ = make_blobs(
    n_samples=n_samples,
    centers=4,
    n_features=2,
    cluster_std=0.8,
    random_state=29
)

# Приводим param1 к диапазону [0.01, 1]
dataset[:, 0] = np.interp(dataset[:, 0],
                          (dataset[:, 0].min(), dataset[:, 0].max()),
                          (0.01, 1))

# Приводим param2 к диапазону [1, 300]
dataset[:, 1] = np.interp(dataset[:, 1],
                          (dataset[:, 1].min(), dataset[:, 1].max()),
                          (1, 300))

# Параметр 3: категории (Самара, Тольятти, Москва)
cities = ['Самара', 'Тольятти', 'Москва']
city_codes = {'Самара': 0, 'Тольятти': 1, 'Москва': 2}
city_array = np.random.choice(cities, n_samples)

# Создаём DataFrame
df = pd.DataFrame(dataset, columns=['param1', 'param2'])
df['city'] = city_array
df['city_code'] = df['city'].map(city_codes)

print("\n[1] СГЕНЕРИРОВАННЫЕ ДАННЫЕ")
print("Первые 15 строк:")
print(df.head(15))

print("\nСтатистика по параметрам:")
print(df[['param1', 'param2']].describe())

print("\nРаспределение по городам:")
print(df['city'].value_counts())

model = KMeans(random_state=29)
visualizer = KElbowVisualizer(model, k=(1, 10))
visualizer.fit(df[['param1', 'param2']])
visualizer.show(outpath="individual_elbow.png")
print("\nГрафик 1 сохранён: individual_elbow.png")

optimal_k = visualizer.elbow_value_
print(f"Оптимальное количество кластеров: {optimal_k}")

kmeans = KMeans(n_clusters=optimal_k, init='k-means++', random_state=29)
kmeans.fit(df[['param1', 'param2']])
df['cluster'] = kmeans.labels_

print("\n[2] РЕЗУЛЬТАТЫ КЛАСТЕРИЗАЦИИ")

print("\nПрогнозируемые кластеры (первые 20):")
print(kmeans.labels_[:20])

print("\nКоординаты центроидов:")
for i, centroid in enumerate(kmeans.cluster_centers_):
    print(f"  Центроид {i}: [param1={centroid[0]:.3f}, param2={centroid[1]:.1f}]")

print(f"\nВнутрикластерная сумма квадратов: {kmeans.inertia_:.2f}")
print(f"Количество итераций: {kmeans.n_iter_}")

print("\nРазмер каждого кластера:")
cluster_sizes = Counter(kmeans.labels_)
for cluster_id in sorted(cluster_sizes.keys()):
    print(f"  Кластер {cluster_id}: {cluster_sizes[cluster_id]} точек")

print("\n[3] РАСПРЕДЕЛЕНИЕ ГОРОДОВ ПО КЛАСТЕРАМ:")
for cluster_id in sorted(df['cluster'].unique()):
    cluster_data = df[df['cluster'] == cluster_id]
    city_dist = cluster_data['city'].value_counts()
    print(f"\nКластер {cluster_id} ({len(cluster_data)} точек):")
    for city, count in city_dist.items():
        print(f"    {city}: {count}")

plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='param1', y='param2', hue='cluster', palette='viridis')
plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1],
            marker='X', c='red', s=200, label='centroids')
plt.title(f'Кластеризация данных (вариант 2, k={optimal_k})')
plt.xlabel('Параметр 1 [0.01; 1]')
plt.ylabel('Параметр 2 [1; 300]')
plt.legend()
plt.savefig("individual_clusters.png")
print("\nГрафик 2 сохранён: individual_clusters.png")

plt.figure(figsize=(10, 6))
plt.scatter(df['param1'], df['param2'], c='blue', alpha=0.6)
plt.title('Исходные данные (без кластеризации)')
plt.xlabel('Параметр 1 [0.01; 1]')
plt.ylabel('Параметр 2 [1; 300]')
plt.grid(True, alpha=0.3)
plt.savefig("individual_raw_data.png")
print("График 3 сохранён: individual_raw_data.png")

plt.figure(figsize=(10, 6))
colors_city = {'Самара': 'blue', 'Тольятти': 'green', 'Москва': 'red'}
for city in cities:
    city_data = df[df['city'] == city]
    plt.scatter(city_data['param1'], city_data['param2'], 
                c=colors_city[city], label=city, alpha=0.6)

plt.title('Распределение данных по городам (Самара, Тольятти, Москва)')
plt.xlabel('Параметр 1 [0.01; 1]')
plt.ylabel('Параметр 2 [1; 300]')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("individual_by_city.png")
print("График 4 сохранён: individual_by_city.png")


