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

print("=" * 60)
print("ИНДИВИДУАЛЬНОЕ ЗАДАНИЕ (ВАРИАНТ 31)")
print("3 параметра: [0.1-5], [0.1-3], [10%,20%,80%,90%]")
print("=" * 60)

# Генерация базовых данных (3 признака)
dataset, _ = make_blobs(
    n_samples=200,
    centers=4,
    n_features=3,
    cluster_std=0.5,
    random_state=31
)

# Приводим param1 к диапазону [0.1, 5]
dataset[:, 0] = np.interp(dataset[:, 0],
                          (dataset[:, 0].min(), dataset[:, 0].max()),
                          (0.1, 5))

# Приводим param2 к диапазону [0.1, 3]
dataset[:, 1] = np.interp(dataset[:, 1],
                          (dataset[:, 1].min(), dataset[:, 1].max()),
                          (0.1, 3))

# Параметр 3: категории 10%, 20%, 80%, 90%
categories = [0.1, 0.2, 0.8, 0.9]
dataset[:, 2] = np.random.choice(categories, 200)

# Создаём DataFrame
df = pd.DataFrame(dataset, columns=['param1', 'param2', 'param3'])
print("\nНабор данных (первые 10 строк):")
print(df.head(10))

# ============================================================
# ГРАФИК 1: МЕТОД ЛОКТЯ (Elbow)
# ============================================================
model = KMeans()
visualizer = KElbowVisualizer(model, k=(1, 12))
visualizer.fit(df[['param1', 'param2']])
visualizer.show(outpath="individual_elbow.png")
print("\nГрафик 1 сохранён: individual_elbow.png")

# Определяем оптимальное k
optimal_k = visualizer.elbow_value_
print(f"Оптимальное количество кластеров: {optimal_k}")

# ============================================================
# КЛАСТЕРИЗАЦИЯ С ОПТИМАЛЬНЫМ k
# ============================================================
kmeans = KMeans(n_clusters=optimal_k, init='k-means++', random_state=31).fit(df[['param1', 'param2']])

print("\nПрогнозируемые кластеры (первые 20):")
print(kmeans.labels_[:20])

print("\nКоординаты центроидов:")
print(kmeans.cluster_centers_)

print(f"\nВнутрикластерная сумма квадратов: {kmeans.inertia_}")
print(f"Количество итераций: {kmeans.n_iter_}")

print("\nРазмер каждого кластера:")
print(Counter(kmeans.labels_))

# ============================================================
# ГРАФИК 2: ДИАГРАММА РАССЕЯНИЯ С КЛАСТЕРАМИ И ЦЕНТРОИДАМИ
# ============================================================
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='param1', y='param2', hue=kmeans.labels_, palette='viridis')
plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1],
            marker='X', c='red', s=200, label='centroids')
plt.title('Кластеризация данных (вариант 31)')
plt.xlabel('Параметр 1 [0.1; 5]')
plt.ylabel('Параметр 2 [0.1; 3]')
plt.legend()
plt.savefig("individual_clusters.png")



