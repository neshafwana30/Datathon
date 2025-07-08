from geopy.distance import geodesic


import pandas as pd

file_path = "dataset/1742574481558_Dataset-ME-2025.xlsx"  # ganti dengan path ke file kamu
xls = pd.ExcelFile(file_path)
print(xls.sheet_names)




# --- 1. DC Sheet: Tampilkan Area dan jumlah baris per Area ---
df_dc = pd.read_excel(xls, sheet_name="DC")
area_counts = df_dc['Area'].value_counts().reset_index()
area_counts.columns = ['Area', 'Jumlah Baris']
# print("Jumlah baris per Area di sheet 'DC':")
# print(area_counts)



df_dc.columns

import pandas as pd

# --- DC Sheet ---
df_dc = pd.read_excel(xls, sheet_name="DC Final")
area_set = set(df_dc['Area'].dropna().unique())

# --- Middle Mile Sheet ---
df_middle = pd.read_excel(xls, sheet_name="Resources", header=3)
origin_area_set = set(df_middle['BRANCH'].dropna().unique())

# --- Bandingkan ---
same_areas = area_set & origin_area_set  # irisan = yang sama
only_in_dc = area_set - origin_area_set
only_in_middle = origin_area_set - area_set

# --- Print Areas ---
print("✅ Area yang ADA di keduanya:")
print(sorted(same_areas))

print("\n📌 Area yang HANYA ADA di sheet 'DC Final':")
print(sorted(only_in_dc))

# --- Show count of each Type for areas only in DC Final ---
only_in_dc_df = df_dc[df_dc['Area'].isin(only_in_dc)]
type_counts = only_in_dc_df['Type'].value_counts()

print("\n📌 Jumlah setiap Type pada area yang hanya ada di sheet 'DC Final':")
print(type_counts)

print("\n📌 Area yang HANYA ADA di sheet 'resources':")
print(sorted(only_in_middle))

only_in_dc_df = df_dc[df_dc['Area'].isin(only_in_dc)]
filtered_areas = only_in_dc_df[only_in_dc_df['Type'] != 'Depo'][['Area', 'Type']]

print("\n📌 Area yang HANYA ADA di sheet 'DC Final' dan Type-nya bukan 'Depo':")
print(filtered_areas)


import pandas as pd

# Load dari Excel
xls = pd.ExcelFile("dataset/1742574481558_Dataset-ME-2025.xlsx")
df_dc = pd.read_excel(xls, sheet_name="DC Final")

# --- Bersihkan dan Standarisasi Kolom ---
df_dc.columns = df_dc.columns.str.strip().str.lower().str.replace(" ", "_")

# --- Ambil Kolom Penting ---
df_node = df_dc[[
    'dc_id',           # node_id
    'type',            # node_type
    'area',            # lokasi spesifik node
    'distributor_area',# regional / cakupan
    'latitude',
    'longitude',
    'sent_from'
]].dropna(subset=['dc_id', 'latitude', 'longitude'])

# --- Rename agar sesuai format standar node ---
df_node = df_node.rename(columns={
    'dc_id': 'node_id',
    'type': 'node_type',
    'area': 'location_name',
    'distributor_area': 'region'
})


# --- Pastikan koordinat dalam format float ---
df_node['latitude'] = df_node['latitude'].astype(str).str.replace(',', '.').astype(float)
df_node['longitude'] = df_node['longitude'].astype(str).str.replace(',', '.').astype(float)

# --- (Opsional) Drop duplikat ---
df_node = df_node.drop_duplicates(subset='node_id')

# --- Lihat hasil ---
print(df_node.head())


# Koordinat umum Karawang (bisa disesuaikan)
karawang_lat = -6.305384
karawang_lon = 107.296913

# Tambahkan SDC ke df_node
df_node = pd.concat([
    df_node,
    pd.DataFrame([{
        'node_id': 'SDC',
        'node_type': 'Pabrik',
        'location_name': 'Karawang',
        'region': 'Jawa Barat',
        'latitude': karawang_lat,
        'longitude': karawang_lon,
        'sent_from': None
    }])
], ignore_index=True)




df_edge = df_node[df_node['sent_from'].notna()].copy()

# Buat kolom edge_from dan edge_to
df_edge['edge_from'] = df_edge['sent_from']
df_edge['edge_to'] = df_edge['location_name']

# Sekalian ambil ID node yang sesuai
df_edge = df_edge.merge(df_node[['location_name', 'node_id']], how='left', left_on='edge_from', right_on='location_name', suffixes=('', '_from'))
df_edge = df_edge.merge(df_node[['location_name', 'node_id']], how='left', left_on='edge_to', right_on='location_name', suffixes=('', '_to'))

# Bersihin kolom
df_edges_clean = df_edge[[
    'node_id_from', 'node_id_to'
]].rename(columns={
    'node_id_from': 'from_node',
    'node_id_to': 'to_node'
})


import networkx as nx

# Inisialisasi graf terarah
G = nx.DiGraph()

# Tambahkan node
for _, row in df_node.iterrows():
    G.add_node(row['node_id'], 
               location=row['location_name'],
               type=row['node_type'],
               latitude=row['latitude'],
               longitude=row['longitude'])

# Tambahkan edge dari df_edges_clean
for _, row in df_edges_clean.iterrows():
    G.add_edge(row['from_node'], row['to_node'])

G.add_node(
    'SDC',
    label='SDC',
    type='Pabrik',
    pos=(karawang_lon, karawang_lat)
)



import matplotlib.pyplot as plt

plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=42)

nx.draw(G, pos, with_labels=True, node_color='lightgreen', node_size=800, arrows=True)
nx.draw_networkx_labels(G, pos, font_size=8)

plt.title("Graf Distribusi Internal M&E (SDC → Depo)", fontsize=14)
plt.tight_layout()
plt.show()


# Buat dict posisi berdasarkan lat-long
pos_geo = {
    row['node_id']: (row['longitude'], row['latitude'])  # format: (x, y) = (lon, lat)
    for _, row in df_node.iterrows()
}


import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# --- STEP 1: Load Dataset ---
xls = pd.ExcelFile("dataset/1742574481558_Dataset-ME-2025.xlsx")
df_dc = pd.read_excel(xls, sheet_name="DC Final")

# --- STEP 2: Preprocessing df_node (semua DC) ---
df_dc.columns = df_dc.columns.str.strip().str.lower().str.replace(" ", "_")

df_node = df_dc[[
    'dc_id', 'type', 'area', 'distributor_area', 'latitude', 'longitude', 'sent_from'
]].dropna(subset=['dc_id', 'latitude', 'longitude'])

df_node = df_node.rename(columns={
    'dc_id': 'node_id',
    'type': 'node_type',
    'area': 'location_name',
    'distributor_area': 'region'
})

# Pastikan latitude & longitude numerik
df_node['latitude'] = df_node['latitude'].astype(str).str.replace(',', '.').astype(float)
df_node['longitude'] = df_node['longitude'].astype(str).str.replace(',', '.').astype(float)

# --- STEP 3: Bangun Graph G ---
G = nx.DiGraph()

# Tambah node
for _, row in df_node.iterrows():
    G.add_node(
        row['node_id'],
        label=row['node_id'],
        type=row['node_type'],
        pos=(row['longitude'], row['latitude'])
    )

# --- Tambahkan node SDC Karawang secara manual ---
karawang_lat = -6.305384
karawang_lon = 107.296913

G.add_node(
    'SDC',
    label='SDC',
    type='Pabrik',
    pos=(karawang_lon, karawang_lat)
)

# --- STEP 4: Buat Dataframe Edge dari sent_from ---
# Map lokasi asal (sent_from) → node_id
location_to_node = dict(zip(df_node['location_name'], df_node['node_id']))

df_edges = df_node[df_node['sent_from'].notna()][['node_id', 'sent_from']].copy()
df_edges = df_edges.rename(columns={'node_id': 'to_node', 'sent_from': 'from_node'})
df_edges['from_node'] = df_edges['from_node'].map(location_to_node)

# Drop baris yang mapping-nya gagal
df_edges = df_edges.dropna(subset=['from_node'])

# Tambah edge ke graf
for _, row in df_edges.iterrows():
    G.add_edge(row['from_node'], row['to_node'])

# Tambahkan edge dari Karawang ke node yang sent_from-nya 'SDC'
karawang_children = df_node[df_node['sent_from'] == 'SDC']['node_id'].tolist()

for to_node in karawang_children:
    G.add_edge('SDC', to_node)


# --- STEP 5: Gambar Peta Jaringan Distribusi ---
pos_geo = {node: data['pos'] for node, data in G.nodes(data=True)}

plt.figure(figsize=(15, 12))

# Gambar node
nx.draw_networkx_nodes(
    G, pos_geo, 
    node_color='skyblue', 
    node_size=500, 
    alpha=0.8
)

# Gambar edge (panah antar DC)
nx.draw_networkx_edges(
    G, pos_geo, 
    edge_color='gray', 
    arrows=True,
    width=1.5
)

# Tambahkan label node
labels = {node: G.nodes[node]['label'] for node in G.nodes}
nx.draw_networkx_labels(
    G, pos_geo, labels,
    font_size=8
)

plt.title("Peta Jaringan Distribusi M&E Berdasarkan Lokasi Geografis", fontsize=14)
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True)
plt.axis('equal')  # supaya bentuk geografis tidak melebar
plt.tight_layout()
plt.show()


import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import networkx as nx

# Ambil posisi node
pos_geo = {node: (data['pos'][0], data['pos'][1]) for node, data in G.nodes(data=True)}  # (lon, lat)

# Setup peta dengan Cartopy
fig = plt.figure(figsize=(14, 12))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([95, 141, -11, 6])  # Indonesia bbox: [lon_min, lon_max, lat_min, lat_max]

# Tambah fitur geografi
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN)
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAKES, alpha=0.5)
ax.add_feature(cfeature.RIVERS)

# Gambar edges
for u, v in G.edges():
    x_vals = [pos_geo[u][0], pos_geo[v][0]]
    y_vals = [pos_geo[u][1], pos_geo[v][1]]
    ax.plot(x_vals, y_vals, color='gray', linewidth=1.2, alpha=0.7, transform=ccrs.Geodetic())

# Gambar nodes
for node, (lon, lat) in pos_geo.items():
    ax.plot(lon, lat, marker='o', color='dodgerblue', markersize=5, transform=ccrs.PlateCarree())
    ax.text(lon + 0.3, lat + 0.3, G.nodes[node]['label'], fontsize=7, transform=ccrs.PlateCarree())

# Judul dan label
plt.title("Peta Jaringan Distribusi M&E di Atas Peta Indonesia", fontsize=14)
plt.show()


# Tambah SDC (jika belum)
karawang_lat = -6.305384
karawang_lon = 107.296913

df_node = pd.concat([
    df_node,
    pd.DataFrame([{
        'node_id': 'SDC',
        'node_type': 'Pabrik',
        'location_name': 'Karawang',
        'region': 'Jawa Barat',
        'latitude': karawang_lat,
        'longitude': karawang_lon,
        'sent_from': None
    }])
], ignore_index=True)

df_node = df_node.drop_duplicates(subset='node_id', keep='last')



from geopy.distance import geodesic
import pandas as pd

# Ambil koordinat dan ID node
locations = list(zip(df_node['latitude'], df_node['longitude']))
node_ids = df_node['node_id'].tolist()

# Buat DataFrame kosong
distance_matrix = pd.DataFrame(index=node_ids, columns=node_ids)

# Hitung jarak (km) antar semua node
for i in range(len(locations)):
    for j in range(len(locations)):
        distance = geodesic(locations[i], locations[j]).km
        distance_matrix.iloc[i, j] = round(distance, 2)

# Tampilkan sebagian hasil
print("Distance matrix antar DC (termasuk SDC/Karawang):")
print(distance_matrix.head())


df_land = pd.read_excel(xls, sheet_name="Land Logistics")
df_land.columns = df_land.columns.str.strip().str.lower().str.replace(" ", "_")

df_land['fixed_cost'] = (
    df_land['fixed_cost'].astype(str)
    .str.replace('.', '', regex=False)
    .str.replace(',', '.', regex=False)
    .astype(float)
)

df_land_edges = df_land[[
    'dc_id', 'destination_(city)', 'type', 'volume', 'fixed_cost'
]].rename(columns={
    'dc_id': 'from_dc',
    'destination_(city)': 'to_area',
    'type': 'mode',
    'volume': 'volume_cbm',
    'fixed_cost': 'cost_idr'
})

df_land_edges.head()

df_ocean = pd.read_excel(
    xls, 
    sheet_name="Ocean Freight",
    dtype=str  # ⬅️ ini penting: baca semua kolom sebagai string!
)
print(df_ocean.columns.tolist())
df_ocean.head()



df_ocean['fixed_cost_clean'] = pd.to_numeric(df_ocean['Fixed Cost'], errors='coerce').fillna(0).round(0)
df_ocean.head()

df_ocean_clean = df_ocean[[
    'DC ID', 'Destination (City)', 'Type', 'Volume', 'fixed_cost_clean'
]].rename(columns={
    'DC ID': 'from_dc',
    'Destination (City)': 'to_area',
    'Type': 'mode',
    'Volume': 'volume_cbm',
    'fixed_cost_clean': 'cost_idr'
})

print(df_ocean_clean[['from_dc', 'to_area', 'mode', 'cost_idr']].sample(5))


df_edges = pd.concat([df_land_edges, df_ocean_clean], ignore_index=True)


print("Jumlah total rute:", len(df_edges))
print(df_edges.sample(5))  # contoh acak

# Optional: Simpan ke file
# df_edges.to_excel("all_edges_logistik.xlsx", index=False)


def classify_mode(mode_str):
    if pd.isna(mode_str):
        return 'Unknown'
    mode_str = str(mode_str).upper()
    if 'FT' in mode_str:
        return 'Ocean'
    return 'Land'

df_edges['mode_type'] = df_edges['mode'].apply(classify_mode)
df_edges.sample(5)





df_dc_edges_joined = df_node.merge(
    df_edges,
    left_on='node_id',
    right_on='from_dc',
    how='left'
)

df_summary_per_dc = (
    df_dc_edges_joined
    .groupby('node_id')[['cost_idr', 'volume_cbm']]
    .sum()
    .reset_index()
    .rename(columns={
        'cost_idr': 'total_rate_from_node',
        'volume_cbm': 'total_volume_from_node'
    })
)

mode_per_dc = (
    df_edges
    .groupby('from_dc')['mode']
    .agg(lambda x: ', '.join(sorted(set(x))))
    .reset_index()
    .rename(columns={'from_dc': 'node_id', 'mode': 'modes'})
)

# Gabungkan ke df_summary_per_dc
df_dc_summary_with_mode = df_summary_per_dc.merge(mode_per_dc, on='node_id', how='left')

# Gabungkan ke df_node (biar satu row per DC)
df_dc_final_summary = df_node.merge(df_dc_summary_with_mode, on='node_id', how='left')

# Lihat hasil untuk DC031
df_dc_final_summary[df_dc_final_summary['node_id'] == 'DC031']




print(df_edges.columns)


df_dc_final_summary.sample(10)

# Merge df_node dengan df_edges
df_dc_olCost = df_node.merge(
    df_edges,
    left_on='node_id',
    right_on='from_dc',
    how='left'
)

# Drop kolom 'from_dc' dan 'to_area' dari hasil merge
df_dc_olCost = df_dc_olCost.drop(columns=['from_dc', 'to_area'])

# Cek hasil
df_dc_olCost.sample(10)



# Ambil data dari sheet rute (misal: df_sdc_routing)
df_sdc_routing = df_dc_olCost.copy()

# Filter hanya node_type: Direct DC atau Direct CPU
df_sdc_direct = df_sdc_routing[df_sdc_routing['node_type'].isin(['Direct DC', 'Direct CPU'])].copy()

# Filter hanya rute dari SDC
df_sdc_direct = df_sdc_direct[df_sdc_direct['sent_from'].str.contains("SDC", case=False, na=False)]

# Cek hasil akhir
print(df_sdc_direct[['node_id', 'location_name', 'sent_from', 'mode', 'cost_idr']].head())


# Pisahkan edge berdasarkan mode_type
land_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('mode_type') == 'Land']
ocean_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('mode_type') == 'Ocean']
internal_edges = [(u, v) for u, v in G.edges if 'mode_type' not in G[u][v]]

plt.figure(figsize=(15, 12))
nx.draw_networkx_nodes(G, pos_geo, node_color='skyblue', node_size=500, alpha=0.8)

nx.draw_networkx_edges(G, pos_geo, edgelist=internal_edges, edge_color='gray', arrows=True, width=1.5)
nx.draw_networkx_edges(G, pos_geo, edgelist=land_edges, edge_color='green', arrows=True, width=2)
nx.draw_networkx_edges(G, pos_geo, edgelist=ocean_edges, edge_color='blue', style='dashed', arrows=True, width=2)

nx.draw_networkx_labels(G, pos_geo, labels={n: G.nodes[n]['label'] for n in G.nodes}, font_size=8)

plt.title("Jaringan Distribusi M&E (Internal + Land + Ocean)", fontsize=14)
plt.grid(True)
plt.axis('equal')
plt.tight_layout()
plt.show()


import pandas as pd
from geopy.distance import geodesic

# 1. Load data
file_path = "dataset/E2099100.xlsx"
df_middle = pd.read_excel(file_path, sheet_name="Middle Mile")

# 2. Convert kolom koordinat ke float
coord_cols = ['Origin Latitude', 'Longitude_x', 'Destination Latitude', 'Destination Longitude']
for col in coord_cols:
    df_middle[col] = pd.to_numeric(df_middle[col], errors='coerce')  # coerce biar error jadi NaN


df_middle.sample(10)

df_middle.info()

# 3. Drop baris yang koordinatnya tidak valid
df_middle_cleaned = df_middle.dropna(subset=coord_cols)

# 4. Hitung jarak
df_middle_cleaned['distance_km'] = df_middle_cleaned.apply(
    lambda row: geodesic(
        (row['Origin Latitude'], row['Longitude_x']),
        (row['Destination Latitude'], row['Destination Longitude'])
    ).km,
    axis=1
)
df_middle_cleaned['distance_km'] = df_middle_cleaned['distance_km'].round(2)

# 5. Lihat hasil
print(df_middle_cleaned[['Origin Area', 'Destination Area', 'distance_km']].sample(10))


df_middle_cleaned.head()

df_dc_olCost.head()

import pandas as pd

# Step 1: Buat mapping location_name → DC ID
location_to_dc_id = df_dc_olCost.set_index('location_name')['node_id'].to_dict()

# Step 2: Salin df_middle_cleaned biar tidak ubah yang asli
df_middle_edges = df_middle_cleaned.copy()

# Step 3: Mapping ke DC ID
df_middle_edges['origin_id'] = df_middle_edges['Origin Area'].map(location_to_dc_id)
df_middle_edges['destination_id'] = df_middle_edges['Destination Area'].map(location_to_dc_id)

# Step 4: Cek mapping yang gagal
missing_origin = df_middle_edges[df_middle_edges['origin_id'].isna()]
missing_dest = df_middle_edges[df_middle_edges['destination_id'].isna()]

print("🚨 Origin Area yang tidak ditemukan:")
print(missing_origin[['Origin Area']].drop_duplicates())

print("\n🚨 Destination Area yang tidak ditemukan:")
print(missing_dest[['Destination Area']].drop_duplicates())

# Step 5: Drop baris yang tidak berhasil mapping
df_middle_edges_cleaned = df_middle_edges.dropna(subset=['origin_id', 'destination_id']).copy()

# Step 6: Buat edge list final
df_middle_edge_list = df_middle_edges_cleaned[[
    'origin_id',
    'destination_id',
    'distance_km',
    'Volume (CS)'  # atau 'volume_cbm' tergantung kolom kamu
]].rename(columns={
    'distance_km': 'distance_km',
    'Volume (CS)': 'max_volume'
})

print("\n✅ Contoh edge list middle mile:")
print(df_middle_edge_list.sample(5))


import pandas as pd
import numpy as np

# --- Load ODS Cost ---
df_ods = pd.read_excel("dataset/1742574481558_Dataset-ME-2025.xlsx", sheet_name="ODS Cost")

df_ods = df_ods[[
    'Distributor Area', 'Area', 'Type',
    'CDD', 'CDE', 'GrandMax', 'Kijang', 'Driver', 'Staff',
    'CDD Cost', 'CDE Cost', 'GrandMax Cost', 'Kijang Cost', 'Driver Cost', 'Staff Cost', 'Rental', 'TOTAL COST'
]]
df_ods.info()
df_ods.head()



# --- Load T&W Cost ---
df_tw = pd.read_excel("dataset/1742574481558_Dataset-ME-2025.xlsx", sheet_name="T&W Cost")

columns_needed = ["Distributor Area", "Area", "Type", "Vehicle", "Trips/mth", "Total Cost"]
df_tw_cleaned = df_tw[columns_needed].copy()


print(df_tw_cleaned.head())

import pandas as pd
import numpy as np

# --- Step 1: Bersihkan kolom Total Cost jadi float ---
df_tw['Total Cost'] = (
    df_tw['Total Cost']
    .astype(str)
    .str.replace(r"[^\d.,]", "", regex=True)   # hilangkan semua selain angka, titik, koma
    .str.replace(".", "", regex=False)         # hilangkan titik (pemisah ribuan)
    .str.replace(",", ".", regex=False)        # ganti koma dengan titik (untuk desimal)
    .replace("", np.nan)
    .astype(float)
)

# --- Step 2: Agregasi total cost per area ---
df_tw_agg = (
    df_tw.groupby(['Distributor Area', 'Area', 'Type'])[['Total Cost']]
    .sum()
    .reset_index()
    .rename(columns={'Total Cost': 'TW_TotalCost'})
)

# --- Step 3: Gabungkan jenis kendaraan per area ---
df_vehicle_info = (
    df_tw.groupby(['Distributor Area', 'Area', 'Type'])['Vehicle']
    .apply(lambda x: ', '.join(sorted(set(x.dropna()))))  # hapus duplikat + NaN
    .reset_index()
    .rename(columns={'Vehicle': 'Vehicle_List'})
)

# --- Step 4: Gabungkan hasil cost + kendaraan ---
df_tw_final = pd.merge(
    df_tw_agg,
    df_vehicle_info,
    on=['Distributor Area', 'Area', 'Type'],
    how='left'
)

# --- Step 5: Gabungkan dengan ODS ---
df_final_cost = pd.merge(
    df_ods, 
    df_tw_final, 
    on=['Distributor Area', 'Area', 'Type'], 
    how='outer'
)

# --- Step 6: Hitung total biaya distribusi keseluruhan (ODS + TW) ---
df_final_cost['Total_Distribution_Cost'] = (
    df_final_cost['TOTAL COST'].fillna(0) +
    df_final_cost['TW_TotalCost'].fillna(0)
)

df_final_cost.head()

df_resources = pd.read_excel("dataset/1742574481558_Dataset-ME-2025.xlsx", sheet_name="Resources", skiprows=3)

# Rename
df_resources.columns = [
    "Region", "Branch",
    "CDD", "CDE", "GrandMax", "Kijang",
    "Unused1",
    "Driver", "Staff",
    "CDD Cost", "CDE Cost", "GrandMax Cost", "Kijang Cost", "Driver Cost", "Staff Cost",
    "CDD Total", "CDE Total", "GrandMax Total", "Kijang Total", "Driver Total",
    "Unused2",
    "Fleet Fixed Cost/Day", "Fleet Variable Cost/Day", "People Cost/Day",
    "Transport All In/Day", "Capacity"
]

# Drop kolom yang tidak dipakai
df_resources.drop(columns=["Unused1", "Unused2"], inplace=True)

# Pastikan kolom numerik jadi float
numeric_cols = df_resources.columns.difference(["Region", "Branch"])
df_resources[numeric_cols] = df_resources[numeric_cols].fillna(0).astype(float)

df_resources.head()


df_dc.head()

# 1. Buat salinan kolom yang akan dibandingkan
df_resources['Branch_lower'] = df_resources['Branch'].str.lower().str.strip()
df_dc['Area_lower'] = df_dc['area'].str.lower().str.strip()

# 2. Merge pakai versi lowercase
df_resources_joined = df_resources.merge(
    df_dc[['Area_lower', 'dc_id']],
    left_on='Branch_lower',
    right_on='Area_lower',
    how='left'
)

# 3. Drop kolom bantu kalau sudah tidak dipakai
df_resources_joined.drop(columns=['Branch_lower', 'Area_lower'], inplace=True)

# 4. Lihat hasil join
df_resources_joined.head()


df_resources_joined.head(10)

df_demand.head()



df_demand = pd.read_csv("dataset/demand_per_dc_no_capacity.csv")
df_demand.head()

import pandas as pd
import numpy as np

# Load data demand dan kapasitas
df_demand = pd.read_csv("dataset/demand_per_dc_no_capacity.csv")
df_capacity = df_resources_joined[["dc_id", "Capacity"]].copy()
df_capacity.columns = ["DC ID", "Capacity"]  # rename biar konsisten

# Gabungkan berdasarkan DC ID
df_turnover = df_demand.merge(df_capacity, on="DC ID", how="left")

# Drop baris yang tidak punya info kapasitas
df_turnover = df_turnover.dropna(subset=["Capacity"])

# Hitung turnover (jumlah kali perputaran gudang dalam sebulan)
df_turnover["Turnover Per Bulan"] = np.ceil(df_turnover["Total Demand (box)"] / df_turnover["Capacity"]).astype(int)

# Flag Over Capacity
df_turnover["Over Capacity"] = df_turnover["Total Demand (box)"] > df_turnover["Capacity"]

# Output hasil
print(df_turnover[["DC ID", "Total Demand (box)", "Capacity", "Turnover Per Bulan", "Over Capacity"]])


df_dc_demand = df_dc[['Area', 'DC ID', 'Distributor Area', 'Type','Sent From', 'Latitude', 'Longitude',
                      'Monthly Demand (Average FY2021) - Carton', 
                      'Max Demand - FY2021 - Carton']]

df_dc_demand['Monthly Demand (Average FY2021) - Carton'] = df_dc_demand['Monthly Demand (Average FY2021) - Carton'].round(0)
df_dc_demand['Max Demand - FY2021 - Carton'] = df_dc_demand['Max Demand - FY2021 - Carton'].round(0)


df_dc_demand.head()

df_edges.head()

df_dc_olCost.head()

df = df_dc_olCost.rename(columns={
    'location_name': 'to_node',
    'latitude': 'to_latitude',
    'longitude': 'to_longitude',
    'sent_from': 'from_node'
})


df.head()

df_pos = df_node[['location_name', 'latitude', 'longitude']]
df_pos = df_pos.rename(columns={
    'location_name': 'from_node',
    'latitude': 'from_latitude',
    'longitude': 'from_longitude'
})

df_pos.head()


df_manual_coords = pd.DataFrame([
    {'from_node': 'SDC', 'from_latitude': -6.305384, 'from_longitude': 107.296913},
    {'from_node': 'SDC (CPU)', 'from_latitude': -6.305384, 'from_longitude': 107.296913},
    {'from_node': 'Palu ', 'from_latitude': -0.8917, 'from_longitude': 119.8707},
    {'from_node': 'Surabaya', 'from_latitude': -7.2504, 'from_longitude': 112.7688}
    ])

df_pos = pd.concat([df_pos, df_manual_coords], ignore_index=True)
df = df.merge(df_pos, on='from_node', how='left')


# Merge untuk tambahkan posisi asal
df.head()

df.sample(5)

df.info()

print('node_type' in df.columns)
print(df['node_type'].unique())



import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.patches as mpatches

# --- STEP 1: Siapkan Graph dan Posisi ---
G = nx.DiGraph()

# Buat mapping node_type dari node_id
node_type_dict = dict(zip(df['to_node'], df['node_type']))

# Gabungkan node asal dan tujuan
nodes = pd.concat([
    df[['from_node', 'from_latitude', 'from_longitude']].rename(
        columns={'from_node': 'node', 'from_latitude': 'lat', 'from_longitude': 'lon'}),
    df[['to_node', 'to_latitude', 'to_longitude']].rename(
        columns={'to_node': 'node', 'to_latitude': 'lat', 'to_longitude': 'lon'})
]).dropna(subset=['node']).drop_duplicates(subset='node')

# Tambahkan kolom node_type ke DataFrame nodes berdasarkan mapping
nodes['node_type'] = nodes['node'].map(node_type_dict)

# Mapping warna node berdasarkan jenisnya
node_type_colors = {
    'Pabrik': 'red',
    'Indirect DC': 'orange',
    'Direct DC': 'purple',
    'Direct CPU': 'blue',
    'Depo': 'green'
}

# Tambahkan node ke graf beserta pos dan type
for _, row in nodes.iterrows():
    tipe = row['node_type'] if pd.notna(row['node_type']) else 'Unknown'
    G.add_node(row['node'], pos=(row['lon'], row['lat']), node_type=tipe)

# --- STEP 2: Tambahkan Edge berdasarkan mode_type ---
for _, row in df.dropna(subset=['from_node', 'to_node']).iterrows():
    mode = str(row['mode_type']).lower() if pd.notna(row['mode_type']) else 'unknown'

    if mode == 'ocean':
        color = 'green'
    elif mode == 'land':
        color = 'blue'
    else:
        color = 'black'

    G.add_edge(row['from_node'], row['to_node'], color=color, mode=mode)

# --- STEP 3: Visualisasi ---
pos = nx.get_node_attributes(G, 'pos')
edge_colors = [G[u][v]['color'] for u, v in G.edges()]
node_types = nx.get_node_attributes(G, 'node_type')
node_colors = [node_type_colors.get(node_types.get(n, 'Unknown'), 'gray') for n in G.nodes()]

plt.figure(figsize=(12, 10))

# Gambar node berwarna
nx.draw_networkx_nodes(G, pos, node_size=600, node_color=node_colors, alpha=0.9)

# Gambar edge
nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=2)

# Gambar label node
nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

# --- Legenda Warna Edge ---
legend_edges = [
    mpatches.Patch(color='blue', label='Land'),
    mpatches.Patch(color='green', label='Ocean'),
    mpatches.Patch(color='black', label='Unknown Mode')
]

# --- Legenda Warna Node ---
legend_nodes = [
    mpatches.Patch(color='red', label='Pabrik'),
    mpatches.Patch(color='orange', label='Indirect DC'),
    mpatches.Patch(color='purple', label='Direct DC'),
    mpatches.Patch(color='blue', label='Direct CPU'),
    mpatches.Patch(color='green', label='Depo'),
    mpatches.Patch(color='gray', label='Unknown Type')
]

plt.legend(handles=legend_edges + legend_nodes, loc='upper right', fontsize=9)

plt.title("Peta Jaringan Distribusi: Node Type & Mode Transportasi", fontsize=14)
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True)
plt.axis('equal')
plt.tight_layout()
plt.show()


missing_coords = df[
    df[['from_latitude', 'from_longitude', 'to_latitude', 'to_longitude']].isnull().any(axis=1)
]

print("Baris dengan koordinat tidak lengkap:")
print(missing_coords[['from_node', 'to_node', 'from_latitude', 'from_longitude', 'to_latitude', 'to_longitude']])


df_clean = df.dropna(subset=['from_latitude', 'from_longitude', 'to_latitude', 'to_longitude']).copy()

from geopy.distance import geodesic

df_clean['distance_km'] = df_clean.apply(lambda row:
    geodesic((row['from_latitude'], row['from_longitude']),
             (row['to_latitude'], row['to_longitude'])).km,
    axis=1
)

df_clean['distance_km'] = df_clean['distance_km'].round(2)


df_clean.head()

df_model = df_clean[[
    'from_node', 'to_node', 'mode', 'mode_type', 'volume_cbm', 'distance_km', 'cost_idr'
]].dropna()


df_model.columns



df_model.sample(10)

df_kendaraan_info = pd.DataFrame({
    'type': ['CDD', 'CDE', 'GrandMax', 'Kijang', 'Motorbike'],
    'kapasitas_cbm': [280, 200, 120, 80, 5],
    'petrol_per_100km': [4, 7, 8, 10, 15]
})


df_resources.columns

# --- STEP 2: Ambil dari df_resources ---
vehicle_cols = ['CDD', 'CDE', 'GrandMax', 'Kijang']
df_vehicle = df_resources[['Branch'] + vehicle_cols].copy()

# Pastikan semua kolom kendaraan numerik
for col in vehicle_cols:
    df_vehicle[col] = pd.to_numeric(df_vehicle[col], errors='coerce').fillna(0)

# --- STEP 3: Long Format ---
df_long = df_vehicle.melt(id_vars='Branch', var_name='type', value_name='jumlah_unit')
df_long = df_long[df_long['jumlah_unit'] > 0]

# Gabung dengan info kapasitas & BBM
df_long = df_long.merge(df_kendaraan_info, on='type', how='left')

# Hitung total kapasitas dan konsumsi BBM
df_long['total_kapasitas'] = df_long['jumlah_unit'] * df_long['kapasitas_cbm']
df_long['total_petrol'] = df_long['jumlah_unit'] * df_long['petrol_per_100km']

# --- STEP 4: Agregasi per Branch ---
df_summary = df_long.groupby('Branch').agg({
    'jumlah_unit': 'sum',
    'total_kapasitas': 'sum',
    'total_petrol': 'sum'
}).reset_index()

df_summary = df_summary.rename(columns={
    'jumlah_unit': 'origin_total_vehicle',
    'total_kapasitas': 'origin_total_capacity_cbm',
    'total_petrol': 'origin_total_petrol_per_100km'
})

df_summary['origin_avg_petrol_per_100km'] = (
    df_summary['origin_total_petrol_per_100km'] / df_summary['origin_total_vehicle']
).round(2)

# --- STEP 5: One-hot ketersediaan kendaraan ---
df_availability = df_vehicle.copy()
for col in vehicle_cols:
    df_availability[col] = (df_availability[col] > 0).astype(int)

df_availability = df_availability.rename(columns={
    'CDD': 'CDD_available',
    'CDE': 'CDE_available',
    'GrandMax': 'GrandMax_available',
    'Kijang': 'Kijang_available'
})

# --- FINAL OUTPUT ---
print("✅ df_summary:")
print(df_summary.head())

print("\n✅ df_availability:")
print(df_availability.head())

df_middle_cleaned.head()

df_final = df_middle_cleaned.merge(
    df_summary, left_on='origin_area', right_on='Branch', how='left'
).drop(columns='Branch')

df_final = df_final.merge(
    df_availability, left_on='origin_area', right_on='Branch', how='left'
).drop(columns='Branch')


newxls = "dataset/Dataset Bersih Lengkap.xlsx"
df_customer = pd.read_excel(newxls, sheet_name="Customer Final")

df_customer.head()
# Ambil kolom-kolom yang diperlukan dari df_customer
df_customer_filtered = df_customer[[
    'Customer ID',
    'Sub-District Area',
    'Latitude',
    'Longitude',
    'Avg Monthly Demand (box)'
]].copy()
df_customer_filtered.head()


import pandas as pd

# 1. Baca sheet Resources dengan header di baris ke-3
df_region = pd.read_excel(file_path, sheet_name='Resources', header=3, usecols=['REGION', 'BRANCH'])

# 2. Bersihkan dan lowercase
df_region['BRANCH'] = df_region['BRANCH'].str.strip().str.lower()
df_region['REGION'] = df_region['REGION'].str.strip()

# Ganti 'bali' menjadi 'denpasar' di df_region
df_region['BRANCH'] = df_region['BRANCH'].replace('bali', 'denpasar')

# 3. Standardisasi df_dc_demand
df_dc_demand['Area'] = df_dc_demand['Area'].str.strip().str.lower()

# 4. Join berdasarkan Area dan Branch
df_dc_enriched = df_dc_demand.merge(
    df_region.drop_duplicates(),
    how='left',
    left_on='Area',
    right_on='BRANCH'
)

# 5. Drop kolom BRANCH (optional)
df_dc_enriched.drop(columns=['BRANCH'], inplace=True)

# 6. Tangani Area yang REGION-nya masih NaN → isi "Unknown"
# 6. Tangani NaN di REGION:
# Jika Type == 'Depo', isi REGION = 'Depo'
# Jika tidak, isi REGION = 'Unknown'
df_dc_enriched['REGION'] = df_dc_enriched.apply(
    lambda row: 'Depo' if pd.isna(row['REGION']) and row['Type'].lower() == 'depo' else (
        'Unknown' if pd.isna(row['REGION']) else row['REGION']
    ),
    axis=1
)

# 7. Contoh hasil
print(df_dc_enriched[['DC ID', 'Area', 'REGION']].sample(10))


df_dc_enriched.head()

df_dc_enriched['REGION'].value_counts().reset_index().rename(
    columns={'index': 'REGION', 'REGION': 'Jumlah DC'}
)


import pandas as pd
from geopy.distance import geodesic

# PARAMETER
MAX_DELIVERY_DISTANCE = 100000  # km, batas maksimal jarak realistis

# Step 1: Filter DC (tanpa Pabrik / SDC)
df_dc_deliver = df_dc_enriched[df_dc_enriched['Type'] != 'Pabrik'].copy()
df_dc_deliver['Remaining Capacity'] = df_dc_deliver['Max Demand - FY2021 - Carton'].copy()

# Step 2: Sampling customer (bisa 117k++ nanti kalau sudah stabil)
# df_customer_sample = df_customer.sample(n=50000, random_state=100)

# Step 3: Alokasi
allocation_result = []

for idx, cust in df_customer_filtered.iterrows():
    cust_coord = (cust['Latitude'], cust['Longitude'])
    cust_demand = cust['Avg Monthly Demand (box)']
    
    # Hitung jarak ke semua DC
    dc_distances = []
    for _, dc in df_dc_deliver.iterrows():
        dc_coord = (dc['Latitude'], dc['Longitude'])
        dist = geodesic(cust_coord, dc_coord).km
        dc_distances.append((dc['DC ID'], dist, dc['Type']))
    
    # Urutkan berdasarkan Jarak dan Preferensi Type
    dc_distances.sort(key=lambda x: (x[1], {'Direct DC': 0, 'Direct CPU': 0, 'Indirect DC': 1, 'Indirect CPU': 1, 'Depo': 2}.get(x[2], 3)))
    
    # Alokasikan ke DC yang kapasitasnya cukup dan jaraknya wajar
    assigned = False
    for dc_id, dist, dc_type in dc_distances:
        if dist > MAX_DELIVERY_DISTANCE:
            continue  # Skip terlalu jauh
        
        dc_index = df_dc_deliver[df_dc_deliver['DC ID'] == dc_id].index[0]
        remaining = df_dc_deliver.at[dc_index, 'Remaining Capacity']
        
        if remaining >= cust_demand:
            df_dc_deliver.at[dc_index, 'Remaining Capacity'] -= cust_demand
            allocation_result.append({
                'Customer ID': cust['Customer ID'],
                'Latitude': cust['Latitude'],
                'Longitude': cust['Longitude'],
                'Nearest DC ID': dc_id,
                'Distance to DC (km)': round(dist, 2),
                'Avg Monthly Demand (box)': cust_demand
            })
            assigned = True
            break

    if not assigned:
        allocation_result.append({
            'Customer ID': cust['Customer ID'],
            'Latitude': cust['Latitude'],
            'Longitude': cust['Longitude'],
            'Nearest DC ID': 'UNASSIGNED',
            'Distance to DC (km)': None,
            'Avg Monthly Demand (box)': cust_demand
        })

# Step 4: Buat DataFrame hasil
df_customer_assigned = pd.DataFrame(allocation_result)

# Step 5: Total demand per DC
df_demand_per_dc = df_customer_assigned[df_customer_assigned['Nearest DC ID'] != 'UNASSIGNED'] \
    .groupby('Nearest DC ID')['Avg Monthly Demand (box)'].sum().reset_index()
df_demand_per_dc.columns = ['DC ID', 'Total Demand (box)']

# Step 6: Save ke CSV
df_demand_per_dc.to_csv('demand_per_dc.csv', index=False)
df_customer_assigned.to_csv('customer_assigned_to_dc.csv', index=False)

# Step 7: Pemetaan Region/Area
df_customer_assigned_with_area = df_customer_assigned.merge(
    df_dc_deliver[['DC ID', 'Distributor Area', 'REGION']],
    left_on='Nearest DC ID',
    right_on='DC ID',
    how='left'
)

df_demand_per_area = df_customer_assigned_with_area[df_customer_assigned_with_area['Nearest DC ID'] != 'UNASSIGNED'] \
    .groupby('REGION')['Avg Monthly Demand (box)'].sum().reset_index()

# Output akhir
print(df_demand_per_area)
print("✅ Hasil demand per DC disimpan ke 'demand_per_dc.csv'")
print("✅ Pemetaan customer disimpan ke 'customer_assigned_to_dc.csv'")


print(df_dc_deliver['REGION'].unique())


df_dc_demand['Area'] = df_dc_demand['Area'].str.strip().str.lower()
df_dc_demand['Area'] = df_dc_demand['Area'].replace('denpasar', 'bali')  # mapping Denpasar jadi Bali


import pandas as pd
from geopy.distance import geodesic
from collections import defaultdict

# PARAMETER
MAX_DELIVERY_DISTANCE = 100000  # optional, tetap disimpan

# Step 1: Filter DC (tanpa Pabrik / SDC)
df_dc_deliver = df_dc_enriched[df_dc_enriched['Type'] != 'Pabrik'].copy()
df_dc_deliver['Remaining Capacity'] = pd.to_numeric(df_dc_deliver['Max Demand - FY2021 - Carton'], errors='coerce').fillna(0)

# Step 2: Customer
# df_customer_sample = df_customer.copy()
# df_customer_sample = df_customer_filtered.sample(n=3000, random_state=100)

# Step 3: Alokasi + log overcapacity
allocation_result = []
over_capacity_log = defaultdict(float)

for idx, cust in df_customer_filtered.iterrows():
    cust_coord = (cust['Latitude'], cust['Longitude'])
    cust_demand = cust['Avg Monthly Demand (box)']
    
    # Hitung jarak ke semua DC
    dc_distances = []
    for _, dc in df_dc_deliver.iterrows():
        dc_coord = (dc['Latitude'], dc['Longitude'])
        dist = geodesic(cust_coord, dc_coord).km
        dc_distances.append((dc['DC ID'], dist, dc['Type']))
    
    # Urutkan berdasarkan jarak & preferensi tipe
    dc_distances.sort(key=lambda x: (x[1], {'Direct DC': 0, 'Direct CPU': 0, 'Indirect DC': 1, 'Indirect CPU': 1, 'Depo': 2}.get(x[2], 3)))
    
    assigned = False
    for dc_id, dist, dc_type in dc_distances:
        dc_index = df_dc_deliver[df_dc_deliver['DC ID'] == dc_id].index
        if len(dc_index) == 0:
            continue
        dc_index = dc_index[0]
        remaining = df_dc_deliver.at[dc_index, 'Remaining Capacity']
        
        if remaining >= cust_demand:
            # Cukup kapasitas → alokasi normal
            df_dc_deliver.at[dc_index, 'Remaining Capacity'] -= cust_demand
            allocation_result.append({
                'Customer ID': cust['Customer ID'],
                'Latitude': cust['Latitude'],
                'Longitude': cust['Longitude'],
                'Nearest DC ID': dc_id,
                'Distance to DC (km)': round(dist, 2),
                'Avg Monthly Demand (box)': cust_demand,
                'Over Capacity': False
            })
            assigned = True
            break

    if not assigned:
        # Tetap paksa assign ke DC terdekat (meskipun over capacity)
        dc_id, dist, dc_type = dc_distances[0]
        dc_index = df_dc_deliver[df_dc_deliver['DC ID'] == dc_id].index[0]
        df_dc_deliver.at[dc_index, 'Remaining Capacity'] -= cust_demand
        over_capacity_log[dc_id] += cust_demand

        allocation_result.append({
            'Customer ID': cust['Customer ID'],
            'Latitude': cust['Latitude'],
            'Longitude': cust['Longitude'],
            'Nearest DC ID': dc_id,
            'Distance to DC (km)': round(dist, 2),
            'Avg Monthly Demand (box)': cust_demand,
            'Over Capacity': True
        })

# Step 4: Buat DataFrame hasil alokasi
df_customer_assigned = pd.DataFrame(allocation_result)

# Step 5: Buat DataFrame log DC over capacity
df_over_capacity_log = pd.DataFrame([
    {'DC ID': dc_id, 'Total Over Capacity (box)': total}
    for dc_id, total in over_capacity_log.items()
])

# Output hasil
df_customer_assigned_sample = df_customer_assigned.sample(10)
df_over_capacity_log_sample = df_over_capacity_log.sample(min(10, len(df_over_capacity_log)))

print("📦 Contoh hasil alokasi customer:")
print(df_customer_assigned_sample)

print("\n⚠️ Contoh log DC over capacity:")
print(df_over_capacity_log_sample)

# Save hasil customer assignment ke CSV
df_customer_assigned.to_csv('customer_assigned_to_dc.csv', index=False)
print("✅ File 'customer_assigned_to_dc.csv' berhasil disimpan.")

# Step 7: Pemetaan Region/Area
df_customer_assigned_with_area = df_customer_assigned.merge(
    df_dc_deliver[['DC ID', 'Distributor Area', 'REGION']],
    left_on='Nearest DC ID',
    right_on='DC ID',
    how='left'
)

df_demand_per_area = df_customer_assigned_with_area[df_customer_assigned_with_area['Nearest DC ID'] != 'UNASSIGNED'] \
    .groupby('REGION')['Avg Monthly Demand (box)'].sum().reset_index()

# Output akhir
print(df_demand_per_area)


print(df_dc_deliver[df_dc_deliver['REGION'] == 'BNT'][['DC ID', 'Area', 'Remaining Capacity']])


import folium
from folium.plugins import MarkerCluster

# Buat map awal, posisinya di tengah-tengah Indonesia
m = folium.Map(location=[-2.5, 118], zoom_start=5)

# --- 1. Tambahkan marker untuk DC ---
for idx, row in df_dc_deliver.iterrows():
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=8,
        color='blue',
        fill=True,
        fill_opacity=0.7,
        popup=f"DC: {row['DC ID']}<br>Area: {row['Area']}",
    ).add_to(m)

# --- 2. Tambahkan marker untuk customer (pakai cluster biar ga rame) ---
customer_cluster = MarkerCluster(name="Customers").add_to(m)

for idx, row in df_customer_filtered.iterrows():
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=3,
        color='red',
        fill=True,
        fill_opacity=0.5,
        popup=f"Customer ID: {row['Customer ID']}",
    ).add_to(customer_cluster)
 
# Simpan map-nya
m.save('map_dc_customer.html')
print("✅ Map berhasil disimpan ke 'map_dc_customer.html'")


df_edges.head()

df_oceanland = df_edges.copy()

# Rename untuk konsistensi
df_oceanland = df_oceanland.rename(columns={
    'from_dc': 'target_node',
    'mode': 'moda',
    'cost_idr': 'cost_per_trip',
    'volume_cbm': 'volume_per_trip'
})

# Tambahkan kolom source_node sebagai SDC
df_oceanland['source_node'] = 'SDC'  # atau nama ID pabrikmu


# Ambil kolom penting untuk df_edges_final
df_oceanland = df_oceanland[['source_node', 'target_node', 'moda', 'cost_per_trip', 'volume_per_trip']]

# Rename untuk konsistensi
df_oceanland = df_oceanland.rename(columns={
    'from_dc': 'target_node',
    'moda': 'mode_type',
    'cost_idr': 'cost_per_trip',
    'volume_cbm': 'volume_per_trip'
})

df_oceanland.head()

df_middle_edge_list.head()

df_resources_joined.head()

import pandas as pd

# Contoh: load data dari Excel (ubah sesuai kebutuhanmu)
df_stp = pd.read_excel(xls, sheet_name="STP Performance")

# Jika sudah berupa DataFrame df_stp:
def parse_order_schedule(order_schedule):
    # Bersihkan spasi dan pisah berdasarkan koma atau strip
    days = []
    if pd.isna(order_schedule):
        return []
    parts = order_schedule.replace('-', ',').replace(' ', '').split(',')
    for p in parts:
        if p != '':
            days.append(p.strip().capitalize())  # capitalized (Mon, Tue, ...)
    return days

def transform_stp_to_order_constraints(df_stp):
    # Rename kolom agar lebih seragam
    df = df_stp.rename(columns={
        'Ship to Point': 'target_node',
        'Current Lead Time\nSO/LO': 'lead_time_days',
        'Order \nSchedule': 'order_schedule',
        'Order/Wk': 'order_wk'
    })

    # Parse kolom hari kirim
    df['valid_days'] = df['order_schedule'].apply(parse_order_schedule)

    # Ambil kolom penting
    df_out = df[['target_node', 'order_wk', 'valid_days', 'lead_time_days']].copy()

    # Normalisasi node name (opsional, misal: uppercase)
    df_out['target_node'] = df_out['target_node'].str.upper().str.strip()

    return df_out

# Contoh pemakaian:
df_order_constraints = transform_stp_to_order_constraints(df_stp)


df_order_constraints.head()

df_resources_joined

vehicle_modes = ['CDD', 'CDE', 'GrandMax', 'Kijang']
mode_param = {
    'CDD': 70,
    'CDE': 100,
    'GrandMax': 120,
    'Kijang': 50
}

# Simulasi data
# df_resource_joined = df_resources.copy()

# Bersihkan dan bentuk long format dari df_resource_joined
resource_edges_v2 = []
for _, row in df_resources_joined.iterrows():
    origin = row['dc_id']
    if pd.isna(origin):
        continue
    for mode in vehicle_modes:
        jumlah = row[mode]
        cost = row[f'{mode} Cost']
        if pd.notna(jumlah) and pd.notna(cost) and jumlah > 0 and cost > 0:
            resource_edges_v2.append({
                'source_node': origin,
                'mode_type': mode,
                'cost_per_trip': cost,
                'volume_per_trip': mode_param[mode]
            })

df_mode_per_dc_v2 = pd.DataFrame(resource_edges_v2)

# Gabungkan ke df_middle_edge_list
df_middle_expanded_v2 = df_middle_edge_list.merge(
    df_mode_per_dc_v2,
    left_on='origin_id',
    right_on='source_node',
    how='left'
)

# Filter hanya kombinasi valid
df_middle_final_v2 = df_middle_expanded_v2.dropna(subset=['mode_type'])

# Ambil kolom final
df_middle_edges_final_v2 = df_middle_final_v2[['source_node', 'destination_id', 'mode_type', 'cost_per_trip', 'volume_per_trip']]
df_middle_edges_final_v2 = df_middle_edges_final_v2.rename(columns={'destination_id': 'target_node'})

df_middle_edges_final_v2.sample(20)

import tools

# Gabungkan df_oceanland (first mile) dengan df_middle_edges_final_v2 (middle mile)
df_edges_final = pd.concat([df_oceanland, df_middle_edges_final_v2], ignore_index=True)

# Tampilkan hasil
df_edges_final.info()

from ortools.sat.python import cp_model

# Inisialisasi model
model = cp_model.CpModel()

# Asumsikan df_edges_final sudah ada
# Ambil kombinasi unik (i, j, m)
edge_tuples = list(df_edges_final[['source_node', 'target_node', 'mode_type']].itertuples(index=False, name=None))

# Buat variabel keputusan x[i][j][m]
x = {}
for i, j, m in edge_tuples:
    x[i, j, m] = model.NewIntVar(0, 1000, f'x_{i}_{j}_{m}')


# Coba paksa konversi kolom volume_per_trip ke float (numerik) secara eksplisit
df_edges_final['volume_per_trip'] = pd.to_numeric(df_edges_final['volume_per_trip'], errors='coerce')

# Ulangi pembuatan dictionary volume_per_trip setelah dibersihkan
volume_per_trip = {
    (row['source_node'], row['target_node'], row['mode_type']): int(round(row['volume_per_trip']))
    for _, row in df_edges_final.iterrows()
    if pd.notna(row['volume_per_trip'])  # hanya jika bukan NaN
}

# Buat juga volume_cap_dict dari df_middle_edge_list
df_middle_edge_list['max_volume'] = pd.to_numeric(df_middle_edge_list['max_volume'], errors='coerce')

volume_cap_dict = {
    (row['origin_id'], row['destination_id']): int(round(row['max_volume']))
    for _, row in df_middle_edge_list.iterrows()
    if pd.notna(row['max_volume'])
}

# Tampilkan sebagian isi dict sebagai preview
preview_volume = dict(list(volume_per_trip.items())[:5])
preview_volume

from ortools.sat.python import cp_model

model = cp_model.CpModel()

# (Sebelumnya sudah bikin variabel x[i,j,m]...)

# Biaya distribusi (total_cost)
cost_terms = [
    x[i, j, m] * cost_per_trip.get((i, j, m), 0)
    for (i, j, m), var in x.items()
]
total_cost = sum(cost_terms)

# Penalti unmet demand (S1)
PENALTY_RATE = 1000
penalty_terms = []
unsatisfied = {}

for j, demand in demand_dict.items():
    sent = model.NewIntVar(0, int(demand), f"sent_{j}")
    model.Add(sent == sum(
        x[i, j2, m] * volume_per_trip.get((i, j2, m), 0)
        for (i, j2, m), var in x.items() if j2 == j
    ))
    unmet = model.NewIntVar(0, int(demand), f"unmet_{j}")
    model.Add(unmet == int(demand) - sent)
    penalty_terms.append(unmet * PENALTY_RATE)
    unsatisfied[j] = unmet

total_penalty = sum(penalty_terms)

# Objective akhir
model.Minimize(total_cost + total_penalty)


from ortools.sat.python import cp_model
model = cp_model.CpModel()

# Variabel keputusan:
x = {}
for i, j, m in df_edges_final[['source_node', 'target_node', 'mode_type']].itertuples(index=False, name=None):
    x[i, j, m] = model.NewIntVar(0, 1000, f"x_{i}_{j}_{m}")


# C1: Batas volume per rute
for (i, j, m), var in x.items():
    vol_per_trip = volume_per_trip.get((i, j, m))
    if vol_per_trip is None:
        continue

    if (i, j) in volume_cap_dict:
        max_volume = volume_cap_dict[(i, j)] * 24  # asumsi 24 hari operasi
        model.Add(var * vol_per_trip <= max_volume)
    else:
        model.Add(var * vol_per_trip <= 1_000_000)

    if (i, j) in volume_cap_dict:
        max_volume = volume_cap_dict[(i, j)] * 24
        print(f"C1: {i} → {j} mode {m} | volume/trip: {vol_per_trip} | batas: {max_volume}")
        model.Add(var * vol_per_trip <= max_volume)


df_resources_joined.head()

vehicle_modes = ['CDD', 'CDE', 'GrandMax', 'FUSO', 'Kijang']  # sesuaikan dengan sumber datamu
DAYS_IN_MONTH = 24  # asumsi

trip_limit = {}

for _, row in df_resources_joined.iterrows():
    dc = row['dc_id']
    if pd.isna(dc):
        continue
    for mode in vehicle_modes:
        jumlah_kendaraan = row.get(mode)
        if pd.notna(jumlah_kendaraan) and jumlah_kendaraan > 0:
            trip_limit[(dc, mode)] = int(jumlah_kendaraan * DAYS_IN_MONTH)

from collections import defaultdict

# Akumulasi semua trip per (origin, mode)
trip_vars = defaultdict(list)

for (i, j, m), var in x.items():
    trip_vars[(i, m)].append(var)

# Pasang constraint per (origin, mode)
for (i, m), vars_list in trip_vars.items():
    if (i, m) in trip_limit:
        model.Add(sum(vars_list) <= trip_limit[(i, m)])
        


solver = cp_model.CpSolver()
status = solver.Solve(model)


for (i, m), vars_list in trip_vars.items():
    total_trip = sum(solver.Value(v) for v in vars_list)
    limit = trip_limit.get((i, m), None)
    
    if limit is not None:
        print(f"Trip C2: {i}-{m} → used: {total_trip} | limit: {limit}")
        if total_trip > limit:
            print(f"🚨 C2 VIOLATION: {i}-{m} melebihi batas trip!")


order_limit = {
    row['target_node']: int(row['order_wk'] * 4)
    for _, row in df_order_constraints.iterrows()
    if pd.notna(row['order_wk'])
}

from collections import defaultdict

# Akumulasi semua trip dari SDC ke j
sdctrip_vars = defaultdict(list)

for (i, j, m), var in x.items():
    if i.startswith("SDC") or i == "SDC":
        sdctrip_vars[j].append(var)

# Pasang constraint: max trip ke j sesuai jadwal order/wk
for j, vars_list in sdctrip_vars.items():
    if j in order_limit:
        model.Add(sum(vars_list) <= order_limit[j])


solver = cp_model.CpSolver()
status = solver.Solve(model)
print("🧪 Verifikasi Constraint C3: Trip dari SDC ke DC\n" + "-"*50)

has_trip = False
for j, vars_list in sdctrip_vars.items():
    used = sum(solver.Value(v) for v in vars_list)
    limit = order_limit.get(j)

    if used > 0:
        has_trip = True
        if limit is not None:
            status = "✅ OK" if used <= limit else "🚨 VIOLATION"
            print(f"{status} | SDC → {j} | trip used: {used} / limit: {limit}")
        else:
            print(f"⚠️  SDC → {j} | trip: {used} | limit ❌ not set")

if not has_trip:
    print("⚠️ Tidak ada trip dari SDC ke node manapun pada solusi ini.")


demand_dict = {
    row['DC ID']: int(round(row['Total Demand (box)']))
    for _, row in df_demand.iterrows()
    if pd.notna(row['Total Demand (box)'])
}

from collections import defaultdict

# Akumulasi variabel per DC tujuan
incoming_vars = defaultdict(list)

for (i, j, m), var in x.items():
    vol = volume_per_trip.get((i, j, m))
    if vol:
        incoming_vars[j].append((var, vol))

# Pasang constraint: total volume ke j ≤ demand[j]
for j, varlist in incoming_vars.items():
    if j in demand_dict:
        expr = sum(var * vol for var, vol in varlist)
        model.Add(expr <= demand_dict[j])


for j, varlist in incoming_vars.items():
    total = sum(solver.Value(var) * vol for var, vol in varlist)
    print(f"📦 DC {j}: diterima {total} box | demand: {demand_dict.get(j, '❌')}")


print("🧪 Verifikasi Constraint C4: Volume Masuk ke DC Tujuan\n" + "-"*50)

for j, varlist in incoming_vars.items():
    total_volume = sum(solver.Value(var) * vol for var, vol in varlist)
    limit = demand_dict.get(j)

    if limit is not None:
        status = "✅ OK" if total_volume <= limit else "🚨 VIOLATION"
        print(f"{status} | DC {j} | volume: {total_volume} / limit: {limit}")


lead_time_dict = {
    row['target_node']: int(row['lead_time_days'])
    for _, row in df_order_constraints.iterrows()
    if pd.notna(row['lead_time_days'])
}

trip_max_middlemile = {}

for (i, j, m), var in x.items():
    if (i, j) in volume_cap_dict and j in lead_time_dict:
        lead_time = lead_time_dict[j]
        kendaraan_tersedia = trip_limit.get((i, m), 0)  # dari C2
        max_trip = (DAYS_IN_MONTH // (2 * lead_time)) * kendaraan_tersedia
        trip_max_middlemile[(i, j, m)] = max_trip


for (i, j, m), limit in trip_max_middlemile.items():
    model.Add(x[(i, j, m)] <= limit)


print("🧪 Verifikasi Constraint C5: Rotasi Kendaraan 2×Lead Time\n" + "-"*50)

for (i, j, m), limit in trip_max_middlemile.items():
    val = solver.Value(x[(i, j, m)])
    status = "✅ OK" if val <= limit else "🚨 VIOLATION"
    print(f"{status} | {i} → {j} via {m} | used: {val} / limit: {limit}")


valid_edges = set(
    zip(df_edges_final['source_node'], df_edges_final['target_node'])
)

valid_middle_edges = set(
    zip(df_middle_edge_list['origin_id'], df_middle_edge_list['destination_id'])
)

# Gabungkan semua rute valid (boleh first mile atau middle mile)
all_valid_routes = valid_edges.union(valid_middle_edges)


for (i, j, m), var in x.items():
    if (i, j) not in all_valid_routes:
        model.Add(var == 0)  # blokir penggunaan rute tak valid


print("🧪 Verifikasi Constraint C6: Rute Valid Sesuai Edge List\n" + "-"*50)

for (i, j, m), var in x.items():
    val = solver.Value(var)
    if val > 0 and (i, j) not in all_valid_routes:
        print(f"🚨 VIOLATION: {i} → {j} via {m} digunakan padahal bukan rute valid!")


capacity_dict = {
    row['dc_id']: int(round(row['Capacity']))
    for _, row in df_resources_joined.iterrows()
    if pd.notna(row['dc_id']) and pd.notna(row['Capacity'])
}

for j, varlist in incoming_vars.items():
    if j in capacity_dict:
        expr = sum(var * vol for var, vol in varlist)
        model.Add(expr <= capacity_dict[j])


print("🧪 Verifikasi Constraint C7: Kapasitas DC Tujuan\n" + "-"*50)

for j, varlist in incoming_vars.items():
    total_volume = sum(solver.Value(var) * vol for var, vol in varlist)
    limit = capacity_dict.get(j)

    if limit is not None:
        status = "✅ OK" if total_volume <= limit else "🚨 VIOLATION"
        print(f"{status} | DC {j} | volume masuk: {total_volume} / kapasitas: {limit}")


solver = cp_model.CpSolver()
status = solver.Solve(model)
if status == cp_model.OPTIMAL:
    print("✅ Solver menemukan solusi optimal.")
elif status == cp_model.FEASIBLE:
    print("✅ Solver menemukan solusi feasible (mungkin belum optimal).")
else:
    print("❌ Solver tidak menemukan solusi. Coba cek constraint terlalu ketat?")
has_delivery = False
for (i, j, m), var in x.items():
    val = solver.Value(var)
    if val > 0:
        print(f"🚚 {i} → {j} via {m} | trip = {val}")
        has_delivery = True

if not has_delivery:
    print("⚠️ Tidak ada trip aktif dalam solusi ini.")


for (i, j, m), var in x.items():
    if i == "SDC" and solver.Value(var) > 0:
        print(f"SDC → {j} via {m}: {solver.Value(var)} trip")


print(f"🧾 Total biaya akhir dari solver: Rp {solver.ObjectiveValue():,.0f}")


PENALTY_RATE = 1000  # 💰 penalti per box yang tidak dikirim

unsatisfied = {}
penalty_terms = []

for j, demand in demand_dict.items():
    # Hitung volume terkirim ke DC j
    sent = model.NewIntVar(0, int(demand), f"sent_{j}")
    terms = [
        x[i, j, m] * volume_per_trip.get((i, j, m), 0)
        for (i, j2, m), var in x.items() if j2 == j
    ]
    model.Add(sent == sum(terms))

    # Hitung unmet demand
    unmet = model.NewIntVar(0, int(demand), f"unmet_{j}")
    model.Add(unmet == int(demand) - sent)
    penalty_terms.append(unmet * PENALTY_RATE)

    unsatisfied[j] = unmet

# 💰 Tambahkan ke objective (gabung cost + penalti)
total_penalty = sum(penalty_terms)
model.Minimize(total_cost + total_penalty)


# jalanin model


solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 120  # misal limit waktu
status = solver.Solve(model)


for (i, j, m), var in x.items():
    trips = solver.Value(var)
    if trips > 0:
        cost = cost_per_trip.get((i, j, m), 0)
        vol = volume_per_trip.get((i, j, m), 0)
        print(f"{i} → {j} via {m} = {trips} trip | Cost: Rp {trips * cost:,} | Volume: {trips * vol}")


cost_per_trip = {
    (row['source_node'], row['target_node'], row['mode_type']): int(round(row['cost_per_trip']))
    for _, row in df_edges_final.iterrows()
    if pd.notna(row['cost_per_trip'])
}

total_cost_expr = sum(
    solver_model.NewIntVar(0, 1_000_000_000, f"cost_{i}_{j}_{m}")  # placeholder var
    if cost_per_trip.get((i, j, m)) is None else
    x[(i, j, m)] * cost_per_trip[(i, j, m)]
    for (i, j, m) in x
)


model.Minimize(total_cost_expr)

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    print("✅ Solusi optimal ditemukan.")
elif status == cp_model.FEASIBLE:
    print("✅ Solusi feasible ditemukan.")
else:
    print("❌ Tidak ada solusi.")


total_cost = sum(
    solver.Value(x[(i, j, m)]) * cost_per_trip[(i, j, m)]
    for (i, j, m) in x
    if (i, j, m) in cost_per_trip
)

print(f"💰 Total biaya distribusi: Rp {total_cost:,.0f}")


print("🚚 Trip Aktif dalam Solusi:\n" + "-"*50)

total_cost = 0
total_volume = 0

for (i, j, m), var in x.items():
    trips = solver.Value(var)
    if trips > 0:
        cost = cost_per_trip.get((i, j, m), 0)
        vol_per_trip = volume_per_trip.get((i, j, m), 0)

        subtotal = trips * cost
        volume_total = trips * vol_per_trip

        print(f"{i} → {j} via {m} | trip = {trips:3} | cost/trip = Rp {cost:,.0f} | total cost = Rp {subtotal:,.0f} | volume = {volume_total}")

        total_cost += subtotal
        total_volume += volume_total

print("-"*50)
print(f"💰 Total Biaya Distribusi: Rp {total_cost:,.0f}")
print(f"📦 Total Volume Dikirim: {total_volume:,} box")
