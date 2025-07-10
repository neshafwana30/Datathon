# --- 0. IMPORTS & MODEL SETUP ---
from ortools.sat.python import cp_model
import pandas as pd
import math
from collections import defaultdict

unmet = {}  # Dictionary untuk menyimpan variabel unmet demand

model = cp_model.CpModel()

# --- 1. DATA PREPARATION (Diasumsikan sudah dimuat) ---
# Diperlukan DataFrame: df_edges_final, df_middle_edge_list, df_resources_joined, df_demand, df_order_constraints
# Pastikan semua DataFrame ini sudah di-load dengan benar sebelum menjalankan kode ini.

vehicle_modes = ['CDD', 'CDE', 'GrandMax', 'FUSO', 'Kijang']
mode_param = {
    'CDD': 280,
    'CDE': 200,
    'GrandMax': 120,
    'Kijang': 80,
    'FUSO': 350 # Pastikan FUSO ada jika digunakan
}
PENALTY_RATE = 100_000_000_000 # Penalti untuk setiap unit demand yang tidak terpenuhi (untuk motivasi solver)

WORKING_HOURS_PER_DAY = 10
WORKING_DAYS_PER_MONTH = 24
TOTAL_WORKING_HOURS = WORKING_HOURS_PER_DAY * WORKING_DAYS_PER_MONTH  # 240 jam
DAYS_IN_MONTH = WORKING_DAYS_PER_MONTH # Definisikan untuk konsistensi

# Konversi kolom numerik
for col in ['volume_per_trip', 'cost_per_trip']:
    df_edges_final[col] = pd.to_numeric(df_edges_final[col], errors='coerce')
df_middle_edge_list['max_volume'] = pd.to_numeric(df_middle_edge_list['max_volume'], errors='coerce')

# --- Paksa update volume_per_trip di df_edges_final sesuai mode_param ---
df_edges_final['mode_type'] = df_edges_final['mode_type'].str.strip()  # Buang spasi ekstra
for mode, vol in mode_param.items():
    df_edges_final.loc[df_edges_final['mode_type'] == mode, 'volume_per_trip'] = vol

# --- Penyesuaian: Sesuaikan volume_per_trip dengan max_volume per rute (jika max_volume adalah batas per trip) ---
# Membuat indeks untuk df_middle_edge_list agar pencarian lebih efisien
df_middle_edge_indexed = df_middle_edge_list.set_index(['origin_id', 'destination_id'])

for idx, row in df_edges_final.iterrows():
    i, j, m = row['source_node'], row['target_node'], row['mode_type']
    
    # Cek apakah rute (i, j) ada di df_middle_edge_indexed dan punya max_volume
    if (i, j) in df_middle_edge_indexed.index:
        route_max_volume_per_trip = df_middle_edge_indexed.loc[(i, j), 'max_volume']
        if pd.notna(route_max_volume_per_trip) and route_max_volume_per_trip > 0:
            # Volume efektif per trip adalah minimum dari volume kendaraan atau batas rute
            df_edges_final.loc[idx, 'volume_per_trip'] = min(row['volume_per_trip'], route_max_volume_per_trip)
        # Jika route_max_volume_per_trip NaN atau 0, kita biarkan volume_per_trip sesuai mode_param
        # Ini berarti rute tidak memiliki batasan volume per trip yang lebih rendah
        # dari kapasitas kendaraan standar.

# Buat dictionary volume_per_trip setelah modifikasi df_edges_final
volume_per_trip = {
    (r.source_node, r.target_node, r.mode_type): int(round(r.volume_per_trip))
    for _, r in df_edges_final.iterrows() if pd.notna(r.volume_per_trip)
}

# Dictionary lead time dari SDC ke DC tujuan
lead_time_dict_sdc = {
    ("SDC", r['target_node']): int(r['lead_time_days']) * 24 # Konversi ke jam
    for _, r in df_order_constraints.iterrows() if pd.notna(r['lead_time_days'])
}

# Mapping kecepatan kendaraan
speed_by_mode = {
    'GrandMax': 40,
    'Kijang': 50,
    'CDE': 45,
    'CDD': 45,
    'FUSO': 35
}

# Buat dictionary lead_time_dict_dc berdasarkan rute antar DC dan mode
lead_time_dict_dc = {}
# df_middle_edge tetap merujuk ke df_middle_edge_list seperti permintaan user
df_middle_edge = df_middle_edge_list.copy() 

for _, row in df_edges_final.iterrows():
    i, j, m = row['source_node'], row['target_node'], row['mode_type']
    
    if (i, j) in df_middle_edge_indexed.index: # Gunakan indexed df_middle_edge_list
        dist_km = df_middle_edge_indexed.loc[(i, j), 'distance_km']
        speed = speed_by_mode.get(m, 40)  # Default 40 km/jam kalau mode gak dikenal
        if pd.notna(dist_km) and speed > 0:
            lead_time = int(round(dist_km / speed)) # Hasil dalam jam (km / (km/jam))
            lead_time_dict_dc[(i, j, m)] = lead_time

# Gabungkan kedua dictionary lead time
lead_time_dict = {**lead_time_dict_sdc, **lead_time_dict_dc}

cost_per_trip = {
    (r.source_node, r.target_node, r.mode_type): int(round(r.cost_per_trip))
    for _, r in df_edges_final.iterrows() if pd.notna(r.cost_per_trip)
}

# volume_cap_dict dan constraint terkait DIHAPUS karena max_volume sekarang diinterpretasikan per trip
# dan sudah disesuaikan ke volume_per_trip di awal.

demand_dict = {
    r['DC ID']: int(round(r['Total Demand (box)']))
    for _, r in df_demand.iterrows() if pd.notna(r['Total Demand (box)'])
}

capacity_dict = {
    r['dc_id']: int(round(r['Capacity']))
    for _, r in df_resources_joined.iterrows() if pd.notna(r['Capacity'])
}

order_limit = {
    r['target_node']: int(r['order_wk'] * 4) # Diasumsikan 4 minggu dalam sebulan
    for _, r in df_order_constraints.iterrows() if pd.notna(r['order_wk'])
}

trip_limit = {}
for _, row in df_resources_joined.iterrows():
    dc = row['dc_id']
    for mode in vehicle_modes:
        if mode in row and pd.notna(row[mode]):
            # trip_limit adalah jumlah total trip bulanan yang bisa dilakukan oleh armada di DC tersebut
            trip_limit[(dc, mode)] = int(row[mode] * DAYS_IN_MONTH)

# --- Tambahan: Anggap SDC punya kendaraan unlimited ---
for mode in vehicle_modes:
    trip_limit[("SDC", mode)] = 999999  # Nilai sangat besar agar tidak membatasi

# Jika df_turnover tidak tersedia, buat dummy
if 'df_turnover' not in locals():
    unique_dc_ids = df_demand['DC ID'].unique()
    df_turnover = pd.DataFrame({
        'DC ID': unique_dc_ids,
        'Capacity': [100000] * len(unique_dc_ids), # Kapasitas default tinggi
        'Turnover Per Bulan': [1] * len(unique_dc_ids) # Turnover default 1
    })

turnover_capacity_dict = {
    row['DC ID']: int(round(row['Capacity'] * (row['Turnover Per Bulan'] + 1)))
    for _, row in df_turnover.iterrows()
    if pd.notna(row['Capacity']) and pd.notna(row['Turnover Per Bulan'])
}



# --- 2. DECISION VARIABLES ---
x = {}
for i, j, m in df_edges_final[['source_node', 'target_node', 'mode_type']].itertuples(index=False, name=None):
    vol = volume_per_trip.get((i, j, m), 1) # Default 1 untuk menghindari pembagian dengan nol
    dem = demand_dict.get(j, 0) # Default 0 jika DC tidak ada di demand_dict
    # Batas atas untuk trip bisa lebih realistis: total demand tertinggi dibagi volume terkecil
    # Ini untuk mencegah variabel menjadi terlalu besar dan memperlambat solver
    max_trips_possible = math.ceil(max(demand_dict.values()) / min(mode_param.values())) if mode_param else 1_000_000
    x[i, j, m] = model.NewIntVar(0, max_trips_possible, f"x_{i}{j}{m}")


# --- 3. CONSTRAINTS ---
trip_vars = defaultdict(list) # Untuk mengumpulkan variabel trip per (DC asal, mode)
incoming_vars = defaultdict(list) # Untuk mengumpulkan variabel trip masuk per DC tujuan

# Menggunakan df_middle_edge_list untuk definisi rute valid
valid_routes = set(zip(df_edges_final.source_node, df_edges_final.target_node)) | \
               set(zip(df_middle_edge_list.origin_id, df_middle_edge_list.destination_id))

for (i, j, m), var in x.items():
    vol = volume_per_trip.get((i, j, m), 0)
    trip_vars[(i, m)].append(var)
    incoming_vars[j].append((var, vol))
    
    # --- Constraint: Lead Time × Working Hours ---
    # Hanya tambahkan constraint lead time jika BUKAN dari SDC
    # Prioritaskan lead time spesifik per mode, lalu lead time rute umum
    lead = lead_time_dict.get((i, j, m))
    if lead is None:
        lead = lead_time_dict.get((i, j)) # Jika tidak ada mode spesifik, coba rute umum

    if lead is not None and not i.startswith("SDC") and lead > 0:
        # Cari jumlah kendaraan di depot i untuk mode m
        n_vehicle_per_dc_mode = 0
        if i in df_resources_joined['dc_id'].values and m in df_resources_joined.columns:
            temp_n_vehicle = df_resources_joined.loc[df_resources_joined['dc_id'] == i, m].squeeze()
            if isinstance(temp_n_vehicle, pd.Series): # Handle jika .squeeze() mengembalikan Series kosong/multi-nilai
                n_vehicle_per_dc_mode = 0 if temp_n_vehicle.empty else temp_n_vehicle.iloc[0]
            else:
                n_vehicle_per_dc_mode = temp_n_vehicle
            
            if pd.isna(n_vehicle_per_dc_mode):
                n_vehicle_per_dc_mode = 0
            n_vehicle_per_dc_mode = int(n_vehicle_per_dc_mode) # Pastikan integer

        if n_vehicle_per_dc_mode > 0:
            total_hours_per_vehicle_per_month = WORKING_HOURS_PER_DAY * WORKING_DAYS_PER_MONTH
            trips_per_vehicle_per_month = total_hours_per_vehicle_per_month // (2 * lead) # 2 * lead untuk round trip

            max_trip_by_lead_time = n_vehicle_per_dc_mode * trips_per_vehicle_per_month
            model.Add(var <= max_trip_by_lead_time)
        else:
            # Jika tidak ada kendaraan untuk mode ini di DC sumber, maka trip harus 0
            # model.Add(var == 0)
            pass
    elif lead == 0 and not i.startswith("SDC"): # Jika lead time 0 dan bukan SDC, batasi trip jadi 0 (tidak realistis)
        model.Add(var == 0)

    # --- Constraint: Valid Route ---
    # Memastikan hanya trip pada rute yang valid yang dipertimbangkan
    if (i, j) not in valid_routes:
        model.Add(var == 0)

    # --- Constraint: SDC ke DC order constraint mingguan (per MODA) ---
    # Ini memastikan setiap MODA dari SDC ke DC tujuan memiliki batas trip sendiri
    if i.startswith("SDC") and j in order_limit:
        # Asumsi: order_limit[j] adalah batas trip untuk setiap moda ke DC tersebut dari SDC
        model.Add(var <= order_limit[j])


# --- Constraint: total trip per (i, mode) ---
# Membatasi jumlah total trip yang bisa dilakukan oleh armada tertentu dari DC asal
for (i, m), vars_list in trip_vars.items():
    if (i, m) in trip_limit:
        model.Add(sum(vars_list) <= trip_limit[(i, m)])


# --- Constraint: total volume masuk per DC (Kapasitas Gudang Tujuan) ---
# Memastikan total volume yang masuk ke DC tujuan tidak melebihi kapasitas gudang
for j, varlist in incoming_vars.items():
    capacity = turnover_capacity_dict.get(j, capacity_dict.get(j, 100_000_000)) # Default tinggi jika tidak ada
    if capacity > 0: # Pastikan kapasitas positif untuk menghindari masalah
        model.Add(sum(var * vol for var, vol in varlist) <= capacity)


# --- TAMBAHAN: Variabel kendaraan aktif per DC & Mode ---
vehicle_used = {}

for i in df_resources_joined['dc_id'].unique():
    for m in vehicle_modes:
        relevant_trips = [(j, mode) for (src, j, mode) in x if src == i and mode == m]
        if not relevant_trips:
            continue

        total_workload_expr = []
        for j, mode in relevant_trips:
            var = x[i, j, m]
            lead = lead_time_dict.get((i, j, m)) or lead_time_dict.get((i, j)) or 12  # default 12 jam
            total_workload_expr.append(var * (2 * lead))  # round trip

        vehicle_var = model.NewIntVar(0, 999, f"vehicle_used_{i}_{m}")
        model.Add(vehicle_var * WORKING_HOURS_PER_MONTH >= sum(total_workload_expr))
        vehicle_used[(i, m)] = vehicle_var

# --- Constraint global kendaraan per mode ---
vehicle_global_limit = {
    'GrandMax': 30,
    'CDE': 102,
    'CDD': 48,
    'Kijang': 1,
}

for m in vehicle_modes:
    model.Add(
        sum(vehicle_used[(i, m)] for i in df_resources_joined['dc_id'].unique() if (i, m) in vehicle_used)
        <= vehicle_global_limit.get(m, 0)
    )

# --- PENAMBAHAN UNTUK KEANEKARAGAMAN MODA (DIVERSITY BONUS) - DIHAPUS ---
# Variabel y dan batasan terkait dihapus
# diversity_bonus_terms dihapus dari fungsi objektif


# --- 4. OBJECTIVE ---
cost_terms = [x[i, j, m] * cost_per_trip.get((i, j, m), 0) for (i, j, m) in x]
penalty_terms = []
sent_volume_var = {}

for j, demand in demand_dict.items():
    sent = model.NewIntVar(0, demand, f"sent_{j}")
    # Volume yang dikirim ke DC j
    model.Add(sent == sum(x[i, j2, m] * volume_per_trip.get((i, j2, m), 0)
                        for (i, j2, m) in x if j2 == j))

    unmet_var = model.NewIntVar(0, demand, f"unmet_{j}")
    model.AddMaxEquality(unmet_var, [0, demand - sent])  # ✅ Fix unmet jadi max(0, demand - sent)

        
    # Tambahkan penalti untuk setiap unmet demand
    penalty_terms.append(unmet_var * PENALTY_RATE)
    
    unmet[j] = unmet_var  # Simpan variabel unmet untuk laporan nanti
    sent_volume_var[j] = sent  # Simpan total volume yang berhasil dikirim



# Fungsi objektif: Minimalkan (biaya distribusi + penalti unmet demand)
# Bagian diversity_bonus_terms telah dihapus
model.Minimize(sum(cost_terms) + sum(penalty_terms))

# --- 5. SOLVER ---
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 180 # Batas waktu eksekusi solver
solver.parameters.num_search_workers = 4  # Mengaktifkan multi-threading
solver.parameters.linearization_level = 2  # Level linearisasi (bisa membantu kinerja)

status = solver.Solve(model) # Jalankan solver

print(f"⏱ Runtime solver: {solver.WallTime():.2f} detik")

print("\n📦 Summary per DC (Sent vs Unmet):")
for j in sent_volume_var:
    print(f"{j}: sent = {solver.Value(sent_volume_var[j]):,} | unmet = {solver.Value(unmet[j]):,}")


# --- 6. OUTPUT HASIL SOLUSI ---
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print("✅ Solusi ditemukan.")
else:
    print("❌ Tidak ada solusi atau tidak mencapai optimal dalam batas waktu.")

print("\n🚚 Trip Aktif dalam Solusi:\n" + "-" * 50)
total_cost = 0
total_volume = 0
sdc_to_dc_cost = 0 # Inisialisasi biaya SDC-DC
inter_dc_cost = 0  # Inisialisasi biaya Antar-DC


for (i, j, m), var in x.items():
    trip = solver.Value(var)
    if trip > 0:
        cost = cost_per_trip.get((i, j, m), 0)
        vol = volume_per_trip.get((i, j, m), 0)
        
        # Peringatan jika ada trip tanpa biaya atau volume (biasanya berarti ada masalah data)
        if cost == 0 or vol == 0:
            print(f"❗Trip tanpa biaya/volume: {i} → {j} via {m} | cost = {cost}, vol = {vol}")

        subtotal = trip * cost
        volume_total = trip * vol
        print(f"{i} → {j} via {m} | trip = {trip:,} | cost/trip = Rp {cost:,} | total cost = Rp {subtotal:,} | volume = {volume_total:,}")
        total_cost += subtotal
        total_volume += volume_total

        # --- Tambahan: Klasifikasi Biaya ---
        if i.startswith("SDC"):
            sdc_to_dc_cost += subtotal
        else:
            inter_dc_cost += subtotal
        
        # Peringatan untuk trip yang sangat mahal per box
        if trip > 0 and vol > 0:
            cost_per_box = cost / vol
            if cost_per_box > 1_000_000: # Batas peringatan, sesuaikan
                print(f"⚠ TRIP MAHAL: {i} → {j} via {m} = Rp {cost_per_box:,.0f}/box")


print("-" * 50)
print(f"💰 Total Biaya Distribusi: Rp {total_cost:,}")
print(f"  💸 Biaya SDC ke DC: Rp {sdc_to_dc_cost:,}") # Cetak rincian
print(f"  💸 Biaya Antar DC: Rp {inter_dc_cost:,}")   # Cetak rincian
print(f"📦 Total Volume Dikirim: {total_volume:,} box")

print("\n💸 Trip dengan Cost per Box Tertinggi:")
trip_costs = []

for (i, j, m), var in x.items():
    trip = solver.Value(var)
    if trip > 0:
        cost = cost_per_trip.get((i, j, m), 0)
        vol = volume_per_trip.get((i, j, m), 0)
        if vol > 0:
            cost_per_box = cost / vol
            trip_costs.append((cost_per_box, i, j, m, cost, vol, trip))

trip_costs.sort(reverse=True)  # Urutkan dari yang paling mahal per box
for cpb, i, j, m, c, v, t in trip_costs[:10]:  # Tampilkan top 10
    print(f"🔥 Rp {cpb:,.0f}/box → {i} → {j} via {m} | trip = {t}, cost/trip = Rp {c:,}, vol/trip = {v}")


# Hitung total unmet demand dan penalti
total_unmet = sum(solver.Value(unmet[j]) for j in demand_dict)
total_penalty = total_unmet * PENALTY_RATE

# Bagian bonus keanekaragaman dihapus dari output
print(f"🚫 Total Unmet Demand: {total_unmet:,} box")
print(f"💣 Total Penalti: Rp {total_penalty:,.0f}")
print(f"🧾 Biaya Total Akhir (Distribusi + Denda): Rp {total_cost + total_penalty:,.0f}")


# --- 7. DEBUG: ALASAN UNMET DEMAND ---
print("\n🔍 Diagnosa Unmet Demand per DC:\n" + "-" * 60)

sent_volume = {
    j: sum(
        solver.Value(x[i, j2, m]) * volume_per_trip.get((i, j2, m), 0)
        for (i, j2, m) in x if j2 == j
    )
    for j in demand_dict
}

unmet_volume = {
    j: demand_dict[j] - sent_volume.get(j, 0)
    for j in demand_dict
}

debug_data = []

for j in demand_dict:
    demand = demand_dict[j]
    sent = sent_volume.get(j, 0)
    unmet = unmet_volume[j]
    kapasitas = turnover_capacity_dict.get(j, capacity_dict.get(j, 100_000_000))
    rute_masuk = sum(1 for (i, j2, m) in x if j2 == j)
    trip_dikirim = sum(solver.Value(x[i, j2, m]) for (i, j2, m) in x if j2 == j)
    
    # Bagian modes_used_for_dc juga dihapus karena variabel y tidak lagi ada
    # modes_used_for_dc = [m for m in vehicle_modes if (j,m) in y and solver.Value(y[j,m]) == 1]

    debug_data.append({
        'DC': j,
        'Demand': demand,
        'Sent': sent,
        'Unmet': unmet,
        'Kapasitas Efektif': kapasitas,
        'Jumlah Rute Masuk': rute_masuk,
        'Jumlah Trip Dikirim': trip_dikirim,
        'Moda Digunakan': "N/A (Diversity Bonus Disabled)" # Ganti dengan pesan ini
    })

df_debug = pd.DataFrame(debug_data).sort_values(by='Unmet', ascending=False)

# Tampilkan 30 DC dengan unmet demand terbesar
print(df_debug.head(30).to_string(index=False))

# Tambahan diagnosa untuk DC dengan unmet tertinggi
print("\n🧠 Analisis Constraint Detail untuk DC dengan Unmet Tinggi:")
for j in df_debug.head(5)['DC']:  # Ambil 5 DC teratas untuk analisis detail
    print(f"\n[DC: {j}]")
    
    rute_masuk_detail = [(i, m) for (i, j2, m) in x if j2 == j]
    if not rute_masuk_detail:
        print("❌ Tidak ada rute masuk ke DC ini.")
        continue

    for (i, m) in rute_masuk_detail:
        vol = volume_per_trip.get((i, j, m), 0)
        trips_val = solver.Value(x[i, j, m])
        
        # Informasi Batas Trip Armada
        if i.startswith("SDC"):
            max_trip_limit_text = "∞ (Unlimited)"
        else:
            max_trip_limit = trip_limit.get((i, m), 0)
            max_trip_limit_text = f"{max_trip_limit:,}"

        # Informasi Batas Trip dari Lead Time
        lead = lead_time_dict.get((i, j, m))
        if lead is None:
            lead = lead_time_dict.get((i, j))

        max_trip_lead_text = '–'
        if lead is not None and lead > 0 and not i.startswith("SDC"):
            n_vehicle_per_dc_mode = 0
            if i in df_resources_joined['dc_id'].values and m in df_resources_joined.columns:
                temp_n_vehicle = df_resources_joined.loc[df_resources_joined['dc_id'] == i, m].squeeze()
                if isinstance(temp_n_vehicle, pd.Series):
                    n_vehicle_per_dc_mode = 0 if temp_n_vehicle.empty else temp_n_vehicle.iloc[0]
                else:
                    n_vehicle_per_dc_mode = temp_n_vehicle
                if pd.isna(n_vehicle_per_dc_mode):
                    n_vehicle_per_dc_mode = 0
                n_vehicle_per_dc_mode = int(n_vehicle_per_dc_mode)

            if n_vehicle_per_dc_mode > 0:
                total_hours_per_vehicle_per_month = WORKING_HOURS_PER_DAY * WORKING_DAYS_PER_MONTH
                trips_per_vehicle_per_month = total_hours_per_vehicle_per_month // (2 * lead)
                max_trip_lead_text = f"{n_vehicle_per_dc_mode * trips_per_vehicle_per_month:,}"
            else:
                max_trip_lead_text = "0 (No vehicles)"
        elif i.startswith("SDC"): # Khusus SDC, batasan order_wk diterapkan per moda
            max_trip_lead_text = f"Controlled by order_wk ({order_limit.get(j, 'N/A')})"


        route_valid = (i, j) in valid_routes
        # Max_volume_per_trip dari data rute mempengaruhi 'vol' (volume_per_trip) di awal.
        # Ini adalah nilai asli dari df_middle_edge_list
        route_max_vol_per_trip_from_data = df_middle_edge_indexed.loc[(i,j), 'max_volume'] if (i,j) in df_middle_edge_indexed.index and pd.notna(df_middle_edge_indexed.loc[(i,j), 'max_volume']) else "No specific limit"

        # print(f"- {i} → {j} via {m}:")
        # print(f"  ✔ Rute valid? {route_valid}")
        # print(f"  🚚 Trip yang digunakan: {trips_val:,}")
        # print(f"  📦 Volume/trip (setelah penyesuaian): {vol:,}")
        # print(f"  🛣 Max_volume_per_trip dari data rute: {route_max_vol_per_trip_from_data}")
        # print(f"  💼 Batas trip dari armada: {max_trip_limit_text}")
        # print(f"  ⏱ Batas trip dari lead time: {max_trip_lead_text}")

print("\n📨 Detail Rute Masuk ke DC033 (Contoh):")
for (i, j, m) in x:
    if j == "DC033": # Ganti dengan DC yang ingin Anda periksa detailnya
        trips = solver.Value(x[i, j, m])
        vol = volume_per_trip.get((i, j, m), 0)
        print(f"{i} → {j} via {m}: trips = {trips}, total vol = {trips * vol:,} | vol/trip = {vol}")

from math import ceil

# --- Biaya Antar DC Berdasarkan Utilisasi Armada ---
print("\n🚛 Biaya Antar DC (Baru - Berdasarkan Utilisasi Armada):\n" + "-" * 60)

inter_dc_cost_new = 0
vehicle_workload = defaultdict(int)  # key: (i, m), value: total jam kerja (trip × durasi)
vehicle_fixed_cost = defaultdict(int)  # key: (i, m), value: fixed cost per kendaraan

# Durasi kerja bulanan
WORKING_HOURS_PER_MONTH = 240
FUEL_COST_PER_DAY = 200_000

# Bangun fixed cost dari df_edges_final
for _, row in df_edges_final.iterrows():
    i, j, m = row['source_node'], row['target_node'], row['mode_type']
    if not i.startswith("SDC"):
        vehicle_fixed_cost[(i, m)] = int(row['cost_per_trip'])  # cost_per_trip = fixed cost per kendaraan

# Estimasi total jam kerja kendaraan (per DC asal & mode)
for (i, j, m), var in x.items():
    if i.startswith("SDC"):
        continue  # lewati, ini ditangani di bagian SDC
    trip = solver.Value(var)
    if trip > 0:
        lead_time = lead_time_dict.get((i, j, m)) or lead_time_dict.get((i, j))
        if lead_time is None or lead_time == 0:
            continue
        duration_per_trip = 2 * lead_time  # round trip
        vehicle_workload[(i, m)] += trip * duration_per_trip



inter_dc_cost_new = 0
total_fixed_cost = 0
total_fuel_cost = 0



# --- 1. FIXED COST berdasarkan kendaraan aktif per DC & mode ---
for (i, m), total_workload in vehicle_workload.items():
    n_kendaraan = math.ceil(total_workload / WORKING_HOURS_PER_MONTH)
    fixed_cost = vehicle_fixed_cost.get((i, m), 0)
    fixed_component = n_kendaraan * fixed_cost
    total_fixed_cost += fixed_component  # ✅ track fixed cost
    inter_dc_cost_new += fixed_component

    print(f"🚐 {i} - {m} | Jam total: {total_workload}, Kendaraan aktif: {n_kendaraan}, Fixed: Rp {fixed_component:,}")

# --- 2. VARIABLE COST (bensin) berdasarkan trip ---
for (i, j, m), var in x.items():
    if i.startswith("SDC"):  # Skip jalur dari pabrik
        continue
    trip = solver.Value(var)
    if trip > 0:
        lead_time = lead_time_dict.get((i, j, m)) or lead_time_dict.get((i, j))
        if lead_time is None or lead_time == 0:
            continue

        duration_per_trip = 2 * lead_time
        duration_in_days = math.ceil(duration_per_trip / 24)
        fuel_component = trip * duration_in_days * FUEL_COST_PER_DAY

        total_fuel_cost += fuel_component  # ✅ track fuel cost
        inter_dc_cost_new += fuel_component

        print(f"⛽ {i} → {j} via {m} | trips: {trip}, durasi: {duration_in_days} hari, fuel cost: Rp {fuel_component:,}")

# --- 3. REKAP TOTAL COST ---
print("-" * 60)
print(f"💸 Biaya Antar DC (Baru): Rp {inter_dc_cost_new:,}")
print(f"   └── Fixed Cost: Rp {total_fixed_cost:,}")
print(f"   └── Fuel Cost:  Rp {total_fuel_cost:,}")



# --- 3. DRIVER COST ---
total_driver_cost = 0

for (i, m), total_workload in vehicle_workload.items():
    n_kendaraan = math.ceil(total_workload / WORKING_HOURS_PER_MONTH)
    n_supir = 2 * n_kendaraan + 2  # 2 per kendaraan + 2 supir tambahan

    # Ambil biaya driver per (DC, mode)
    driver_cost = df_resources_joined[
        (df_resources_joined['dc_id'] == i)
    ]['Driver Cost'].values

    if len(driver_cost) == 0:
        print(f"[WARNING] Tidak ada data driver cost untuk {i}-{m}, diasumsikan Rp 0")
        driver_cost = [0]

    cost_per_driver = driver_cost[0]
    total_driver_component = n_supir * cost_per_driver
    total_driver_cost += total_driver_component

    print(f"🧍 {i} - {m} | Kendaraan aktif: {n_kendaraan}, Supir: {n_supir}, "
          f"Cost/Driver: Rp {cost_per_driver:,}, Total: Rp {total_driver_component:,}")

# --- 4. TOTAL BIAYA (DC + DRIVER) ---
grand_total_cost = inter_dc_cost_new + total_driver_cost

print("-" * 60)
print(f"💸 Biaya Antar DC (Baru): Rp {inter_dc_cost_new:,}")
print(f"🚚 Biaya Supir         : Rp {total_driver_cost:,}")
print(f"💰 TOTAL KESELURUHAN   : Rp {grand_total_cost:,}")

print("\n📊 Total Kendaraan Aktif per Mode (Global):")
for m in vehicle_modes:
    total = sum(solver.Value(vehicle_used[(i, m)])
                for i in df_resources_joined['dc_id'].unique()
                if (i, m) in vehicle_used)
    print(f"{m}: {total} kendaraan")

for dc in df_debug.head(10)['DC']:
    print(f"🛑 {dc} → order_limit: {order_limit.get(dc, 'N/A')}")

# Misal kamu mau debug DC016 (atau DC manapun yang masih unmet)
dc_target = 'DC016'

print(f"\n🔎 Debug semua rute masuk ke {dc_target}")
for (i, j, m) in x:
    if j == dc_target:
        trips = solver.Value(x[i, j, m])
        vol = volume_per_trip.get((i, j, m), 0)
        cost = cost_per_trip.get((i, j, m), 0)
        if vol > 0:
            cost_per_box = cost / vol
            print(f"{i} → {j} via {m}: trip = {trips}, vol/trip = {vol}, cost/trip = Rp {cost:,}, cost/box = Rp {cost_per_box:,.0f}")