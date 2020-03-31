from reegis import powerplants, opsd
from deflex import basic_scenario, geometries
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

#KW_list_prepared = opsd.prepare_opsd_file(category="conventional", prepared_file_name='KW_test.csv', overwrite=False)

pp_reegis = powerplants.get_reegis_powerplants(
    2018, path=None, filename=None, pp=None, overwrite_capacity=False
)

# Kleine Kraftwerke filtern, um MO nicht zu überfrachten und weil wahrscheinlich nicht preisbildend
isgreater100MW = pp_reegis['capacity_in'] >= 100
pp_reegis_100MW = pp_reegis[isgreater100MW]
# Konventionelle Kraftwerke extrahieren
isfossil = pp_reegis_100MW["energy_source_level_1"] == "Fossil fuels"
isnuclear = pp_reegis_100MW["energy_source_level_1"] == "Nuclear"

fossil = pp_reegis_100MW[isfossil]
nuclear = pp_reegis_100MW[isnuclear]
conventional = pd.concat([fossil, nuclear])

# CHPs für MO ausschließen
#isnotchp = conventional["chp"] == "no"
#pp_MO = conventional[isnotchp]

pp_MO = conventional

# Relevante Spalten extrahieren
sel_MO = pd.DataFrame({'capacity':pp_MO.capacity, 'efficiency':pp_MO.efficiency,
                       'energy_source_level_2':pp_MO.energy_source_level_2 })

# Grenzkosten berechnen
# Kostenannahmen von EWI ( https://www.ewi.uni-koeln.de/de/news/ewi-merit-order-tool-2019/ )
cost_ETS = 25 # 25 €/tCO2 (aktueller Wert)
cost_hc = 11.28; cost_lignite = 3.1; cost_gas = 22.78; cost_oil = 33; cost_nuclear = 5.5 #
em_hc = 0.336; em_lignite = 0.378; em_gas = 0.202; em_oil=0.263; em_nuclear = 0

cost_hc = cost_hc + em_hc*cost_ETS
cost_lignite = cost_lignite + em_lignite*cost_ETS
cost_gas = cost_gas + em_gas*cost_ETS
cost_oil = cost_oil + em_oil*cost_ETS

# Zuordnung von Brennstoffkosten zu Kraftwerken
idx = sel_MO.index
fuel_cost = pd.Series(index=idx)

for n in range(0, len(sel_MO)):
    if sel_MO.iloc[n]["energy_source_level_2"] == "Hard coal":
        fuel_cost.iloc[n] = cost_hc

    elif sel_MO.iloc[n]["energy_source_level_2"] == "Lignite":
        fuel_cost.iloc[n] = cost_lignite

    elif sel_MO.iloc[n]["energy_source_level_2"] == "Natural gas":
        fuel_cost.iloc[n] = cost_gas

    elif sel_MO.iloc[n]["energy_source_level_2"] == "Oil":
        fuel_cost.iloc[n] = cost_oil

    elif sel_MO.iloc[n]["energy_source_level_2"] == "Nuclear":
        fuel_cost.iloc[n] = cost_nuclear

sel_MO["fuel_cost"]=fuel_cost
# Berechnung der Grenzkosten (Nur Brennstoff)
sel_MO["marginal_cost"] = sel_MO.fuel_cost / sel_MO.efficiency
# Sortierung der Kraftwerksliste nach Kosten
sort_MO = sel_MO.sort_values(axis=0, by=['marginal_cost'])


# Vermutlich sehr umständliche Vorbereitung eines Merit Order Plots
MO = pd.DataFrame(np.zeros(int(round(sort_MO.capacity.sum()))))
MO["technology"]='n/a'
temp = 0

for n in range(0, len(sel_MO.index)):

    MW = int(sort_MO.capacity.iloc[n])
    MO.iloc[temp:temp+MW,0] = sort_MO.iloc[n]["marginal_cost"]
    MO.iloc[temp:temp + MW, 1] = sort_MO.iloc[n]["energy_source_level_2"]
    temp = temp + MW

# Plot Merit Order
x=np.arange(0,int(round(sort_MO.capacity.sum())))
y=MO[0].values

colors = []
energy = MO["technology"].tolist()
for item in energy:
    if item == "Nuclear":
        color = "#DDF45B"
    if item == "Hard coal":
        color = "#141115"
    if item == "Lignite":
        color = "#8D6346"
    if item == "Natural gas":
        color = "#4C2B36"
    if item == "Oil":
        color = "#C1A5A9"
    colors.append(color)

plt.bar(x, y, color=colors, width=1)
plt.title("Merit-Order des europäischen Kraftwerkparks")
plt.xlabel('Kummulierte Leistung in MW')
plt.ylabel('Grenzkosten in €/MWh')
