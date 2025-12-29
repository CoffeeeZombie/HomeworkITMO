!pip install -q PyDrive2

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
from google.colab import auth
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

# импорты и папка для временных файлов мб
import os, re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

TMP = "/content/tmp_games"
os.makedirs(TMP, exist_ok=True)


FOLDER_ID = "16JRLbMGbNc36eHe8wG4isHUgfQzu7n0z"

# скачиваем первый CSV из папки, мб по ссылке
files = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
if not files:
    raise SystemExit("Папка пустая или нет доступа — остановка.")
f = next((x for x in files if x['title'].lower().endswith('.csv')), files[0])
name = re.sub(r'[\\/:"*?<>|]+', '_', f['title'])
path = os.path.join(TMP, name)
f.GetContentFile(path)
print("Загрузил:", name)

# читаем датасет, на всякий двумя кодировками
try:
    df = pd.read_csv(path)
except Exception:
    df = pd.read_csv(path, encoding='cp1251', engine='python')

# приведение имён столбцов к норм виду
df.columns = [str(c).strip() for c in df.columns]

# простая предобработка
# 1) Global_Sales - если есть. иначе суммируем regional_*_sales
if 'Global_Sales' not in df.columns:
    sales_cols = [c for c in df.columns if 'sales' in c.lower()]
    if sales_cols:
        df['Global_Sales'] = df[sales_cols].sum(axis=1)
    else:
        df['Global_Sales'] = np.nan  # ну ладно, оставим NaN

# 2) User_Score - убрать tbd и привести к числу
if 'User_Score' in df.columns:
    df['User_Score'] = df['User_Score'].replace('tbd', np.nan)
    df['User_Score'] = pd.to_numeric(df['User_Score'], errors='coerce')

# 3) Critic_Score к числу
if 'Critic_Score' in df.columns:
    df['Critic_Score'] = pd.to_numeric(df['Critic_Score'], errors='coerce')

# 4) Year_of_Release в int
if 'Year_of_Release' in df.columns:
    df['Year_of_Release'] = pd.to_numeric(df['Year_of_Release'], errors='coerce').astype('Int64')

# несколько быстрых фактов, можно удалить
print("\nКороткие факты:")
if 'Name' in df.columns and df['Global_Sales'].notna().any():
    top5 = df.nlargest(5, 'Global_Sales')[['Name','Global_Sales']]
    print("Top-5 игр по Global_Sales:\n", top5.to_string(index=False))
if 'Genre' in df.columns:
    gen_sum = df.groupby('Genre')['Global_Sales'].sum().sort_values(ascending=False).head(5)
    print("\nТоп-5 жанров по суммарным продажам:\n", gen_sum.to_string())

# простые графиков
plt.style.use('seaborn-v0_8')  # просто чтобы выглядело нормально
# 1) Global_Sales
plt.figure(figsize=(8,4))
genre_counts = df['Genre'].value_counts()

plt.bar(genre_counts.index, genre_counts.values)
plt.title("Распределение игр по жанрам")
plt.xlabel("Жанр")
plt.ylabel("Количество игр")
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
plt.show()

# 2) Топ жанров по сумме продаж
if 'Genre' in df.columns:
    top_genres = df.groupby('Genre')['Global_Sales'].sum().sort_values(ascending=False).head(10)
    plt.figure(figsize=(8,4))
    plt.bar(top_genres.index, top_genres.values)
    plt.xticks(rotation=45, ha='right')
    plt.title("Топ-10 жанров по суммарным продажам")
    plt.tight_layout()
    plt.show()

# 3) Релизы по годам
if 'Year_of_Release' in df.columns:
    years = df['Year_of_Release'].dropna().astype(int).value_counts().sort_index()
    plt.figure(figsize=(10,3))
    plt.plot(years.index, years.values, marker='o')
    plt.title("Релизы по годам")
    plt.xlabel("Год")
    plt.ylabel("Число релизов")
    plt.tight_layout()
    plt.show()

# Взаимодействия
# A) Global_Sales vs Critic_Score
if 'Critic_Score' in df.columns and df['Global_Sales'].notna().any():
    sub = df[['Global_Sales','Critic_Score']].dropna()
    plt.figure(figsize=(6,4))
    plt.scatter(sub['Critic_Score'], sub['Global_Sales'], alpha=0.6)
    plt.title("Global_Sales vs Critic_Score")
    plt.xlabel("Critic_Score")
    plt.ylabel("Global_Sales")
    plt.tight_layout()
    plt.show()

# B) Global_Sales vs User_Score
if 'User_Score' in df.columns and df['Global_Sales'].notna().any():
    sub = df[['Global_Sales','User_Score']].dropna()
    plt.figure(figsize=(6,4))
    plt.scatter(sub['User_Score'], sub['Global_Sales'], alpha=0.6)
    plt.title("Global_Sales vs User_Score")
    plt.xlabel("User_Score")
    plt.ylabel("Global_Sales")
    plt.tight_layout()
    plt.show()

# C) Boxplot Global_Sales по топ-6 жанрам
if 'Genre' in df.columns and df['Global_Sales'].notna().any():
    top_genres_list = df['Genre'].value_counts().head(6).index.tolist()
    data = [df.loc[df['Genre']==g,'Global_Sales'].dropna() for g in top_genres_list]
    plt.figure(figsize=(10,4))
    plt.boxplot(data, labels=top_genres_list, showfliers=False)
    plt.title("Global_Sales по жанрам (top-6 по частоте)")
    plt.ylabel("Global_Sales")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

# Доп. простой, можно удалить на самом деле
if 'Platform' in df.columns and df['Global_Sales'].notna().any():
    mean_pl = df.groupby('Platform')['Global_Sales'].mean().sort_values(ascending=False).head(8)
    print("\nСредние Global_Sales по топ-8 платформ:\n", mean_pl.to_string())

print("Вот и сказочке конец, а кто слушал огурчик")
