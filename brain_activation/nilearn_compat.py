"""Compatibility shims for nilearn >=0.14 with atlasreader and legacy imports."""

import sys
import types

import numpy as np
import pandas as pd
import nilearn._utils as _nilearn_utils
import nilearn.image as _nilearn_image
from nilearn import image
from nilearn.image import check_niimg
from nilearn.regions import connected_regions

# nilearn 0.14 removed check_niimg from nilearn._utils; atlasreader still imports it.
if not hasattr(_nilearn_utils, "check_niimg"):
    _nilearn_utils.check_niimg = _nilearn_image.check_niimg

# atlasreader still imports pkg_resources on some Python environments.
if "pkg_resources" not in sys.modules:
    try:
        import pkg_resources  # noqa: F401
    except ImportError:
        from importlib.resources import files

        pkg_resources = types.ModuleType("pkg_resources")
        pkg_resources.resource_filename = lambda package, resource: str(
            files(package).joinpath(resource)
        )
        sys.modules["pkg_resources"] = pkg_resources

from atlasreader.atlasreader import (  # noqa: E402
    check_atlases,
    get_cluster_data,
    get_peak_data,
)

try:
    from nilearn.maskers import NiftiMasker
except ImportError:  # nilearn < 0.13
    from nilearn.input_data import NiftiMasker  # type: ignore[no-redef]


def process_img(stat_img, cluster_extent, voxel_thresh, direction="both"):
    """Atlasreader-compatible cluster extraction with nilearn 0.14 fixes."""
    img_4d = check_niimg(stat_img, atleast_4d=True)
    if img_4d.shape[-1] == 1:
        stat_img = img_4d.slicer[..., 0]
    else:
        stat_img = image.index_img(img_4d, 0)

    if voxel_thresh < 0:
        voxel_thresh = f"{100 + voxel_thresh}%"
    elif voxel_thresh > np.nan_to_num(np.abs(stat_img.get_fdata())).max():
        empty = np.zeros(stat_img.shape + (1,))
        return image.new_img_like(stat_img, empty)

    thresh_img = image.threshold_img(stat_img, threshold=voxel_thresh)
    min_region_size = cluster_extent * np.prod(thresh_img.header.get_zooms())
    clusters = []

    if direction == "both":
        direction_list = ["pos", "neg"]
    elif direction == "pos":
        direction_list = ["pos"]
    else:
        direction_list = ["neg"]

    for sign in direction_list:
        data = thresh_img.get_fdata().copy()
        data[(data < 0) if sign == "pos" else (data > 0)] = 0
        if not np.any(data):
            continue
        try:
            if min_region_size != 0.0:
                min_region_size -= 1e-8
            region = connected_regions(
                image.new_img_like(thresh_img, data),
                min_region_size=min_region_size,
                extract_type="connected_components",
            )[0]
            if region is not None:
                clusters.append(region)
        except TypeError:
            pass

    if not clusters:
        return image.new_img_like(thresh_img, np.zeros(stat_img.shape + (1,)))

    clust_img = image.concat_imgs(clusters)
    cluster_size = (clust_img.get_fdata() != 0).sum(axis=(0, 1, 2))
    new_order = np.argsort(cluster_size)[::-1]
    return image.index_img(clust_img, new_order)


def get_statmap_info(
    stat_img,
    cluster_extent,
    atlas="default",
    voxel_thresh=1.96,
    direction="both",
    prob_thresh=5,
    min_distance=None,
):
    """Atlasreader cluster tables with pandas 2.x-safe numeric columns."""
    stat_img = check_niimg(stat_img)
    atlas = check_atlases(atlas)

    clust_img = process_img(
        stat_img,
        voxel_thresh=voxel_thresh,
        direction=direction,
        cluster_extent=cluster_extent,
    )

    clust_info, peaks_info = [], []
    if clust_img.get_fdata().any():
        for n, cluster in enumerate(image.iter_img(clust_img)):
            peak_data = get_peak_data(
                cluster,
                atlas=atlas,
                prob_thresh=prob_thresh,
                min_distance=min_distance,
            )
            clust_data = get_cluster_data(cluster, atlas=atlas, prob_thresh=prob_thresh)
            cluster_id = np.repeat(n + 1, len(peak_data))
            peaks_info.append(np.column_stack([cluster_id, peak_data]))
            clust_info.append([n + 1] + clust_data)
        clust_info = np.row_stack(clust_info)
        peaks_info = np.row_stack(peaks_info)

        atlasnames = [a.atlas for a in atlas]
        clust_frame = pd.DataFrame(
            clust_info,
            columns=[
                "cluster_id",
                "peak_x",
                "peak_y",
                "peak_z",
                "cluster_mean",
                "volume_mm",
            ]
            + atlasnames,
        )
        peaks_frame = pd.DataFrame(
            peaks_info,
            columns=[
                "cluster_id",
                "peak_x",
                "peak_y",
                "peak_z",
                "peak_value",
                "volume_mm",
            ]
            + atlasnames,
        )
        for col in range(6):
            c_clust = clust_frame.columns[col]
            c_peak = peaks_frame.columns[col]
            clust_frame[c_clust] = pd.to_numeric(clust_frame[c_clust], errors="coerce")
            peaks_frame[c_peak] = pd.to_numeric(peaks_frame[c_peak], errors="coerce")

        return clust_frame, peaks_frame

    empty_cols_clust = ["cluster_id", "peak_x", "peak_y", "peak_z", "cluster_mean", "volume_mm"]
    empty_cols_peaks = ["cluster_id", "peak_x", "peak_y", "peak_z", "peak_value", "volume_mm"]
    return pd.DataFrame(columns=empty_cols_clust), pd.DataFrame(columns=empty_cols_peaks)


__all__ = ["get_statmap_info", "process_img", "NiftiMasker"]
