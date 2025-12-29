!pip install -q PyDrive2

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from oauth2client.client import GoogleCredentials
from google.colab import auth
import pandas as pd, os, re

auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

ids = {
 "service.csv":      "1D9xbZSQ9X2Ta3-LEPvvVWtSgY-0wtANk",
 "questionnaire.csv":"1mXcdJZZHGsqPl-DsbNnM6a4owIw36gxn",
 "manager.csv":      "1krSKJ4TXmDY-rJI2_HkthVvGnwnafkF_",
 "client.csv":       "1c3TQ7FgDelM2SQITe2HoYCX_itEu5srH",
 "branch.csv":       "1mwt5S2l8mQrqdowLpD_I5X8YOMKcA9iC"
}

TMP = "/content/_tmp"
os.makedirs(TMP, exist_ok=True)
for name,fid in ids.items():
    drive.CreateFile({'id':fid}).GetContentFile(os.path.join(TMP,name))

# читатель с простой fallback-логикой
def rc(p):
    try: return pd.read_csv(p)
    except: return pd.read_csv(p, encoding='cp1251')

service = rc(f"{TMP}/service.csv")
q = rc(f"{TMP}/questionnaire.csv")
mgr = rc(f"{TMP}/manager.csv")
client = rc(f"{TMP}/client.csv")
branch = rc(f"{TMP}/branch.csv")

# нормальные имена колонок в данных
df = (q.merge(service, on="service_id", how="left")
       .merge(client[['client_id','gender']], on="client_id", how="left")
       .merge(mgr[['manager_id','manager_name']], on="manager_id", how="left")
       .merge(branch[['branch_id','branch_name']], on="branch_id", how="left"))


# 1) самая частая услуга
svc_counts = df['service_name'].value_counts()
print("\n1) Самая частая услуга(ы):")
if svc_counts.empty:
    print("   Нет данных")
else:
    top_n = int(svc_counts.max())
    for s in svc_counts[svc_counts==top_n].index.tolist():
        print(f"   {s} — {top_n} запрос(ов)")

# 2) сколько запросов от женщин и мужчин
print("\n2) Запросы по полу:")

gender_counts = df["gender"].value_counts()

men = gender_counts.get("М", 0)
women = gender_counts.get("Ж", 0)

print(f"Мужчины: {men}")
print(f"Женщины: {women}")

# 3) по регионам — топ-услуги; сортировка по убыванию total, при равенстве — алфавит региона
grp = df.groupby(['branch_name','service_name']).size().reset_index(name='n')
rows = []
for region, g in grp.groupby('branch_name'):
    total = int(g['n'].sum())
    mx = int(g['n'].max())
    tops = sorted(g.loc[g['n']==mx,'service_name'].tolist())
    rows.append((region, total, tops, mx))
rows.sort(key=lambda x: (-x[1], x[0] or ''))
print("\n3) По регионам (region — total | top services):")
for region, total, tops, mx in rows:
    print(f"   {region} — {total} | top: {', '.join(tops)} (count={mx})")
