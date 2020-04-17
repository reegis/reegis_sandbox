import glaes as gl
from glaes import Priors as pr

region = '/home/dbeier/git-projects/reegis/reegis/data/geometries/germany_polygon.geojson'
regionPath = '/home/dbeier/git-projects/glaes/glaes/test/data/aachenShapefile.shp' #['aachenShapefile.shp']
typ_excl=gl.ExclusionCalculator.typicalExclusions

# Choose Region
ec = gl.ExclusionCalculator(region, srs=3035, pixelSize=100)

# Exclude ares close to settlements
ec.excludePrior(pr.settlement_proximity, value=(None, 500)) # 500 m Abstand zu Siedlungen
ec.excludePrior(pr.settlement_urban_proximity, value=(None, 1000)) # 1000m Abstand zu Städten
# Exclude areas close to agriculture
ec.excludePrior(pr.agriculture_arable_proximity, value=(None, 0)) # Ackerfläche wird ausgeschlossen (Im Gegensatz zu Grünland)
# Wirtschaftsbetriebe
ec.excludePrior(pr.industrial_proximity, value=(None, 50))
ec.excludePrior(pr.mining_proximity, value=(None, 50))
ec.excludePrior(pr.camping_proximity, value=(None, 50))
# Infrastruktur
ec.excludePrior(pr.airfield_proximity, value=(None, 3000))
ec.excludePrior(pr.airport_proximity, value=(None, 5000))
ec.excludePrior(pr.power_line_proximity, value=(None, 50))
ec.excludePrior(pr.railway_proximity, value=(None, 50))
ec.excludePrior(pr.roads_main_proximity, value=(None, 50))
ec.excludePrior(pr.roads_proximity, value=(None, 50))
ec.excludePrior(pr.roads_secondary_proximity, value=(None, 50))
# Ungeeignete Standorte
ec.excludePrior(pr.elevation_threshold, value=(1800, None))
ec.excludePrior(pr.lake_proximity, value=(None, 300))
ec.excludePrior(pr.river_proximity, value=(None, 200))
ec.excludePrior(pr.waterbody_proximity, value=(None, 300))
# Naturschutz
ec.excludePrior(pr.leisure_proximity, value=(None, 1000))
ec.excludePrior(pr.protected_biosphere_proximity, value=(None, 300))
ec.excludePrior(pr.protected_bird_proximity, value=(None, 300))
ec.excludePrior(pr.protected_habitat_proximity, value=(None, 300))
ec.excludePrior(pr.protected_landscape_proximity, value=(None, 300))
ec.excludePrior(pr.protected_natural_monument_proximity, value=(None, 300))
ec.excludePrior(pr.protected_park_proximity, value=(None, 300))
ec.excludePrior(pr.protected_reserve_proximity, value=(None, 300))
ec.excludePrior(pr.protected_wilderness_proximity, value=(None, 300))

ec.draw()

