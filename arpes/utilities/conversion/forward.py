import xarray as xr
import numpy as np

from utilities.conversion.bounds_calculations import euler_to_kx, euler_to_ky, euler_to_kz

__all__ = ('convert_coordinates_to_kspace_forward',)


def convert_coordinates_forward(arr: xr.DataArray, dimension_to_convert):
    target_coordinates = dict(arr.coords)

    if dimension_to_convert == 'phi':
        return {}
    if dimension_to_convert == 'polar':
        return {}
    if dimension_to_convert == 'hv':
        return {}


def fill_coords(arr: xr.DataArray):
    """
    Ensures all standard kspace coordinates are represented
    :param arr:
    :return:
    """

    is_anglespace = 'phi' in arr.dims or 'polar' in arr.dims or 'hv'in arr.dims

    new_coordinates = {}

    if is_anglespace:
        full_coordinates = arr.S.full_coords
        for k, v in full_coordinates.items():
            if k not in arr.coords:
                arr.coords[k] = v
    else:
        pass

def convert_coordinates_to_kspace_forward(arr: xr.DataArray, **kwargs):
    """
    Forward converts all the individual coordinates of the data array
    :param arr:
    :param kwargs:
    :return:
    """

    skip = {'eV', 'cycle', 'delay', 'T'}
    keep = {'eV', }

    all = {k: v for k, v in arr.indexes.items() if k not in skip}
    kept = {k: v for k, v in arr.indexes.items() if k in keep}

    old_dims = list(all.keys())
    old_dims.sort()

    if len(old_dims) == 0:
        return None

    dest_coords = {
        ('phi',): ['kp', 'kz'],
        ('polar',): ['kp', 'kz'],
        ('phi', 'polar',): ['kx', 'ky', 'kz'],
        ('hv', 'phi',): ['kx', 'ky', 'kz'],
        ('hv',): ['kp', 'kz'],
        ('hv', 'phi', 'polar'): ['kx', 'ky', 'kz'],
    }.get(tuple(old_dims))

    full_old_dims = old_dims + list(kept.keys())
    projection_vectors = np.ndarray(shape=tuple(len(arr.coords[d]) for d in full_old_dims), dtype=object)

    fill_coords(arr)

    # these are a little special, depending on the scan type we might not have a phi coordinate
    # that aspect of this is broken for now, but we need not worry
    def broadcast_by_dim_location(data, target_shape, dim_location=None):
        if isinstance(data, xr.DataArray):
            if len(data.dims) == 0:
                data = data.item()

        if isinstance(data, (int, float,)):
            return np.ones(target_shape) * data

        # else we are dealing with an actual array
        the_slice = [None] * len(target_shape)
        the_slice[dim_location] = slice(None, None, None)

        return np.asarray(data)[the_slice]

    raw_coords = {
        'phi': arr.coords['phi'].values - arr.S.phi_offset,
        'polar': (arr.coords['polar'].values or 0) - arr.S.polar_offset,
        'hv': arr.coords['hv'],
    }

    raw_coords = {k: broadcast_by_dim_location(v, projection_vectors.shape, full_old_dims.index(k) if k in full_old_dims else None)
                  for k, v in raw_coords.items()}

    # fill in the vectors
    binding_energy = broadcast_by_dim_location(arr.coords['eV'] - arr.S.work_function,
                                               projection_vectors.shape, full_old_dims.index('eV') if 'eV' in full_old_dims else None)
    photon_energy = broadcast_by_dim_location(arr.coords['hv'], projection_vectors.shape, full_old_dims.index('hv') if 'hv' in full_old_dims else None)
    kinetic_energy = binding_energy + photon_energy


    inner_potential = arr.S.inner_potential

    # some notes on angle conversion:
    # BL4 conventions
    # angle conventions are standard:
    # phi = analyzer acceptance
    # polar = perpendicular scan angle
    # theta = parallel to analyzer slit rotation angle

    # [ 1  0          0          ]   [  cos(polar) 0 sin(polar) ]   [ 0          ]
    # [ 0  cos(theta) sin(theta) ] * [  0          1 0          ] * [ k sin(phi) ]
    # [ 0 -sin(theta) cos(theta) ]   [ -sin(polar) 0 cos(polar) ]   [ k cos(phi) ]
    #
    # =
    #
    # [ 1  0          0          ]     [ sin(polar) * cos(phi) ]
    # [ 0  cos(theta) sin(theta) ] * k [ sin(phi) ]
    # [ 0 -sin(theta) cos(theta) ]     [ cos(polar) * cos(phi) ]
    #
    # =
    #
    # k ( sin(polar) * cos(phi),
    #     cos(theta)*sin(phi) + cos(polar) * cos(phi) * sin(theta),
    #     -sin(theta) * sin(phi) + cos(theta) * cos(polar) * cos(phi),
    #   )
    #
    # main chamber conventions, with no analyzer rotation (referred to as alpha angle in the Igor code
    # angle conventions are standard:
    # phi = analyzer acceptance
    # polar = perpendicular scan angle
    # theta = parallel to analyzer slit rotation angle

    # [ 1 0 0                    ]     [ sin(phi + theta) ]
    # [ 0 cos(polar) sin(polar)  ] * k [ 0                  ]
    # [ 0 -sin(polar) cos(polar) ]     [ cos(phi + theta) ]
    #
    # =
    #
    # k (sin(phi + theta), cos(phi + theta) * sin(polar), cos(phi + theta) cos(polar), )
    #

    # for now we are setting the theta angle to zero, this only has an effect for vertical slit analyzers,
    # and then only when the tilt angle is very large
    raw_translated = {
        'kx': euler_to_kx(kinetic_energy, raw_coords['phi'], raw_coords['polar'], theta=0,
                          slit_is_vertical=arr.S.is_slit_vertical),
        'ky': euler_to_ky(kinetic_energy, raw_coords['phi'], raw_coords['polar'], theta=0,
                          slit_is_vertical=arr.S.is_slit_vertical),
        'kz': euler_to_kz(kinetic_energy, raw_coords['phi'], raw_coords['polar'], theta=0,
                          slit_is_vertical=arr.S.is_slit_vertical,
                          inner_potential=inner_potential),
    }

    if 'kp' in dest_coords:
        raw_translated['kp'] = np.sqrt(raw_translated['kx'] ** 2 + raw_translated['ky'] ** 2)

    data_vars = {}
    for dest_coord in dest_coords:
        data_vars[dest_coord] = (full_old_dims, np.squeeze(raw_translated[dest_coord]))

    return xr.Dataset(data_vars, coords=arr.indexes)


