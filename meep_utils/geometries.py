###################
# Standard imports
###################
import meep as mp
from loguru import logger



##############################################################################
# Simple build functions on the MEEP primatives. Might be overkill - 
# the current primatives are pretty abstract already. These are nice for 
# logging purposes at least.
##############################################################################

def build_cylinder(loc:list, axis:list, height:float, radius:float, material_index:float) -> mp.Cylinder:
    #logger.info("Building a MEEP cylinder")

    #logger.info("Creating cylinder material. Index = {}".format(material_index))
    material = mp.Medium(index = material_index)
    center = mp.Vector3(loc[0], loc[1], loc[2])
    axis = mp.Vector3(axis[0], axis[1], axis[2])

    return mp.Cylinder( radius = radius,
                        height = height,
                        axis = axis,
                        center = center,
                        material = material )

def build_block(size:list, loc:list, material_index:float) -> mp.Block:
    #logger.info("Building a MEEP block")

    #logger.info("Creating block material. Index = {}".format(material_index))
    material = mp.Medium(index = material_index)
    size = mp.Vector3(size[0], size[1], size[2])
    center = mp.Vector3(loc[0], loc[1], loc[2])

    return mp.Block( size = size,
                     center = center,
                     material = material )


##############################################################################
# More complex build functions. Combines the ones above into more complicated
# structures, i.e., a metasurface.
##############################################################################

def build_silica_pdms_substrate(params:dict) -> list:

    #logger.info("Building silica + PDMS substrate.")
    ##################################
    #     _____________________
    #    |        PDMS         |
    #    |_____________________|
    #    |    FUSED SILICA     |
    #    |_____________________|
    #
    ##################################

    #logger.info("Reading fused silica parameters")

    size_x_buffer = params['size_x_buffer']
    size_y_buffer = params['size_y_buffer']
    size_z_buffer = params['size_z_buffer']

    offset_x_buffer = params['offset_x_buffer']
    offset_y_buffer = params['offset_y_buffer']
    offset_z_buffer = params['offset_z_buffer']
    
    size_x_fused_silica = params['size_x_fused_silica'] + size_x_buffer
    size_y_fused_silica = params['size_y_fused_silica'] + size_y_buffer
    size_z_fused_silica = params['size_z_fused_silica']
    
    loc_x_fused_silica = params['loc_x_fused_silica'] + round(size_x_buffer / 2, 4)
    loc_y_fused_silica = params['loc_y_fused_silica'] + round(size_y_buffer / 2, 4)
    loc_z_fused_silica = params['loc_z_fused_silica']
    material_index_fused_silica = params['material_index_fused_silica']

    #logger.info("Creating fused silica material. Index = {}".format(material_index_fused_silica))

    fused_silica = build_block( size = [size_x_fused_silica, size_y_fused_silica, size_z_fused_silica],
                                loc = [loc_x_fused_silica, loc_y_fused_silica, loc_z_fused_silica],
                                material_index = material_index_fused_silica)
    #logger.info("Fused silica size: {}".format(fused_silica.size))
    #logger.info("Fused silica center: {}".format(fused_silica.center))

    #logger.info("Reading PDMS parameters")
    loc_x_pdms = params['loc_x_pdms'] + offset_x_buffer
    loc_y_pdms = params['loc_y_pdms'] + offset_y_buffer
    loc_z_pdms = params['loc_z_pdms']
    
    size_x_pdms = params['size_x_pdms'] + size_x_buffer
    size_y_pdms = params['size_y_pdms'] + size_y_buffer
    size_z_pdms = params['size_z_pdms']

    material_index_pdms = params['material_index_pdms']

    #logger.info("Creating fused silica material. Index = {}".format(material_index_fused_silica))

    pdms = build_block( size = [size_x_pdms, size_y_pdms, size_z_pdms],
                        loc = [loc_x_pdms, loc_y_pdms, loc_z_pdms],
                        material_index = material_index_pdms )

    #logger.info("PDMS size : {}".format(pdms.size))
    #logger.info("PDMS loc : {}".format(pdms.center))
    
    return [fused_silica, pdms]

def build_andy_metasurface_neighborhood(params, radii = None):
    '''
    This is basically the same code as the parameter manager's calculate_dependencies
    from the surrogate model code. Just with additional comments and different
    organization.
    Builds a fused silica + pdms substrate with a Nx x Ny pillar neighborhood.
    '''
    geometry_params = params['geometry']
    Nx, Ny = geometry_params['neighborhood_size']
    #logger.info("Creating metasurface neighborhood. Nx,Ny : {},{}".format(Nx,Ny))

    atom_type = geometry_params['atom_type']
    #logger.info("Meta-atom type: {}".format(atom_type))

    unit_cell_size = geometry_params['unit_cell_size']
    #logger.info("Meta-atom size: {}".format(unit_cell_size))

    if geometry_params['substrate_buffer']:
        #logger.info("Buffer is enabled")
        size_x_buffer = geometry_params['size_x_buffer']
        size_y_buffer = geometry_params['size_y_buffer']
        size_z_buffer = geometry_params['size_z_buffer']
        #logger.info("Buffer : {}, {}, {}".format(size_x_buffer, size_y_buffer, size_z_buffer))

        offset_x_buffer = round(size_x_buffer / 2, 4)
        offset_y_buffer = round(size_y_buffer / 2, 4)
        offset_z_buffer = round(size_z_buffer / 2, 4)
        #logger.info("Center offset added by buffer : {}, {}, {}".format(offset_x_buffer, offset_y_buffer, offset_z_buffer))
        params['geometry']['offset_x_buffer'] = offset_x_buffer
        params['geometry']['offset_y_buffer'] = offset_y_buffer
        params['geometry']['offset_z_buffer'] = offset_z_buffer
    else:
        #logger.info("Buffer is disabled")
        size_x_buffer = 0
        size_y_buffer = 0
        size_z_buffer = 0
        offset_x_buffer = 0
        offset_y_buffer = 0
        offset_z_buffer = 0
    
    #Define the z stack size
    thickness_pml = geometry_params['thickness_pml']
    height_pillar = geometry_params['height_pillar']
    size_z_pdms = round(geometry_params['size_z_pdms'] + height_pillar + thickness_pml + size_z_buffer, 4)
    size_z_fused_silica = geometry_params['size_z_fused_silica'] + thickness_pml
    params['geometry']['size_z_pdms'] = size_z_pdms

    #Add all of the z sizes together to get the total z size
    #I added the PML first above, so they are not included here.
    size_z_cell = round(size_z_fused_silica + size_z_pdms, 4)
    #Multiply the unit cell size by the numer of unit cells to get the x and y sizes
    size_x_cell = round(unit_cell_size * Nx, 4) + size_x_buffer
    size_y_cell = round(unit_cell_size * Ny, 4) + size_y_buffer

    params['cell_x'] = size_x_cell
    params['cell_y'] = size_y_cell
    params['cell_z'] = size_z_cell

    #logger.info("Size of total geometry cell : {} x {} x {} [um]".format(size_x_cell, size_y_cell, size_z_cell))
    cell_size = mp.Vector3(size_x_cell, size_y_cell, size_z_cell)
    params['geometry']['cell_size'] = cell_size

    #Get the z locations (centers)  of all of the geometry objects
    #Here, things can be a little confusing. We need to subtract out 1/2 the
    #total cell size to keep things centered on (0,0)



    loc_z_fused_silica = round(0.5 * size_z_fused_silica - 0.5 * size_z_cell,4)
    #logger.info("Center Z of fused silica : {} [um]".format(loc_z_fused_silica))
    loc_z_pdms = round(size_z_fused_silica + 0.5 * size_z_pdms - 0.5 * size_z_cell, 4)
    #logger.info("Center Z of pdms : {} [um]".format(loc_z_pdms))
    loc_z_pillar = round(size_z_fused_silica + 0.5 * height_pillar - 0.5 * size_z_cell, 4)

    #logger.info("Center Z of pillars : {} [um]".format(loc_z_pillar))

    params['geometry']['loc_z_fused_silica'] = loc_z_fused_silica
    params['geometry']['loc_z_pdms'] = loc_z_pdms
    params['geometry']['loc_z_pillar'] = loc_z_pillar

    loc_top_fused_silica = round(size_z_fused_silica - 0.5 * size_z_cell, 4)
    #logger.info("Top of the fused silica : {} [um]".format(loc_top_fused_silica))

    #The top of the pdms - the whole size minus the amount in the PML
    loc_top_pdms = round(size_z_fused_silica + (size_z_pdms - thickness_pml) - 0.5 * size_z_cell, 4)
    #logger.info("Top of the pdms : {} [um]".format(loc_top_pdms))

    #logger.info("Updating params with calculated locations")
    params['geometry']['loc_top_fused_silica'] = loc_top_fused_silica
    params['geometry']['loc_top_pdms'] = loc_top_pdms

    #Get the size of the non pml region
    size_z_non_pml = size_z_fused_silica + size_z_pdms - 2*thickness_pml
    #logger.info("Size of the non PML volume : {}".format(size_z_non_pml))

    #Get the center of the simulation cell
    #loc_z_center_cell = 0 
    loc_z_center_cell = 0 
    loc_x_center_cell = 0
    loc_y_center_cell = 0
    center_sim_cell = mp.Vector3(loc_x_center_cell, loc_y_center_cell, loc_z_center_cell)
    #logger.info("Center of the simulation cell : {}".format(center_sim_cell))
    params['geometry']['center_sim_cell'] = center_sim_cell

    size_z_non_pml 
    #Get the size of the nonbuffer region
    size_x_non_buffer = params['geometry']['unit_cell_size'] * params['grid_size']
    size_y_non_buffer = params['geometry']['unit_cell_size'] * params['grid_size']
    #logger.info("Size of the non buffer volume : x: {} y: {}".format(size_x_non_buffer, size_y_non_buffer))

    params['geometry']['size_z_non_pml'] = size_z_non_pml
    params['geometry']['size_x_non_buffer'] = size_x_non_buffer
    params['geometry']['size_y_non_buffer'] = size_y_non_buffer

    material_index_fused_silica = geometry_params['material_index_fused_silica']
    material_index_pdms = geometry_params['material_index_pdms']

    substrate_params = {
            'size_x_fused_silica': mp.inf,
            'size_y_fused_silica': mp.inf,
            'size_z_fused_silica': size_z_fused_silica,
            'loc_x_fused_silica': 0,
            'loc_y_fused_silica': 0,
            'loc_z_fused_silica': loc_z_fused_silica,
            'material_index_fused_silica': material_index_fused_silica,
            'size_x_pdms': mp.inf,
            'size_y_pdms': mp.inf,
            'size_z_pdms': size_z_pdms,
            'loc_x_pdms': 0,
            'loc_y_pdms': 0,
            'loc_z_pdms': loc_z_pdms,
            'material_index_pdms': material_index_pdms,
            'substrate_buffer': geometry_params['substrate_buffer'],
            'size_x_buffer': size_x_buffer,
            'size_y_buffer': size_y_buffer,
            'size_z_buffer': size_z_buffer,
            'offset_x_buffer': offset_x_buffer,
            'offset_y_buffer': offset_y_buffer,
            'offset_z_buffer': offset_z_buffer
            }

    params['substrate_params'] = substrate_params

    substrate = build_silica_pdms_substrate(substrate_params)

    metasurface = [i for i in substrate]

    #Now for the pillars
    material_index_pillars = geometry_params['material_index_meta_atom']
    
    if radii == None:
        radii = [0.2 for _ in range(0,Nx*Ny)]

    #logger.info("Radii of the pillars : {}".format(radii))
    count = 0
    for ny in range(0,Ny):
        for nx in range(0,Nx):
            loc_x_pillar = round((unit_cell_size * nx) + 0.5 * unit_cell_size - 0.5 * size_x_cell, 4) + offset_x_buffer
            loc_y_pillar = round((unit_cell_size * ny) + 0.5 * unit_cell_size - 0.5 * size_y_cell, 4) + offset_y_buffer
            params['geometry']['loc_x_pillar_{}'.format(count)] = loc_x_pillar
            params['geometry']['loc_y_pillar_{}'.format(count)] = loc_y_pillar
            metasurface.append(build_cylinder(loc = mp.Vector3(loc_x_pillar, loc_y_pillar, loc_z_pillar),
                                              axis = mp.Vector3(0,0,1),
                                              height = height_pillar,
                                              radius = radii[count],
                                              material_index = material_index_pillars))

            count += 1

    #Now for the pml layers
    pml_layers = [mp.PML(thickness = thickness_pml, direction = mp.Z)]

    params['geometry']['pml_layers'] = pml_layers
    #pml_layers = []

    params['source']['loc_z_source'] = round(thickness_pml + ((size_z_fused_silica-thickness_pml) * 0.2) - params['cell_z'] / 2, 4)
    # adjusting monitor volume to reduce the size
    top_monitor = params['source']['loc_z_source'] + 4.5
    bottom_monitor = -params['cell_z'] / 2 + params['geometry']['thickness_pml']
    size_z_reduced = top_monitor - bottom_monitor
 
    loc_z_center_cell_reduced = -(params['cell_z'] / 2) + params['geometry']['thickness_pml'] + size_z_reduced / 2
    center_sim_cell_reduced = mp.Vector3(loc_x_center_cell, loc_y_center_cell, loc_z_center_cell_reduced)
    #Get the volume not in the PML for the monitors
    #monitor_volume = mp.Volume(center = center_sim_cell,
    #                           size = mp.Vector3(size_x_non_buffer, size_y_non_buffer, size_z_non_pml))
    monitor_volume = mp.Volume(center = center_sim_cell_reduced,
                               size = mp.Vector3(size_x_non_buffer, size_y_non_buffer, size_z_reduced))

    params['geometry']['monitor_volume'] = monitor_volume
    return metasurface, pml_layers, monitor_volume, params

if __name__ == "__main__":
    import yaml
    params = yaml.load(open('config.yaml'), Loader = yaml.FullLoader)
    metasurface, pml, monitor_volume = build_andy_metasurface_neighborhood(params)
    from IPython import embed; embed()

