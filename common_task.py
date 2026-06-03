import matplotlib
matplotlib.use('Agg')

import warnings
warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'

from sklearn.datasets import make_blobs
import pandas as pd
from sklearn.cluster import KMeans
from yellowbrick.cluster import KElbowVisualizer
from collections import Counter
import seaborn as sns

print("=" * 70)
print("ЛАБОРАТОРНАЯ РАБОТА №6 - ОБЩАЯ ЗАДАНИЕ")
print("Кластеризация данных методом K-средних (KMeans)")
print("Студент: Папсуева Э.А.")
print("=" * 70)

dataset, classes = make_blobs(
    n_samples=200,
    centers=4,
    n_features=2,
    cluster_std=0.5,
    random_state=0
)

df = pd.DataFrame(dataset, columns=['var1', 'var2'])
print("\nНабор данных (первые 5 строк):")
print(df.head())

model = KMeans()
visualizer = KElbowVisualizer(model, k=(1, 12))
visualizer.fit(df)
visualizer.show(outpath="common_elbow.png")

kmeans = KMeans(n_clusters=4, init='k-means++', random_state=0).fit(df)

print("\nПрогнозируемые кластеры (первые 20):")
print(kmeans.labels_[:20])

print("\nКоординаты центроидов:")
print(kmeans.cluster_centers_)

print(f"\nВнутрикластерная сумма квадратов: {kmeans.inertia_}")
print(f"Количество итераций: {kmeans.n_iter_}")

print("\nРазмер каждого кластера:")
print(Counter(kmeans.labels_))

# ============================================================
# ОДИН ГРАФИК: точки + центроиды
# ============================================================
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='var1', y='var2', hue=kmeans.labels_, palette='viridis')
plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1],
            marker='X', c='red', s=200, label='centroids')
plt.title('Кластеризация данных методом K-средних')
plt.xlabel('var1')
plt.ylabel('var2')
plt.legend()
plt.savefig("common_clusters.png")


