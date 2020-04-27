import pandas as pd
from matplotlib import pyplot as plt
import os
import numpy as np
from my_reegis import results, upstream_analysis

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
    generation["Nuclear"] = transformer["pp"]["nuclear"]
    #generation["Nuclear"] = mrbb.DE01['in']['source']['ee']['geothermal']
    generation["Hard Coal"]=transformer["chp"]["hard_coal"]+transformer["pp"]["hard_coal"]
    generation["Lignite"]=transformer["chp"]["lignite"]+transformer["pp"]["lignite"]
    generation["Natural Gas"]=transformer["chp"]["natural_gas"]+transformer["pp"]["natural_gas"]
    generation["Others"]=transformer["chp"]["other"]+transformer["pp"]["other"] + transformer["chp"]["oil"] + \
                         transformer["pp"]["oil"] + mrbb.DE01['in']['source']['ee']['geothermal']
    generation["Pump"] = mrbb.DE01["out"]["storage"]

    # Emissionszeitreihe
    em_per_technology = results.fetch_cost_emission(de_dispatch, with_chp=True)
    em_mix = pd.DataFrame()
    em_mix["hardcoal_chp"] = transformer["chp"]["hard_coal"] * em_per_technology["emission"]["hard_coal"]["DE01"]["chp"]
    em_mix["hardcoal_pp"] = transformer["pp"]["hard_coal"] * em_per_technology["emission"]["hard_coal"]["DE01"]["pp"]
    em_mix["lignite_chp"] = transformer["chp"]["lignite"] * em_per_technology["emission"]["lignite"]["DE01"]["chp"]
    em_mix["lignite_pp"] = transformer["pp"]["lignite"] * em_per_technology["emission"]["lignite"]["DE01"]["pp"]
    em_mix["natural_gas_chp"] = transformer["chp"]["natural_gas"] * \
                                em_per_technology["emission"]["natural_gas"]["DE01"]["chp"]
    em_mix["natural_gas_pp"] = transformer["pp"]["natural_gas"] * em_per_technology["emission"]["natural_gas"]["DE01"][
        "pp"]
    em_mix["oil_chp"] = transformer["chp"]["oil"] * em_per_technology["emission"]["oil"]["DE01"]["chp"]
    em_mix["oil_pp"] = transformer["pp"]["oil"] * em_per_technology["emission"]["oil"]["DE01"]["pp"]
    em_mix["other_chp"] = transformer["chp"]["other"] * em_per_technology["emission"]["other"]["DE01"]["chp"]
    em_mix["other_pp"] = transformer["pp"]["other"] * em_per_technology["emission"]["other"]["DE01"]["pp"]

    em_factor_deflex = em_mix.sum(axis=1) / demand
    p_spot_deflex = cost_em["mcp"]

    return generation, p_spot_deflex, em_factor_deflex


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


# Plot der monatlichen Emissionen
def plot_em_per_month():
    monate_dict = {1: 'jan',2:'feb',3:'mar',4:'apr',5:'mai',6:'jun',7:'jul',8:'aug',9:'sep',10:'oct',11:'nov',12:'dez'}
    dt = generation_deflex.index

    for i in monate_dict.keys():
        tmp = dt.month == i
        monate_dict[i]=tmp

    em_factor_month = pd.DataFrame()
    em_factor_month["agora"]=np.zeros(12)
    em_factor_month["deflex"]=np.zeros(12)

    for i in range(1,13):
        em_factor_month["agora"].iloc[i-1] = em_factor_agora[monate_dict[i]].mean()
        em_factor_month["deflex"].iloc[i - 1] = em_factor_deflex[monate_dict[i]].mean()

    labels = ['jan','feb','mar','apr','mai','jun','jul','aug','sep','oct','nov','dez']
    x = np.arange(len(labels))

    fig, ax = plt.subplots()
    rects1= ax.bar(x - 0.35/2, em_factor_month["agora"].values, 0.35, label='agora')
    rects2= ax.bar(x + 0.35/2, em_factor_month["deflex"].values, 0.35, label='deflex')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, size=16)
    ax.legend(loc='upper center', fontsize=16)


# Plot der monatlichen Durchschnittspreise
def plot_price_per_month():
    monate_dict = {1: 'jan',2:'feb',3:'mar',4:'apr',5:'mai',6:'jun',7:'jul',8:'aug',9:'sep',10:'oct',11:'nov',12:'dez'}
    dt = generation_deflex.index

    for i in monate_dict.keys():
        tmp = dt.month == i
        monate_dict[i]=tmp

    price_month = pd.DataFrame()
    price_month["agora"]=np.zeros(12)
    price_month["deflex"]=np.zeros(12)

    for i in range(1,13):
        price_month["agora"].iloc[i-1] = p_spot_agora[monate_dict[i]].mean()
        price_month["deflex"].iloc[i - 1] = p_spot_deflex[monate_dict[i]].mean()

    labels = ['jan','feb','mar','apr','mai','jun','jul','aug','sep','oct','nov','dez']
    x = np.arange(len(labels))

    fig, ax = plt.subplots()
    rects1= ax.bar(x - 0.35/2, price_month["agora"].values, 0.35, label='agora')
    rects2= ax.bar(x + 0.35/2, price_month["deflex"].values, 0.35, label='deflex')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, size=16)
    ax.legend(loc='upper center', fontsize=16)


# Plot der Abweichung des Emissionsfaktors
def plot_em_diff(em1=em_factor_agora, em2=em_factor_deflex):
    diff = em1-em2
    plt.figure(1), plt.clf()
    plt.plot(em_factor_agora, label='Agora')
    plt.plot(em_factor_deflex, label='deflex')
    plt.plot(diff, "--", label='Differenz')
    plt.legend()
    plt.ylabel('Emissionsfaktor in g/kWh')
    plt.title('Vergleich des deflex-Emissionsfaktors mit historischen Werten')




# Provide paths to sources
path_to_data = 'ownCloud/FhG-owncloud-Quarree-AB3/Daten/Agora/'
path_to_NEP = '/home/dbeier/reegis/scenarios/deflex/2014/results_cbc/NEP2030.esys'
path_to_de02_2014 = '/home/dbeier/reegis/scenarios/deflex/2014/results_cbc/de02.esys'

# Fetch Agora Dispatch data from XLS
generation_agora, p_spot_agora, em_factor_agora = load_agora_from_owncloud(path_to_data)

# Get deflex data
generation_deflex, p_spot_deflex, em_factor_deflex = prepare_deflex_for_comparison(path_to_de02_2014)

# Plot energy sums
energy_agora = generation_agora.sum() / 1000000  # in TWh
energy_deflex = generation_deflex.sum() / 1000000  # in TWh
compare_energy(energy_agora, energy_deflex)

# Plot emission factor and market price
plot_em_p(p_spot_agora, em_factor_agora)

# Plot monthly emission factors
plot_em_per_month()

# Plot monthly spot prices
plot_price_per_month()

# Plot emission factor deviation
plot_em_diff(em1=em_factor_agora, em2=em_factor_deflex)
