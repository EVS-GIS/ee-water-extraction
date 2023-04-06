import ee


def calculateCloudScore(image, dgo_shape, scale=30):
    
    cloud_mask = image.unmask().select('CLOUDS').eq(0)
    
    cloudy_size = cloud_mask.reduceRegion(
        reducer = ee.Reducer.sum(),
        geometry = dgo_shape.geometry(),
        scale = scale
    ).getNumber('CLOUDS')
    
    full_size = cloud_mask.reduceRegion(
        reducer = ee.Reducer.count(),
        geometry = dgo_shape.geometry(),
        scale = scale
    ).getNumber('CLOUDS')
    
    cloud_score = cloudy_size.divide(full_size).multiply(100)

    return cloud_score


def calculateCoverage(image, dgo_shape, scale=30):
    # Calculate how much an image cover a DGO
    
    unmasked = image.unmask(1)
    
    total_pixels = unmasked.reduceRegion(
        reducer = ee.Reducer.count(),
        geometry = dgo_shape.geometry(),
        scale = scale,
        maxPixels = 1e13
    ).getNumber('red')
    
    act_pixels = image.reduceRegion(
        reducer = ee.Reducer.count(),
        geometry = dgo_shape.geometry(),
        scale = scale,
        maxPixels = 1e13
    ).getNumber('red')
    
    coverage_score = act_pixels.divide(total_pixels).multiply(100).round()

    return coverage_score


def calculateWaterMetrics(image, dgo, scale=30, simplify_tolerance=1.5):
    # Vectorisation des surfaces
    water = image.select('WATER').reduceToVectors(
        geometry = dgo.geometry(),
        scale = scale,
        eightConnected = True,
        maxPixels = 1e12,
        geometryType = 'polygon')
    
    # Séparer les surfaces en eau et les surfaces émergées
    vector_water = water.filter("label == 1")
    vector_dry = water.filter("label == 0")
    
    # Initialisation du dictionnaire des résultats
    results = dict()
    
    # Calculer l'aire des surfaces en eau
    results['WATER_AREA'] = image.select('WATER').reduceRegion(
        reducer = ee.Reducer.sum(),
        geometry = vector_water,
        scale = scale
    ).getNumber('WATER')
    
    # Simplifier les géométries
    geoms_water = vector_water.geometry().simplify(scale*simplify_tolerance)
    
    # Calucler les périmètres
    results['WATER_PERIMETER'] = geoms_water.perimeter(scale)
    
    # Calcul du mndwi moyen des surfaces en eau
    results['MEAN_WATER_MNDWI'] = image.select('MNDWI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = vector_water,
        scale = scale
        ).getNumber('MNDWI')
    
    # Calcul du mndwi moyen des surfaces émergées
    results['MEAN_DRY_MNDWI'] = image.select('MNDWI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = vector_dry,
        scale = scale
        ).getNumber('MNDWI')
    
    # Calcul du mndwi moyen de tout le DGO
    results['MEAN_MNDWI'] = image.select('MNDWI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = dgo.geometry(),
        scale = scale
        ).getNumber('MNDWI')
    
    return results



def calculateVegetationMetrics(image, dgo, scale=30, simplify_tolerance=1.5):
    # Vectorisation des surfaces
    vectors = image.select('VEGETATION').reduceToVectors(
        geometry = dgo.geometry(),
        scale = scale,
        eightConnected = True,
        maxPixels = 1e12,
        geometryType = 'polygon')
    
    # Séparer les surfaces végétation du reste
    vector_vegetation = vectors.filter("label == 1")
    
    # Initialisation du dictionnaire des résultats
    results = dict()

    # Calculer l'aire des surfaces végétation
    results['VEGETATION_AREA'] = image.select('VEGETATION').reduceRegion(
        reducer = ee.Reducer.sum(),
        geometry = vector_vegetation,
        scale = scale
    ).getNumber('VEGETATION')
    
    # Simplifier les géométries
    geom_vegetation = vector_vegetation.geometry().simplify(scale*simplify_tolerance)
    
    # Calucler les périmètres
    results['VEGETATION_PERIMETER'] = geom_vegetation.perimeter(scale)
    
    # Calcul du ndvi moyen des surfaces végétation
    results['MEAN_VEGETATION_NDVI'] = image.select('NDVI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = vector_vegetation,
        scale = scale
        ).getNumber('NDVI')
    
    # Calcul du mndwi moyen des surfaces végétation
    results['MEAN_VEGETATION_MNDWI'] = image.select('MNDWI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = vector_vegetation,
        scale = scale
        ).getNumber('MNDWI')
    
    # Calcul du ndvi moyen de tout le DGO
    results['MEAN_NDVI'] = image.select('NDVI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = dgo.geometry(),
        scale = scale
        ).getNumber('NDVI')
        
    return results


def calculateACMetrics(image, dgo, scale=30, simplify_tolerance=1.5):
    # Vectorisation des surfaces
    vectors = image.select('AC').reduceToVectors(
        geometry = dgo.geometry(),
        scale = scale,
        eightConnected = True,
        maxPixels = 1e12,
        geometryType = 'polygon')
    
    # Séparer les surfaces végétation du reste
    vector_ac = vectors.filter("label == 1")
    
    # Initialisation du dictionnaire des résultats
    results = dict()

    # Calculer l'aire des surfaces végétation
    results['AC_AREA'] = image.select('AC').reduceRegion(
        reducer = ee.Reducer.sum(),
        geometry = vector_ac,
        scale = scale
    ).getNumber('AC')
    
    # Calcul du ndvi moyen des surfaces végétation
    results['MEAN_AC_NDVI'] = image.select('NDVI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = vector_ac,
        scale = scale
        ).getNumber('NDVI')
    
    # Calcul du mndwi moyen des surfaces végétation
    results['MEAN_AC_MNDWI'] = image.select('MNDWI').reduceRegion(
        reducer = ee.Reducer.mean(),
        geometry = vector_ac,
        scale = scale
        ).getNumber('MNDWI')
        
    return results


def dgoMetrics(image):
    def mapDGO(dgo_shape):
        
        #TODO: clip image to DGO bounds
                
        cloud_score = calculateCloudScore(image, dgo_shape)
        coverage_score = calculateCoverage(image, dgo_shape)
        water_metrics = calculateWaterMetrics(image, dgo_shape)
        vegetation_metrics = calculateVegetationMetrics(image, dgo_shape)
        ac_metrics = calculateACMetrics(image, dgo_shape)
        
        return dgo_shape.set({'LANDSAT_PRODUCT_ID': image.get('LANDSAT_PRODUCT_ID'), 
                              'CLOUD_SCORE': cloud_score, 
                              'COVERAGE_SCORE': coverage_score,
                              **water_metrics,
                              **vegetation_metrics,
                              **ac_metrics})
    return mapDGO
    
    
def imageMetrics(dgos):
    def mapImage(image):
        
        metrics = dgos.map(dgoMetrics(image))
                               
        return metrics
    
    return mapImage



def calculateDGOsMetrics(collection, dgos):
    
    collection = collection.filterBounds(dgos.union(1))
    
    metrics = collection.map(imageMetrics(dgos))
    
    metrics = metrics.flatten()
    
    return metrics

