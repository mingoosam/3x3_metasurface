import meep as mp
from meep_utils import geometries



def continuous_source(params):
    
    frequency = params['frequency']
    wavelength = params['wavelength']
    component = params['component']

    if frequency is None and wavelength is None:
        #logger.error("Either frequency or wavelength need to be specified")
        raise NotImplementedError
        exit()

    if component is None:
        #logger.error("The component of the source needs to be specified")
        raise NotImplementedError
        exit()

    if frequency is None and wavelength is not None:
        #logger.info("Calculating frequency from given wavelength")
        frequency = 1 / wavelength

    loc_x_source = params['loc_x_source']
    loc_y_source = params['loc_y_source']
    loc_z_source = params['loc_z_source']

    size_x_source = params['size_x_source']
    size_y_source = params['size_y_source']
    size_z_source = params['size_z_source']

    center = mp.Vector3(loc_x_source, loc_y_source, loc_z_source)
    size = mp.Vector3(size_x_source, size_y_source, size_z_source)
    if None in center:
        #logger.error("Failed to specify center")
        raise NotImplementedError
        exit()

    if None in size:
        #logger.info("Setting default source size from component : {}".format(component))
        if component is mp.Ez:
            size = [params['cell_x'], params['cell_y'], 0]
        elif component is mp.Ex:
            size = [0, params['cell_y'], params['cell_z']]
        elif component is mp.Ey:
            size = [params['cell_x'], 0, params['cell_z']]
        else:
            #logger.error("Failed to specify default size")
            raise NotImplementedError
            exit()


    return [mp.Source(mp.ContinuousSource(frequency=frequency),
                            component=component,
                            center=center,
                            size=size)]


def gaussian_source(params):

    fcen = params['fcen']
    #fwidth = params['fwidth']
    wavelength_list = params['wavelength_list']
    wavelength = params['wavelength']
    component = params['component']

    if fcen is None and wavelength is None:
        #logger.error("Either fcen or wavelength need to be specified")
        raise NotImplementedError
        exit()

    if component is None:
        #logger.error("The component of the source needs to be specified")
        raise NotImplementedError
        exit()

    #if fwidth is None:
    #    logger.error("You need to specify the width of the gaussian source")
    #    exit()

    if fcen is None and wavelength is not None:
        #logger.info("Calculating frequency from given wavelength")
        fcen = 1 / wavelength

    fmax = 1 / min(wavelength_list)
    fmin = 1 / max(wavelength_list)
    fwidth = fmax - fmin

    loc_x_source = params['loc_x_source']
    loc_y_source = params['loc_y_source']
    loc_z_source = params['loc_z_source']

    size_x_source = params['size_x_source']
    size_y_source = params['size_y_source']
    size_z_source = params['size_z_source']

    center = mp.Vector3(loc_x_source, loc_y_source, loc_z_source)
    size = mp.Vector3(size_x_source, size_y_source, size_z_source)
    if None in center:
        #logger.error("Failed to specify center")
        raise NotImplementedError
        exit()

    if None in size:
        #logger.info("Setting default source size from component : {}".format(component))
        if component is mp.Ez:
            size = [params['cell_x'], params['cell_y'], 0]
        elif component is mp.Ex:
            size = [0, params['cell_y'], params['cell_z']]
        elif component is mp.Ey:
            size = [params['cell_x'], 0, params['cell_z']]
        else:
            #logger.error("Failed to specify default size")
            raise NotImplementedError
            exit()

    return [mp.Source(mp.GaussianSource(fcen,
                            fwidth=fwidth),
                            component = component,
                            center=center,
                            size=size)]
   
def build_source(params):
    #logger.info("Building a source")
    source_params = params['source']
    if source_params['type'] == 'continuous':
        #logger.info("Building a continuous source")
        return continuous_source(source_params)
    elif source_params['type'] == 'gaussian':
        #logger.info("Building a gaussian source")
        return gaussian_source(source_params)
    else:
        #logger.error("Source type {} is not supported".format(source_params['type']))
        raise NotImplementedError
        exit()


def build_andy_source(params):

    source_params = params['source']
    substrate_params = params['substrate_params']
    geometry_params = params['geometry']
    thickness_pml = geometry_params['thickness_pml']
    size_z_fused_silica = substrate_params['size_z_fused_silica']

    source_params['component'] = mp.Ey

    #source_params['loc_x_source'] = round(params['cell_x'] / 2, 4)
    #source_params['loc_y_source'] = round(params['cell_y'] / 2, 4)
    source_params['loc_x_source'] = 0
    source_params['loc_y_source'] = 0
    source_params['loc_z_source'] = round(thickness_pml + ((size_z_fused_silica-thickness_pml) * 0.2) - params['cell_z'] / 2, 4)

    source_params['size_x_source'] = params['cell_x']
    source_params['size_y_source'] = params['cell_y']
    source_params['size_z_source'] = 0

    source_params['fcen'] = 1/source_params['wavelength']

    params['source_params'] = source_params

    return build_source(params), params


if __name__ == "__main__":

    params = yaml.load(open('config.yaml'), Loader = yaml.FullLoader)
    geo,pml,mon_vol = geometries.build_andy_metasurface_neighborhood(params)
    source = build_andy_source(params)
    from IPython import embed; embed();

