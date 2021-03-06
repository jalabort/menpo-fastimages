import numpy as np
map_coordinates = None  # expensive, from scipy.ndimage
from menpo.external.skimage._warps_cy import _warp_fast
from menpo.transform import Homogeneous

# Store out a transform that simply switches the x and y axis
xy_yx = Homogeneous(np.array([[0., 1., 0.],
                              [1., 0., 0.],
                              [0., 0., 1.]]))


def scipy_interpolation(pixels, points_to_sample, mode='constant', order=1,
                        cval=0.):
    r"""
    Interpolation utilizing SciPy's map_coordinates function.

    Parameters
    ----------
    pixels : (M, N, ..., n_channels) ndarray
        The image to be sampled from, the final axis containing channel
        information

    points_to_sample : (n_points, n_dims) ndarray
        The points which should be sampled from pixels

    mode : {'constant', 'nearest', 'reflect', 'wrap'}, optional
        Points outside the boundaries of the input are filled according to the
        given mode

    order : int, optional
        The order of the spline interpolation. The order has to be in the
        range 0-5

    cval : float, optional
        The value that should be used for points that are sampled from
        outside the image bounds if mode is 'constant'

    Returns
    -------
    sampled_image : ndarray
        The pixel information sampled at each of the points.
    """
    global map_coordinates
    if map_coordinates is None:
        from scipy.ndimage import map_coordinates  # expensive
    sampled_pixel_values = []
    # Loop over every channel in image - we know last axis is always channels
    # Note that map_coordinates uses the opposite (dims, points) convention
    # to us so we transpose
    points_to_sample_t = points_to_sample.T
    for i in xrange(pixels.shape[0]):
        sampled_pixel_values.append(map_coordinates(pixels[i, ...],
                                                    points_to_sample_t,
                                                    mode=mode,
                                                    order=order,
                                                    cval=cval))
    sampled_pixel_values = [v.reshape([1, -1]) for v in sampled_pixel_values]
    return np.concatenate(sampled_pixel_values, axis=0)


def cython_interpolation(pixels, template_shape, h_transform, mode='constant',
                         order=1, cval=0.):
    r"""
    Interpolation utilizing skimage's fast cython warp function.

    Parameters
    ----------
    pixels : (M, N, ..., n_channels) ndarray
        The image to be sampled from, the final axis containing channel
        information.

    template_shape : tuple
        The shape of the new image that will be sampled

    mode : {'constant', 'nearest', 'reflect', 'wrap'}, optional
        Points outside the boundaries of the input are filled according to the
        given mode.

    order : int, optional
        The order of the spline interpolation. The order has to be in the
        range 0-5.

    cval : float, optional
        The value that should be used for points that are sampled from
        outside the image bounds if mode is 'constant'

    Returns
    -------
    sampled_image : ndarray
        The pixel information sampled at each of the points.
    """
    # unfortunately they consider xy -> yx
    matrix = xy_yx.compose_before(h_transform).compose_before(xy_yx).h_matrix
    warped_channels = []
    # Loop over every channel in image - we know last axis is always channels
    # Note that map_coordinates uses the opposite (dims, points) convention
    # to us so we transpose
    for i in xrange(pixels.shape[0]):
        warped_channels.append(_warp_fast(pixels[i, ...], matrix,
                                          output_shape=template_shape,
                                          mode=mode, order=order, cval=cval))
    warped_channels = [v.reshape([1, -1]) for v in warped_channels]
    return np.concatenate(warped_channels, axis=0)