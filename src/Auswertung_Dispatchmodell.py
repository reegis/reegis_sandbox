import pandas as pd
from matplotlib import pyplot as plt
import os
import numpy as np
from my_reegis import results, upstream_analysis, reegis_plot

# getting path to data from IFAM owncloud
def load_agora_from_owncloud(path_to_data='ownCloud/FhG-owncloud-Quarree-AB3/Daten/Agora/', year=2014):

    # selecting spreadsheet
    filename = os.path.join(
        os.path.expanduser("~"), path_to_data, '2019-04-04_Agorameter_v8.1.xlsx')

    data = pd.read_excel(filename, sheet_name=str(year), header=6)
    data.drop(labels=['Year','Month','Day','Hour'], axis=1, inplace=True)
    data.set_index("Date/Time", inplace=True)

    # taking into account exports for generation
    load2014 = data["Consumption"]
    exportsaldo = data["Exportsaldo"]
    demand_eff = load2014+exportsaldo
    p_spot_agora = data["Day-Ahead Spot"]
    em_factor_agora = data["Emission factor g/kWh"]

    gen_technologies=['Biomass', 'Hydro', 'Wind', 'PV', 'Nuclear', 'Lignite', 'Hard Coal', 'Natural Gas', 'Pump', 'Others']
    generation = data[gen_technologies]

    return generation, p_spot_agora, em_factor_agora

# Prepare deflex data accordingly
def prepare_deflex_for_comparison(path_to_results):
    # Load energy system from results
    de_dispatch = results.load_es(path_to_results)
    results_obj = de_dispatch.results['main']

    # Auswertung
    cost_em = upstream_analysis.get_emissions_and_costs(de_dispatch,with_chp=True)
    vlh = results.fullloadhours(de_dispatch)
    mrbb = results.get_multiregion_bus_balance(de_dispatch)

    # Extrahiere relevante Größen
    demand = mrbb.DE01['out']['demand']['electricity']['all']
    transformer = mrbb.DE01['in']['trsf']
    generation = pd.DataFrame(index=transformer.index)
    ee_single =  mrbb.DE01['in']['source']['ee']
    generation["Biomass"] = transformer["pp"]["bioenergy"] + transformer["chp"]["bioenergy"]
    generation["Wind"] = ee_single["wind"] + mrbb.DE02['in']['source']['ee']['wind']
    generation["Hydro"] = ee_single["hydro"]
    generation["PV"] = ee_single["solar"]
    #generation["Nuclear"] = transformer["pp"]["nuclear"]
    generation["Nuclear"] = mrbb.DE01['in']['source']['ee']['geothermal']
    generation["Hard Coal"]=transformer["chp"]["hard_coal"]+transformer["pp"]["hard_coal"]
    generation["Lignite"]=transformer["chp"]["lignite"]+transformer["pp"]["lignite"]
    generation["Natural Gas"]=transformer["chp"]["natural_gas"]+transformer["pp"]["natural_gas"]
    generation["Others"]=transformer["chp"]["other"]+transformer["pp"]["other"] + transformer["chp"]["oil"] + \
                         transformer["pp"]["oil"] + mrbb.DE01['in']['source']['ee']['geothermal']
    generation["Pump"] = mrbb.DE01["out"]["storage"]

    return generation

# Plot des Emissionsfaktors und Preises
def plot_em_p(p_spot, em_factor):
    fig = plt.figure(1)
    ax1 = fig.add_subplot(111)
    line1 = ax1.plot(p_spot, label='Maket Clearing Price'), plt.legend(loc='upper right'), plt.ylabel('MCP in €/MWh')
    ax2 = ax1.twinx()
    line2 = ax2.plot(em_factor, 'y', label='Emissionsfaktor'), plt.legend(loc='upper left'), plt.ylabel('Emissionsfaktor in  kg CO2/kWh')
    plt.title('Emissionsfaktor und Preissignal')
    plt.show()

# Plot der Jahresenergiemengen im Vergleich
def compare_energy(energy_agora, energy_deflex):
    # Input data has to be pd.Series with identical index
    bar = pd.DataFrame()
    bar["agora"] = energy_agora
    bar["deflex"] = energy_deflex

    ## Barplot
    labels = list(energy_agora.index)
    x = np.arange(len(labels))

    fig, ax = plt.subplots()
    rects1= ax.bar(x - 0.35/2, bar["agora"].values, 0.35, label='agora')
    rects2= ax.bar(x + 0.35/2, bar["deflex"], 0.35, label='deflex')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, size=16)
    ax.legend(loc='upper left', fontsize=16)

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = round(rect.get_height())
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', weight='bold')

    autolabel(rects1)
    autolabel(rects2)

    plt.ylabel('Jahresenergie in TWh', size=16)
    plt.title('Vergleich historischer Dispatch mit deflex')


# Provide paths to sources
path_to_data = 'ownCloud/FhG-owncloud-Quarree-AB3/Daten/Agora/'
path_to_results = '/home/dbeier/reegis/scenarios/deflex/2014/results_cbc/NEP2030.esys'

# Fetch Agora Dispatch data from XLS
generation_agora, p_spot_agora, em_factor_agora = load_agora_from_owncloud(path_to_data='ownCloud/FhG-owncloud-Quarree-AB3/Daten/Agora/')

# Get deflex data
generation_deflex = prepare_deflex_for_comparison(path_to_results)

# Plot energy sums
energy_agora = generation_agora.sum() / 1000000  # In TWh
energy_deflex = generation_deflex.sum() / 1000000  # create dummy value for testing purposes
bar = pd.DataFrame()
bar["agora"]=energy_agora
bar["deflex"]=energy_deflex
compare_energy(energy_agora, energy_deflex)

# Plot emission factor and market price
plot_em_p(p_spot_agora, em_factor_agora)

