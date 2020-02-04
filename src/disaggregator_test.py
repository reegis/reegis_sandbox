import os
from disaggregator import config, data
from reegis import geometries as geo, config as rconfig, demand_elec, demand_heat

nuts_geo_fn = os.path.join(
    rconfig.get('paths', 'geometry'),
    'NUTS_RG_03M_2016_4326_LEVL_3_DE.geojson'
)

nuts_geo = geo.load(fullname=nuts_geo_fn)
nuts_geo.set_index('id', drop=True, inplace=True)
fed_states = geo.get_federal_states_polygon()

nuts_geo = geo.spatial_join_with_buffer(nuts_geo.centroid, fed_states, 'fs')
fed_states['nuts'] = '0'
for state in fed_states.index:
    fed_states.loc[state, 'nuts'] = list(nuts_geo.loc[nuts_geo['fs'] == state].index)

cfg = config.get_config()
dict_nuts3_name = config.region_id_to_nuts3(nuts3_to_name=True)
df_spatial = data.database_description('spatial')
df_temporal = data.database_description('temporal')
elc_consumption_hh_spat = data.elc_consumption_HH_spatial()
elc_consumption_hh_spattemp = data.elc_consumption_HH_spatiotemporal()

print(elc_consumption_hh_spattemp[fed_states.loc['BB', 'nuts']])
print(elc_consumption_hh_spattemp[fed_states.loc['HH', 'nuts']])

# Testing Disaggregator reegis functions
fed_states_nuts = fed_states.loc['BY', 'nuts']
demand_elec.get_household_powerload_by_NUTS3_profile(2014, fed_states_nuts, method='SLP')
demand_heat.get_househould_heat_demand_by_NUTS3(2014, fed_states_nuts, by='buildings', weight_by_income=False)