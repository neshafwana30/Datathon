import pandas as pd
import numpy as np
import random
from math import radians, sin, cos, atan2, sqrt

# --- Global Configurations and Helper Functions ---
# Defining common lists for consistency across sheets
dummy_dcs = ['CDP-KLT', 'CDP-SUL', 'CDP-BNR', 'DC-JKT', 'DC-SBY', 'DC-MDN']
dummy_zones = ['Kalimantan', 'Sulawesi', 'BaliNusra', 'Jawa', 'Sumatera']
dummy_cities_kalsulbanusra = ['Balikpapan', 'Pontianak', 'Palangkaraya'] # Specific Kalimantan cities
dummy_cities_sulawesi = ['Makassar', 'Manado', 'Kendari', 'Palu'] # Specific Sulawesi cities
dummy_cities_balinusra = ['Denpasar', 'Mataram'] # Specific BaliNusra cities
dummy_cities_jawa = ['Jakarta', 'Surabaya', 'Bandung', 'Semarang', 'Yogyakarta'] # Specific Jawa cities
dummy_cities_sumatera = ['Medan', 'Palembang', 'Padang', 'Pekanbaru'] # Specific Sumatera cities

all_cities_pool = (dummy_cities_kalsulbanusra + dummy_cities_sulawesi + dummy_cities_balinusra +
                   dummy_cities_jawa + dummy_cities_sumatera)

dummy_ports = ['Tg. Priok', 'Surabaya Port', 'Makassar Port', 'Balikpapan Port', 'Denpasar Port', 'Belawan Port']
dummy_stps = ['TransCepat', 'LogistikMaju', 'GudangEfisiensi', 'EkspedisiKilat']
vehicle_types_truck = ['Truck (Small)', 'Truck (Medium)', 'Truck (Large)', 'Fuso', 'Tronton']
vehicle_types_last_mile = ['Motorcycle', 'Van', 'Pickup Truck']
container_types = ['20ft Dry', '40ft Dry', '20ft Reefer', '40ft Reefer'] # Length is 4
shipment_types = ['FTL', 'LTL', 'Pallet', 'Box']
performance_metrics = ['On-Time Delivery Rate', 'Damage Rate', 'Lead Time Adherence', 'Cost Efficiency Score', 'Response Time (Hours)']

# Define a more precise mapping for cities/DCs/ports to coordinates and zones
location_details = {
    'Balikpapan': {'coords': (-1.2653, 116.8253), 'zone': 'Kalimantan', 'province': 'Kalimantan Timur'},
    'Pontianak': {'coords': (-0.0267, 109.3300), 'zone': 'Kalimantan', 'province': 'Kalimantan Barat'},
    'Palangkaraya': {'coords': (-2.2089, 113.9167), 'zone': 'Kalimantan', 'province': 'Kalimantan Tengah'},
    'Makassar': {'coords': (-5.1477, 119.4327), 'zone': 'Sulawesi', 'province': 'Sulawesi Selatan'},
    'Manado': {'coords': (1.4748, 124.8421), 'zone': 'Sulawesi', 'province': 'Sulawesi Utara'},
    'Kendari': {'coords': (-3.9888, 122.5159), 'zone': 'Sulawesi', 'province': 'Sulawesi Tenggara'},
    'Palu': {'coords': (-0.8906, 119.8829), 'zone': 'Sulawesi', 'province': 'Sulawesi Tengah'},
    'Denpasar': {'coords': (-8.6500, 115.2167), 'zone': 'BaliNusra', 'province': 'Bali'},
    'Mataram': {'coords': (-8.5833, 116.1167), 'zone': 'BaliNusra', 'province': 'Nusa Tenggara Barat'},
    'Jakarta': {'coords': (-6.2088, 106.8456), 'zone': 'Jawa', 'province': 'DKI Jakarta'},
    'Surabaya': {'coords': (-7.2575, 112.7521), 'zone': 'Jawa', 'province': 'Jawa Timur'},
    'Bandung': {'coords': (-6.9175, 107.6191), 'zone': 'Jawa', 'province': 'Jawa Barat'},
    'Semarang': {'coords': (-6.9667, 110.4233), 'zone': 'Jawa', 'province': 'Jawa Tengah'},
    'Yogyakarta': {'coords': (-7.7956, 110.3695), 'zone': 'Jawa', 'province': 'DI Yogyakarta'},
    'Medan': {'coords': (3.5952, 98.6722), 'zone': 'Sumatera', 'province': 'Sumatera Utara'},
    'Palembang': {'coords': (-2.9761, 104.7754), 'zone': 'Sumatera', 'province': 'Sumatera Selatan'},
    'Padang': {'coords': (-0.9570, 100.3540), 'zone': 'Sumatera', 'province': 'Sumatera Barat'},
    'Pekanbaru': {'coords': (0.5061, 101.4477), 'zone': 'Sumatera', 'province': 'Riau'},
    'Pabrik Karawang': {'coords': (-6.3022, 107.3082), 'zone': 'Jawa', 'province': 'Jawa Barat'},
    'CDP-KLT': {'coords': (-0.5, 115.0), 'zone': 'Kalimantan', 'province': 'Kalimantan Tengah'}, # Representative for Kalimantan
    'CDP-SUL': {'coords': (-3.0, 120.0), 'zone': 'Sulawesi', 'province': 'Sulawesi Tengah'}, # Representative for Sulawesi
    'CDP-BNR': {'coords': (-8.0, 117.0), 'zone': 'BaliNusra', 'province': 'Nusa Tenggara Barat'}, # Representative for BaliNusra
    'DC-JKT': {'coords': (-6.2, 106.8), 'zone': 'Jawa', 'province': 'DKI Jakarta'},
    'DC-SBY': {'coords': (-7.2, 112.7), 'zone': 'Jawa', 'province': 'Jawa Timur'},
    'DC-MDN': {'coords': (3.6, 98.6), 'zone': 'Sumatera', 'province': 'Sumatera Utara'},
    'Tg. Priok': {'coords': (-6.1051, 106.8870), 'zone': 'Jawa', 'province': 'DKI Jakarta'},
    'Surabaya Port': {'coords': (-7.1994, 112.7214), 'zone': 'Jawa', 'province': 'Jawa Timur'},
    'Makassar Port': {'coords': (-5.1328, 119.4005), 'zone': 'Sulawesi', 'province': 'Sulawesi Selatan'},
    'Balikpapan Port': {'coords': (-1.2721, 116.7865), 'zone': 'Kalimantan', 'province': 'Kalimantan Timur'},
    'Denpasar Port': {'coords': (-8.7423, 115.2160), 'zone': 'BaliNusra', 'province': 'Bali'},
    'Belawan Port': {'coords': (3.7845, 98.6873), 'zone': 'Sumatera', 'province': 'Sumatera Utara'}
}

def get_coords(location_name):
    # Returns (lat, long)
    return location_details.get(location_name, {'coords': (np.random.uniform(-8.0, 5.0), np.random.uniform(95.0, 140.0))})['coords']

def get_zone_from_location(location_name):
    # Returns zone string
    return location_details.get(location_name, {'zone': 'Unknown'})['zone']

def get_province_from_location(location_name):
    # Returns province string
    return location_details.get(location_name, {'province': 'Unknown'})['province']

def get_cities_in_zone(zone_name):
    return [city for city, details in location_details.items() if details.get('zone') == zone_name and 'Pabrik' not in city and 'CDP' not in city and 'DC-' not in city and 'Port' not in city]


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# --- 1. Dummy data for Customer Final.csv ---
num_customers_dummy = 100
customer_ids = [f'CUST{i:03d}' for i in range(num_customers_dummy)]
sub_district_areas = []
customer_latitudes = []
customer_longitudes = []
for _ in range(num_customers_dummy):
    city = random.choice(all_cities_pool)
    sub_district_areas.append(city)
    lat, lon = get_coords(city)
    customer_latitudes.append(lat)
    customer_longitudes.append(lon)

avg_monthly_demands = np.random.randint(50, 1000, num_customers_dummy)

customer_final_data = {
    'Customer ID': customer_ids,
    'Sub-District Area': sub_district_areas,
    'Latitude': customer_latitudes,
    'Longitude': customer_longitudes,
    'Avg Monthly Demand (box)': avg_monthly_demands
}
df_customer_final_dummy = pd.DataFrame(customer_final_data)
print("--- Dummy Customer Final.csv (first 5 rows) ---")
print(df_customer_final_dummy.head())
print("\n")

# --- 2. Dummy data for DC Final.csv (Logically consistent with zones/cities) ---
# Columns: DC, Type, Total Flow (Ton), Total Flow (m3), Port, Zone, City, Lat, Long
num_dcs_in_final = len(dummy_dcs) + 1 # FIX: Set to 7 (1 factory + 6 dummy_dcs) to match population for random.sample

dc_names_final_pool = ['Pabrik Karawang'] + dummy_dcs # Full list of unique DCs
dc_names_final = random.sample(dc_names_final_pool, k=num_dcs_in_final) # Pick unique DCs for this sheet

dc_types_final = [location_details.get(dc, {}).get('type', random.choice(['Factory', 'CDP', 'Indirect DC'])) for dc in dc_names_final]
dc_flows_ton_final = [20000 if dc == 'Pabrik Karawang' else np.random.uniform(1000, 15000) for dc in dc_names_final]
dc_flows_m3_final = [flow * 2 for flow in dc_flows_ton_final]

dc_ports_final = []
dc_zones_final = []
dc_cities_final = []
dc_latitudes_final = []
dc_longitudes_final = []

for dc_name in dc_names_final:
    zone = get_zone_from_location(dc_name)
    dc_zones_final.append(zone)
    city_options = get_cities_in_zone(zone)
    # Ensure city chosen is from the correct zone, or the DC's specific mapped city
    city = dc_name if dc_name in all_cities_pool else random.choice(city_options) if city_options else random.choice(all_cities_pool)
    dc_cities_final.append(city)
    lat, lon = get_coords(dc_name)
    dc_latitudes_final.append(lat)
    dc_longitudes_final.append(lon)
    port_options = [p for p in dummy_ports if get_zone_from_location(p) == zone]
    dc_ports_final.append(random.choice(port_options) if port_options else random.choice(dummy_ports))


dc_final_data = {
    'DC': dc_names_final, 'Type': dc_types_final, 'Total Flow (Ton)': dc_flows_ton_final,
    'Total Flow (m3)': dc_flows_m3_final, 'Port': dc_ports_final, 'Zone': dc_zones_final,
    'City': dc_cities_final, 'Lat': dc_latitudes_final, 'Long': dc_longitudes_final
}
df_dc_final_dummy = pd.DataFrame(dc_final_data)
print("--- Dummy DC Final.csv (first 5 rows) ---")
print(df_dc_final_dummy.head())
print("\n")


# --- 3. Dummy data for Final.csv (DC Master Data - Logically consistent) ---
# Columns: DC ID, Area, Type, Latitude, Longitude, Average Monthly Demand, Monthly Operating Cost,
#          Order Freq, Driver Cost, Labor Cost, CDD Cost, CDE Cost, GrandMax Cost, Kijang Cost, Motorbike Cost,
#          CDD Binary, CDE Binary, GrandMax Binary, Kijang Binary, Motorbike Binary,
#          40FT Cost, 20FT Cost, FUSO Cost, Build Up Cost,
#          40FT Binary, 20FT Binary, FUSO Binary, Build Up Binary
num_final_rows_dc_master = len(dummy_dcs) + 1 # Include Karawang factory

dc_ids_master = ['Pabrik Karawang'] + dummy_dcs
area_master = [get_zone_from_location(dc_id) for dc_id in dc_ids_master]
type_master = [location_details.get(dc, {}).get('type', random.choice(['Factory', 'CDP', 'Indirect DC'])) for dc in dc_ids_master]

latitudes_master = [get_coords(name)[0] for name in dc_ids_master]
longitudes_master = [get_coords(name)[1] for name in dc_ids_master]

avg_monthly_demand_master = np.random.randint(1000, 20000, num_final_rows_dc_master) # in units/boxes
monthly_operating_cost_master = np.random.uniform(50000, 1000000, num_final_rows_dc_master)
order_freq_master = np.random.randint(50, 500, num_final_rows_dc_master)

# Vehicle/Cost components
driver_cost_master = np.random.uniform(500, 5000, num_final_rows_dc_master)
labor_cost_master = np.random.uniform(1000, 10000, num_final_rows_dc_master)
cdd_cost_master = np.random.uniform(200, 2000, num_final_rows_dc_master)
cde_cost_master = np.random.uniform(300, 3000, num_final_rows_dc_master)
grandmax_cost_master = np.random.uniform(100, 1000, num_final_rows_dc_master)
kijang_cost_master = np.random.uniform(150, 1200, num_final_rows_dc_master)
motorbike_cost_master = np.random.uniform(50, 300, num_final_rows_dc_master)

cdd_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)
cde_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)
grandmax_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)
kijang_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)
motorbike_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)

ft40_cost_master = np.random.uniform(1000, 8000, num_final_rows_dc_master)
ft20_cost_master = np.random.uniform(500, 4000, num_final_rows_dc_master)
fuso_cost_master = np.random.uniform(800, 6000, num_final_rows_dc_master)
build_up_cost_master = np.random.uniform(1500, 10000, num_final_rows_dc_master)

ft40_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)
ft20_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)
fuso_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)
build_up_binary_master = np.random.choice([0, 1], size=num_final_rows_dc_master)

final_data_dc_master = {
    'DC ID': dc_ids_master, 'Area': area_master, 'Type': type_master,
    'Latitude': latitudes_master, 'Longitude': longitudes_master,
    'Average Monthly Demand': avg_monthly_demand_master,
    'Monthly Operating Cost': monthly_operating_cost_master,
    'Order Freq': order_freq_master,
    'Driver Cost': driver_cost_master, 'Labor Cost': labor_cost_master,
    'CDD Cost': cdd_cost_master, 'CDE Cost': cde_cost_master,
    'GrandMax Cost': grandmax_cost_master, 'Kijang Cost': kijang_cost_master,
    'Motorbike Cost': motorbike_cost_master,
    'CDD Binary': cdd_binary_master, 'CDE Binary': cde_binary_master,
    'GrandMax Binary': grandmax_binary_master, 'Kijang Binary': kijang_binary_master,
    'Motorbike Binary': motorbike_binary_master,
    '40FT Cost': ft40_cost_master, '20FT Cost': ft20_cost_master,
    'FUSO Cost': fuso_cost_master, 'Build Up Cost': build_up_cost_master,
    '40FT Binary': ft40_binary_master, '20FT Binary': ft20_binary_master,
    'FUSO Binary': fuso_binary_master, 'Build Up Binary': build_up_binary_master
}
df_final_dummy = pd.DataFrame(final_data_dc_master)
print("--- Dummy Final.csv (DC Master Data - first 5 rows) ---")
print(df_final_dummy.head())
print("\n")


# --- 4. Dummy data for Vehicle Details.csv (UNCHANGED) ---
num_vehicles_dummy = 10
vehicle_types_all = vehicle_types_truck + vehicle_types_last_mile
vehicle_details_data = {
    'Vehicle Type': random.choices(vehicle_types_all, k=num_vehicles_dummy),
    'Capacity (Ton)': np.random.uniform(0.5, 25, num_vehicles_dummy),
    'Capacity (m3)': np.random.uniform(1, 50, num_vehicles_dummy),
    'Cost/km': np.random.uniform(0.1, 1.5, num_vehicles_dummy),
    'Speed (km/h)': np.random.randint(20, 80, num_vehicles_dummy)
}
df_vehicle_details_dummy = pd.DataFrame(vehicle_details_data)
print("--- Dummy Vehicle Details.csv (first 5 rows) ---")
print(df_vehicle_details_dummy.head())
print("\n")

# --- 5. Dummy data for Container Details.csv (UNCHANGED) ---
num_containers_dummy = len(container_types)
container_details_data = {
    'Container Type': container_types,
    'Capacity (Ton)': [20, 28, 18, 26][:num_containers_dummy],
    'Capacity (m3)': [33, 67, 28, 60][:num_containers_dummy],
    'Cost/Container': np.random.uniform(1000, 5000, num_containers_dummy)
}
df_container_details_dummy = pd.DataFrame(container_details_data)
print("--- Dummy Container Details.csv (first 5 rows) ---")
print(df_container_details_dummy.head())
print("\n")

# --- 6. Dummy data for Customer Code.csv (UNCHANGED) ---
num_customer_codes_dummy = 100
customer_codes_list = [f'CUST{i:03d}' for i in range(num_customer_codes_dummy)]
customer_names_list = [f'Customer {i+1}' for i in range(num_customer_codes_dummy)]
customer_code_data = {
    'Cust_Code': customer_codes_list, 'Customer Name': customer_names_list,
    'Zone': random.choices(dummy_zones, k=num_customer_codes_dummy),
    'City': random.choices(all_cities_pool, k=num_customer_codes_dummy)
}
df_customer_code_dummy = pd.DataFrame(customer_code_data)
print("--- Dummy Customer Code.csv (first 5 rows) ---")
print(df_customer_code_dummy.head())
print("\n")

# --- 7. Dummy data for DC.csv (UPDATED COLUMNS and LOGIC for consistent location) ---
# Columns: Area, DC ID, Distributor, Distributor Area, Type, Sent From,
#          Address, Latitude, Longitude, Monthly Demand (Average FY2021) - Carton, Max Demand - FY2021 - Carton,
#          Fixed Operating Costs
num_dcs_dc_sheet = len(dummy_dcs) + 1 # Include Karawang factory

dc_ids_dc_sheet = ['Pabrik Karawang'] + dummy_dcs
areas_dc_sheet = [get_zone_from_location(dc_id) for dc_id in dc_ids_dc_sheet] # Use Zone as Area

dc_cities_for_sheet = []
for dc_id in dc_ids_dc_sheet:
    if dc_id == 'Pabrik Karawang':
        dc_cities_for_sheet.append('Karawang')
    else:
        zone = get_zone_from_location(dc_id)
        city_options = get_cities_in_zone(zone)
        dc_cities_for_sheet.append(random.choice(city_options) if city_options else random.choice(all_cities_pool))

distributors = [f'Distributor {i+1}' for i in range(num_dcs_dc_sheet)]
distributor_areas = [get_zone_from_location(d) for d in dc_ids_dc_sheet] # This could be same as 'Area' or broader
types_dc_sheet = [location_details.get(dc, {}).get('type', random.choice(['Factory', 'CDP', 'Indirect DC'])) for dc in dc_ids_dc_sheet]
sent_froms = ['Factory'] + random.choices(['Factory', 'Port'], k=len(dummy_dcs))
addresses = [f'Address {i+1}' for i in range(num_dcs_dc_sheet)]

monthly_demand_carton = np.random.randint(5000, 50000, num_dcs_dc_sheet)
max_demand_carton = monthly_demand_carton * np.random.uniform(1.2, 1.5, num_dcs_dc_sheet)
fixed_operating_costs_dc = np.random.uniform(10000, 500000, num_dcs_dc_sheet)

dc_data_updated = {
    'Area': areas_dc_sheet,
    'DC ID': dc_ids_dc_sheet,
    'Distributor': distributors,
    'Distributor Area': distributor_areas,
    'Type': types_dc_sheet,
    'Sent From': sent_froms,
    'Address': addresses,
    'Latitude': [get_coords(d_id)[0] for d_id in dc_ids_dc_sheet],
    'Longitude': [get_coords(d_id)[1] for d_id in dc_ids_dc_sheet],
    'Monthly Demand (Average FY2021) - Carton': monthly_demand_carton,
    'Max Demand - FY2021 - Carton': max_demand_carton,
    'Fixed Operating Costs': fixed_operating_costs_dc
}
df_dc_dummy = pd.DataFrame(dc_data_updated)
print("--- Dummy DC.csv (first 5 rows) ---")
print(df_dc_dummy.head())
print("\n")

# --- 8. Dummy data for Port.csv (UPDATED LOGIC for consistent city/province) ---
num_ports_dummy = len(dummy_ports)

port_data = {
    'Port': dummy_ports,
    'City': [get_province_from_location(p) for p in dummy_ports], # Using Province of the port's city
    'Lat': [get_coords(port_name)[0] for port_name in dummy_ports],
    'Long': [get_coords(port_name)[1] for port_name in dummy_ports]
}
df_port_dummy = pd.DataFrame(port_data)
print("--- Dummy Port.csv (first 5 rows) ---")
print(df_port_dummy.head())
print("\n")

# --- 9. Dummy data for Land Logistics.csv (UNCHANGED) ---
num_land_routes_dummy = 150
land_origins = random.choices(dummy_dcs + all_cities_pool, k=num_land_routes_dummy)
land_destinations = random.choices(dummy_dcs + all_cities_pool, k=num_land_routes_dummy)
land_distances_km = np.random.uniform(10, 1000, num_land_routes_dummy)
land_cost_per_ton = np.random.uniform(0.08, 0.25, num_land_routes_dummy)
land_logistics_data = {
    'Origin': land_origins, 'Destination': land_destinations,
    'Distance (km)': land_distances_km, 'Cost/Ton': land_cost_per_ton
}
df_land_logistics_dummy = pd.DataFrame(land_logistics_data)
print("--- Dummy Land Logistics.csv (first 5 rows) ---")
print(df_land_logistics_dummy.head())
print("\n")

# --- 10. Dummy data for Ocean Freight.csv (UPDATED COLUMNS) ---
num_ocean_freight_rows = 50

ocean_dc_ids = random.choices(dummy_dcs, k=num_ocean_freight_rows) # DC where freight originates/is allocated
carrier_providers = random.choices(dummy_stps, k=num_ocean_freight_rows)
fixed_costs_ocean = np.random.uniform(1000, 5000, num_ocean_freight_rows)
variable_costs_ocean = np.random.uniform(500, 3000, num_ocean_freight_rows)
destination_cities_ocean = random.choices(all_cities_pool, k=num_ocean_freight_rows)
customer_codes_ocean = random.choices([f'OCUST{i:03d}' for i in range(50)], k=num_ocean_freight_rows)
customer_names_ocean = [f'Ocean Customer {i}' for i in range(num_ocean_freight_rows)]
types_ocean = random.choices(['Container', 'Bulk', 'LCL'], k=num_ocean_freight_rows)
volumes_ocean = np.random.uniform(10, 100, num_ocean_freight_rows)

ocean_freight_data_updated = {
    'DC ID': ocean_dc_ids,
    'Carrier Provider': carrier_providers,
    'Fixed Cost': fixed_costs_ocean,
    'Variable Cost': variable_costs_ocean,
    'Destination (City)': destination_cities_ocean,
    'Customer Code': customer_codes_ocean,
    'Customer Name': customer_names_ocean,
    'Type': types_ocean,
    'Volume': volumes_ocean
}
df_ocean_freight_dummy = pd.DataFrame(ocean_freight_data_updated)
print("--- Dummy Ocean Freight.csv (first 5 rows) ---")
print(df_ocean_freight_dummy.head())
print("\n")

# --- 11. Dummy data for Truck by STP (LTA).csv (UNCHANGED) ---
num_truck_stp_dummy = 100
stp_origins = random.choices(dummy_dcs + all_cities_pool, k=num_truck_stp_dummy)
stp_destinations = random.choices(dummy_dcs + all_cities_pool, k=num_truck_stp_dummy)
stp_vehicle_types = random.choices(vehicle_types_truck, k=num_truck_stp_dummy)
stp_cost_per_trip = np.random.uniform(100, 2000, num_truck_stp_dummy)
truck_stp_data = {
    'STP': random.choices(dummy_stps, k=num_truck_stp_dummy), 'Origin': stp_origins,
    'Destination': stp_destinations, 'Vehicle Type': stp_vehicle_types, 'Cost/Trip': stp_cost_per_trip
}
df_truck_stp_dummy = pd.DataFrame(truck_stp_data)
print("--- Dummy Truck by STP (LTA).csv (first 5 rows) ---")
print(df_truck_stp_dummy.head())
print("\n")

# --- 12. Dummy data for Resources.csv (UNCHANGED) ---
num_resources_dummy = 7
resource_types_list = ['Manpower (Warehouse)', 'Manpower (Drivers)', 'Warehouse Space (m2)', 'Forklifts', 'Pallet Racks (units)', 'IT Systems (licenses)', 'Office Space (m2)']
resource_units_list = ['person', 'person', 'm2', 'unit', 'unit', 'license', 'm2']
resources_data = {
    'Resource Type': random.sample(resource_types_list, k=num_resources_dummy),
    'Capacity': np.random.uniform(10, 1000, num_resources_dummy),
    'Unit': random.sample(resource_units_list, k=num_resources_dummy),
    'Cost/Unit': np.random.uniform(50, 10000, num_resources_dummy)
}
df_resources_dummy = pd.DataFrame(resources_data)
print("--- Dummy Resources.csv (first 5 rows) ---")
print(df_resources_dummy.head())
print("\n")

# --- 13. Dummy data for STP Performance.csv (UNCHANGED) ---
num_stp_perf_dummy = len(dummy_stps) * len(performance_metrics)
stp_perf_data = []
for stp in dummy_stps:
    for metric in performance_metrics:
        value = 0.9 + np.random.uniform(-0.05, 0.05) if 'Rate' in metric or 'Adherence' in metric else np.random.uniform(1, 10)
        if 'Damage Rate' in metric: value = np.random.uniform(0.01, 0.05)
        stp_perf_data.append({'STP': stp, 'Performance Metric': metric, 'Value': value})
df_stp_performance_dummy = pd.DataFrame(stp_perf_data)
print("--- Dummy STP Performance.csv (first 5 rows) ---")
print(df_stp_performance_dummy.head())
print("\n")

# --- 14. Dummy data for Spending (Topline).csv (UNCHANGED) ---
num_spending_dummy = 15
spending_categories = ['First Mile', 'Middle Mile', 'Last Mile', 'Warehousing', 'Customs & Duties', 'Overheads']
spending_years = [2023, 2024, 2025]
spending_regions = ['Kalimantan', 'Sulawesi', 'BaliNusra', 'Jawa', 'Sumatera', 'Overall']
spending_data = []
for _ in range(num_spending_dummy):
    category = random.choice(spending_categories)
    amount = np.random.uniform(100000, 5000000)
    year = random.choice(spending_years)
    region = random.choice(spending_regions)
    spending_data.append({'Category': category, 'Amount': amount, 'Year': year, 'Regional': region})
df_spending_topline_dummy = pd.DataFrame(spending_data)
print("--- Dummy Spending (Topline).csv (first 5 rows) ---")
print(df_spending_topline_dummy.head())
print("\n")

# --- 15. Dummy data for T&W Cost.csv (UNCHANGED) ---
num_tw_cost_dummy = 30
tw_cost_types = ['Fixed Warehouse Cost', 'Variable Warehouse Cost', 'Fixed Transportation Cost', 'Variable Transportation Cost']
tw_locations = dummy_dcs + all_cities_pool
tw_cost_data = []
for _ in range(num_tw_cost_dummy):
    location = random.choice(tw_locations)
    cost_type = random.choice(tw_cost_types)
    amount = np.random.uniform(5000, 500000)
    tw_cost_data.append({'Location': location, 'Cost Type': cost_type, 'Amount': amount})
df_tw_cost_dummy = pd.DataFrame(tw_cost_data)
print("--- Dummy T&W Cost.csv (first 5 rows) ---")
print(df_tw_cost_dummy.head())
print("\n")

# --- 16. Dummy data for ODS Cost.csv (UNCHANGED) ---
num_ods_cost_dummy = 150
ods_origins = random.choices(dummy_dcs + all_cities_pool, k=num_ods_cost_dummy)
ods_destinations = random.choices(dummy_dcs + all_cities_pool, k=num_ods_cost_dummy)
ods_shipment_types = random.choices(shipment_types, k=num_ods_cost_dummy)
ods_costs = np.random.uniform(50, 5000, num_ods_cost_dummy)
ods_cost_data = {
    'Origin': ods_origins, 'Destination': ods_destinations,
    'Shipment Type': ods_shipment_types, 'Cost': ods_costs
}
df_ods_cost_dummy = pd.DataFrame(ods_cost_data)
print("--- Dummy ODS Cost.csv (first 5 rows) ---")
print(df_ods_cost_dummy.head())
print("\n")

# --- 17. Dummy data for Population.csv (UNCHANGED) ---
num_population_dummy = len(all_cities_pool)
population_data = {
    'City': all_cities_pool,
    'Population': np.random.randint(50000, 10000000, num_population_dummy),
    'Growth Rate': np.random.uniform(-0.01, 0.03, num_population_dummy)
}
df_population_dummy = pd.DataFrame(population_data)
print("--- Dummy Population.csv (first 5 rows) ---")
print(df_population_dummy.head())
print("\n")

# --- 18. Dummy data for Dist Center.csv (UNCHANGED from previous, but shares logic with DC.csv) ---
# Note: This is similar to new 'Final.csv' (DC Master) and 'DC.csv', might be redundant if data is consolidated.
num_dist_center_dummy = len(dummy_dcs) + 1 # Include Karawang factory potentially

dist_center_names = ['Pabrik Karawang'] + dummy_dcs
dist_center_locations = []
for dc_id in dist_center_names:
    if dc_id == 'Pabrik Karawang':
        dist_center_locations.append('Karawang')
    else:
        zone = get_zone_from_location(dc_id)
        city_options = get_cities_in_zone(zone)
        dist_center_locations.append(random.choice(city_options) if city_options else random.choice(all_cities_pool))

dist_center_capacities = np.random.uniform(10000, 100000, num_dist_center_dummy)
dist_center_costs = np.random.uniform(50000, 1000000, num_dist_center_dummy)
dist_center_data = {
    'DC Name': dist_center_names, 'Location': dist_center_locations,
    'Capacity': dist_center_capacities, 'Cost': dist_center_costs
}
df_dist_center_dummy = pd.DataFrame(dist_center_data)
print("--- Dummy Dist Center.csv (first 5 rows) ---")
print(df_dist_center_dummy.head())
print("\n")

# --- 19. Dummy data for Middle Mile.csv (Updated with user's specified columns - re-included for completeness) ---
num_middle_mile_rows_dummy = 500

distributor_areas_mm = random.choices(dummy_dcs, k=num_middle_mile_rows_dummy)
origin_areas_mm = random.choices(dummy_dcs, k=num_middle_mile_rows_dummy)
destination_areas_mm = []
for i in range(num_middle_mile_rows_dummy):
    zone_for_dest = get_zone_from_location(distributor_areas_mm[i]) # Try to pick destination in same region as distributor
    city_options = get_cities_in_zone(zone_for_dest)
    destination_areas_mm.append(random.choice(city_options) if city_options else random.choice(all_cities_pool))

volumes_cs_mm = np.random.randint(100, 5000, num_middle_mile_rows_dummy)

middle_mile_distances_mm = []
middle_mile_costs_per_trip = []
base_cost_per_km_mm = 0.5 # USD/km as a base for middle mile truck

for i in range(num_middle_mile_rows_dummy):
    orig_lat, orig_long = get_coords(origin_areas_mm[i])
    dest_lat, dest_long = get_coords(destination_areas_mm[i])
    dist = haversine_distance(orig_lat, orig_long, dest_lat, dest_long)
    middle_mile_distances_mm.append(dist)
    middle_mile_costs_per_trip.append(dist * base_cost_per_km_mm * np.random.uniform(0.8, 1.2))

middle_mile_data_updated = {
    'Distributor Area': distributor_areas_mm, 'Origin Area': origin_areas_mm,
    'Origin Latitude': [get_coords(a)[0] for a in origin_areas_mm],
    'Longitude_x': [get_coords(a)[1] for a in origin_areas_mm],
    'Destination Area': destination_areas_mm,
    'Destination Latitude': [get_coords(a)[0] for a in destination_areas_mm],
    'Destination Longitude': [get_coords(a)[1] for a in destination_areas_mm],
    'Volume (CS)': volumes_cs_mm,
    'Distance (km)': middle_mile_distances_mm,
    'Cost/Trip': middle_mile_costs_per_trip
}
df_middle_mile_dummy_updated = pd.DataFrame(middle_mile_data_updated)

print("--- Dummy Middle Mile.csv (Updated Columns - first 5 rows) ---")
print(df_middle_mile_dummy_updated.head())
print("\n")


# --- CALIBRATION SCRIPT ---

target_regions = ['Kalimantan', 'Sulawesi', 'BaliNusra']
first_mile_target_cost = 600000  # USD
middle_mile_target_cost = 2000000 # USD

print("--- Starting Calibration ---")

# --- Calibrate First Mile Cost (now from df_ocean_freight_dummy) ---
df_ocean_freight_dummy['Total Cost'] = df_ocean_freight_dummy['Fixed Cost'] + df_ocean_freight_dummy['Variable Cost']

first_mile_ocean_df = df_ocean_freight_dummy[
    (df_ocean_freight_dummy['DC ID'].apply(get_zone_from_location).isin(['Jawa', 'Pabrik Karawang'])) & # Assuming origins from Jawa (Karawang)
    (df_ocean_freight_dummy['Destination (City)'].apply(get_zone_from_location).isin(target_regions))
].copy()

current_first_mile_cost = first_mile_ocean_df['Total Cost'].sum()
print(f"Current Dummy First Mile Cost (Target Regions - Ocean Freight): USD {current_first_mile_cost:,.2f}")

if current_first_mile_cost > 0:
    scaling_factor_first_mile = first_mile_target_cost / current_first_mile_cost
    print(f"Scaling factor for First Mile (Ocean Freight): {scaling_factor_first_mile:.2f}")

    df_ocean_freight_dummy.loc[first_mile_ocean_df.index, 'Fixed Cost'] *= scaling_factor_first_mile
    df_ocean_freight_dummy.loc[first_mile_ocean_df.index, 'Variable Cost'] *= scaling_factor_first_mile
    df_ocean_freight_dummy.loc[first_mile_ocean_df.index, 'Total Cost'] = \
        df_ocean_freight_dummy.loc[first_mile_ocean_df.index, 'Fixed Cost'] + \
        df_ocean_freight_dummy.loc[first_mile_ocean_df.index, 'Variable Cost']

calibrated_first_mile_cost = df_ocean_freight_dummy[df_ocean_freight_dummy.index.isin(first_mile_ocean_df.index)]['Total Cost'].sum()
print(f"Calibrated Dummy First Mile Cost (Target Regions - Ocean Freight): USD {calibrated_first_mile_cost:,.2f}")
print("\n")


# --- Calibrate Middle Mile Cost (from df_middle_mile_dummy_updated) ---
middle_mile_df = df_middle_mile_dummy_updated[
    (df_middle_mile_dummy_updated['Origin Area'].apply(get_zone_from_location).isin(target_regions)) |
    (df_middle_mile_dummy_updated['Destination Area'].apply(get_zone_from_location).isin(target_regions))
].copy()

current_middle_mile_cost = middle_mile_df['Cost/Trip'].sum()
print(f"Current Dummy Middle Mile Cost (Target Regions): USD {current_middle_mile_cost:,.2f}")

if current_middle_mile_cost > 0:
    scaling_factor_middle_mile = middle_mile_target_cost / current_middle_mile_cost
    print(f"Scaling factor for Middle Mile: {scaling_factor_middle_mile:.2f}")

    df_middle_mile_dummy_updated.loc[middle_mile_df.index, 'Cost/Trip'] *= scaling_factor_middle_mile

calibrated_middle_mile_cost = df_middle_mile_dummy_updated[df_middle_mile_dummy_updated.index.isin(middle_mile_df.index)]['Cost/Trip'].sum()
print(f"Calibrated Dummy Middle Mile Cost (Target Regions): USD {calibrated_middle_mile_cost:,.2f}")
print("\n--- Calibration Complete ---")


# --- Instructions for saving to CSV ---
print("\nUntuk menyimpan DataFrame ini ke file CSV di komputer Anda, tambahkan baris berikut setelah setiap DataFrame dibuat (di lingkungan Python lokal Anda):")
print("\n# Contoh menyimpan df_customer_final_dummy")
print("df_customer_final_dummy.to_csv('dummy_customer_final.csv', index=False)")
print("\n# Dan seterusnya untuk setiap DataFrame yang telah dibuat...")

# Setelah membuat df_customer_final_dummy
df_customer_final_dummy.to_csv('dummy_customer_final.csv', index=False)

# Setelah membuat df_dc_final_dummy
df_dc_final_dummy.to_csv('dummy_dc_final.csv', index=False)

# Setelah membuat df_final_dummy
df_final_dummy.to_csv('dummy_final.csv', index=False)

# Setelah membuat df_ocean_freight_dummy
df_ocean_freight_dummy.to_csv('dummy_ocean_freight.csv', index=False)

# Setelah membuat df_middle_mile_dummy_updated (nama dataframe yang diperbarui)
df_middle_mile_dummy_updated.to_csv('dummy_middle_mile.csv', index=False)