import glaes as gl
from glaes import Priors as pr
import pandas as pd
from reegis import geometries as geom

DE = '/home/dbeier/git-projects/reegis/reegis/data/geometries/germany_polygon.geojson'
BB = '/home/dbeier/Downloads/BB_shapes/Brandenburg-Landkreise.shp'
#BE = '/home/dbeier/Downloads/BB_shapes/bezirksgrenzen.geojson'

region = BB


def calculate_wind_sites(region, invert=False, separation=700, name='NoRegion', convert2epsg=True):
        # Choose Region
        ecWind = gl.ExclusionCalculator(region, srs=3035, pixelSize=100, limitOne=False)

        # Define Exclusion Criteria
        selExlWind = {
                "access_distance": (5000, None ),
                #"agriculture_proximity": (None, 50 ),
                #"agriculture_arable_proximity": (None, 50 ),
                #"agriculture_pasture_proximity": (None, 50 ),
                #"agriculture_permanent_crop_proximity": (None, 50 ),
                #"agriculture_heterogeneous_proximity": (None, 50 ),
                "airfield_proximity": (None, 1760 ),    # Diss WB
                "airport_proximity": (None, 5000 ),     # Diss WB
                "connection_distance": (10000, None ),
                #"dni_threshold": (None, 3.0 ),
                "elevation_threshold": (1500, None ),
                #"ghi_threshold": (None, 3.0 ),
                "industrial_proximity": (None, 250 ),  # Diss Wingenbach / UBA 2013
                "lake_proximity": (None, 0 ),
                "mining_proximity": (None, 100 ),
                "ocean_proximity": (None, 10 ),
                "power_line_proximity": (None, 120 ),   # Diss WB
                "protected_biosphere_proximity": (None, 5 ), # UBA 2013
                "protected_bird_proximity": (None, 200 ), # UBA 2013
                "protected_habitat_proximity": (None, 5 ), # UBA 2013
                "protected_landscape_proximity": (None, 5 ), # UBA 2013
                "protected_natural_monument_proximity": (None, 200 ), # UBA 2013
                "protected_park_proximity": (None, 5 ), # UBA 2013
                "protected_reserve_proximity": (None, 200 ), # UBA 2013
                "protected_wilderness_proximity": (None, 200 ), # UBA 2013
                "camping_proximity": (None, 900),       # UBA 2013)
                #"touristic_proximity": (None, 800),
                #"leisure_proximity": (None, 1000),
                "railway_proximity": (None, 250 ),      # Diss WB
                "river_proximity": (None, 5 ),        # Abweichung vom standardwert (200)
                "roads_proximity": (None, 80 ),         # Diss WB
                "roads_main_proximity": (None, 80 ),    # Diss WB
                "roads_secondary_proximity": (None, 80 ),# Diss WB
                #"sand_proximity": (None, 5 ),
                "settlement_proximity": (None, 600 ),   # Diss WB
                "settlement_urban_proximity": (None, 1000 ),
                "slope_threshold": (10, None ),
                #"slope_north_facing_threshold": (3, None ),
                "wetland_proximity": (None, 5 ), # Diss WB / UBA 2013
                "waterbody_proximity": (None, 5 ), # Diss WB / UBA 2013
                "windspeed_100m_threshold": (None, 4.5 ),
                "windspeed_50m_threshold": (None, 4.5 ),
                "woodland_proximity": (None, 0 ),     # Abweichung vom standardwert (300) / Diss WB
                "woodland_coniferous_proximity": (None, 0 ), # Abweichung vom standardwert (300)
                "woodland_deciduous_proximity": (None, 0 ), # Abweichung vom standardwert (300)
                "woodland_mixed_proximity": (None, 0 ) # Abweichung vom standardwert (300)
                }

        # Apply selected exclusion criteria
        for key in selExlWind:
            ecWind.excludePrior(pr[key], value=ecWind.typicalExclusions[key])

        # Placement Algorithm
        ecWind.distributeItems(separation=separation, outputSRS=4326)

        # Extract and convert site coords of turbines
        site_coords = pd.DataFrame(ecWind.itemCoords)
        site_coords.columns = ['latitude','longitude']
        site_coords_gdf = geom.create_geo_df(site_coords, wkt_column=None, lon_column="longitude", lat_column='latitude')

        # Convert2epsg for plotting purposes
        if convert2epsg==True:
                trsf= site_coords_gdf["geometry"]
                site_coords_gdf_epsg3857 = trsf.to_crs(epsg=3857)

                # Save coords in EPSG3587 to hard disk
                site_coords_gdf_epsg3857.to_file("site_coordsWind_epsg3857_" + name + ".geojson", driver='GeoJSON')
                site_coords_gdf.to_file("site_coordsWind_WGS84_" + name + ".geojson", driver='GeoJSON')

        elif convert2epsg==False:
                site_coords_gdf.to_file("site_coordsWind_WGS84_" + name + ".geojson", driver='GeoJSON')

        # Write turbines to power plants df
        res_df_Wind = pd.DataFrame(columns=["energy_source_level_1", "energy_source_level_2", "technology",
                                "electrical_capacity", "lon", "lat", "data_source"])

        res_df_Wind["lon"] = site_coords["latitude"]
        res_df_Wind["lat"] = site_coords["longitude"]
        res_df_Wind["energy_source_level_1"] = 'Renewable energy'
        res_df_Wind["energy_source_level_2"] = 'Wind'
        res_df_Wind["technology"] = 'Onshore'
        res_df_Wind["electrical_capacity"] = 3.5
        res_df_Wind["data_source"] = 'GLAES'

        return res_df_Wind, ecWind


def calculate_PV_sites(region, invert=True, separation=1000, name='NoRegion', convert2epsg=True):
        # Choose Region
        ecPV = gl.ExclusionCalculator(region, srs=3035, pixelSize=100, limitOne=False)

        # Apply selected exclusion criteria
        ecPV.excludePrior(pr.settlement_proximity, value=None)
        ecPV.excludePrior(pr.settlement_urban_proximity, value=None)
        ecPV.excludePrior(pr.industrial_proximity, value=None)

        # Placement Algorithm
        ecPV.distributeItems(separation=1000, invert=invert, outputSRS=4326)

        # Extract and convert site coords of turbines
        site_coords = pd.DataFrame(ecPV.itemCoords)
        site_coords.columns = ['latitude','longitude']
        site_coords_gdf = geom.create_geo_df(site_coords, wkt_column=None, lon_column="longitude", lat_column='latitude')

        # Convert2epsg for plotting purposes
        if convert2epsg==True:
                trsf= site_coords_gdf["geometry"]
                site_coords_gdf_epsg3857 = trsf.to_crs(epsg=3857)

                # Save coords in EPSG3587 to hard disk
                site_coords_gdf_epsg3857.to_file("site_coordsPV_epsg3857_" + name + ".geojson", driver='GeoJSON')
                site_coords_gdf.to_file("site_coordsPV_WGS84_" + name + ".geojson", driver='GeoJSON')
        elif convert2epsg==False:
                site_coords_gdf.to_file("site_coordsPV_WGS84_" + name + ".geojson", driver='GeoJSON')

        # Calculate Power per Site in MW
        p_mean = 300000 / len(site_coords) #Total possible PV-Power in MW divided by site count

        # Write turbines to power plants df
        res_df_PV = pd.DataFrame(columns=["energy_source_level_1", "energy_source_level_2", "technology",
                                "electrical_capacity", "lon", "lat", "data_source"])

        res_df_PV["lon"] = site_coords["latitude"]
        res_df_PV["lat"] = site_coords["longitude"]
        res_df_PV["energy_source_level_1"] = 'Renewable energy'
        res_df_PV["energy_source_level_2"] = 'Solar'
        res_df_PV["technology"] = 'Photovoltaics'
        res_df_PV["electrical_capacity"] = p_mean
        res_df_PV["data_source"] = 'GLAES'

        return res_df_PV, ecPV


calculate_wind_sites(BB, invert=False, separation=500, name='BB', convert2epsg=True)
calculate_PV_sites(BB, invert=True, separation=1000, name='BB', convert2epsg=True)









# PV-Freiflächenpotenzial nach Wingenbach / UBA 2013
selExlPV = {
        "access_distance": (5000, None ),
        #"agriculture_proximity": (None, 50 ),
        "agriculture_arable_proximity": (None, 50 ),
        #"agriculture_pasture_proximity": (None, 50 ),
        #"agriculture_permanent_crop_proximity": (None, 50 ),
        #"agriculture_heterogeneous_proximity": (None, 50 ),
        "airfield_proximity": (None, 5 ),    # Diss WB
        "airport_proximity": (None, 5 ),     # Diss WB
        "connection_distance": (10000, None ),
        "dni_threshold": (None, 3.0 ),
        "elevation_threshold": (1500, None ),
        #"ghi_threshold": (None, 3.0 ),
        "industrial_proximity": (None, 0 ),  # Diss Wingenbach / UBA 2013
        "lake_proximity": (None, 5 ),
        "mining_proximity": (None, 100 ),
        "ocean_proximity": (None, 10 ),
        "power_line_proximity": (None, 120 ),   # Diss WB
        "protected_biosphere_proximity": (None, 5 ), # UBA 2013
        "protected_bird_proximity": (None, 5 ), # UBA 2013
        "protected_habitat_proximity": (None, 5 ), # UBA 2013
        "protected_landscape_proximity": (None, 5 ), # UBA 2013
        "protected_natural_monument_proximity": (None, 5 ), # UBA 2013
        "protected_park_proximity": (None, 5 ), # UBA 2013
        "protected_reserve_proximity": (None, 5 ), # UBA 2013
        "protected_wilderness_proximity": (None, 5 ), # UBA 2013
        "camping_proximity": (None, 500),       # UBA 2013)
        #"touristic_proximity": (None, 800),
        #"leisure_proximity": (None, 1000),
        "railway_proximity": (None, 5 ),      # Diss WB
        "river_proximity": (None, 5 ),        # Abweichung vom standardwert (200)
        "roads_proximity": (None, 80 ),         # Diss WB
        "roads_main_proximity": (None, 80 ),    # Diss WB
        "roads_secondary_proximity": (None, 80 ),# Diss WB
        #"sand_proximity": (None, 5 ),
        "settlement_proximity": (None, 600 ),   # Diss WB
        "settlement_urban_proximity": (None, 1000 ),
        #"slope_threshold": (10, None ),
        "slope_north_facing_threshold": (3, None ),
        "wetland_proximity": (None, 5 ), # Diss WB / UBA 2013
        "waterbody_proximity": (None, 5 ), # Diss WB / UBA 2013
        #"windspeed_100m_threshold": (None, 4.5 ),
        #"windspeed_50m_threshold": (None, 4.5 ),
        "woodland_proximity": (None, 0 ),     # Abweichung vom standardwert (300) / Diss WB
        "woodland_coniferous_proximity": (None, 0 ), # Abweichung vom standardwert (300)
        "woodland_deciduous_proximity": (None, 0 ), # Abweichung vom standardwert (300)
        "woodland_mixed_proximity": (None, 0 ) # Abweichung vom standardwert (300)
        }

