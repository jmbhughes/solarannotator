from astropy.io import fits
import numpy as np
from goessolarretriever import Product, Satellite, Retriever
from collections import namedtuple
import tempfile
import os
from dateutil.parser import parse as parse_date_str
from sunpy.net import Fido, attrs as a
import astropy.units as u
from datetime import timedelta
import sunpy.map
from sunpy.coordinates import Helioprojective


Image = namedtuple('Image', 'data header')


class ImageSet:
    def __init__(self, mapping):
        super().__init__()
        self.images = mapping

    @staticmethod
    def retrieve(date):
        full_set = ImageSet._load_suvi_composites(date)
        full_set['gong'] = ImageSet._load_gong_image(date, full_set['195'])
        return ImageSet(full_set)

    @staticmethod
    def _load_gong_image(date, suvi_195_image):
        # Find an image and download it
        results = Fido.search(a.Time(date-timedelta(hours=1), date+timedelta(hours=1)),
                              a.Wavelength(6563 * u.Angstrom), a.Source("GONG"))
        selection = results[0][len(results[0])//2]  # only download the middle image
        downloads = Fido.fetch(selection)
        with fits.open(downloads[0]) as hdul:
            gong_data = hdul[1].data
            gong_head = hdul[1].header

        # update the header to actually load in a SunPy map
        gong_head['CTYPE1'] = "HPLN-TAN"
        gong_head['CTYPE2'] = "HPLT-TAN"
        gong_head['CUNIT1'] = "arcsec"
        gong_head['CUNIT2'] = "arcsec"
        # number below from SunPy discussions: https://github.com/sunpy/sunpy/issues/6656#issuecomment-1344413011
        gong_head['CDELT1'] = 1.082371820584223
        gong_head['CDELT2'] = 1.082371820584223

        # Load as a map
        gong_map = sunpy.map.Map(gong_data, gong_head)
        suvi_map = sunpy.map.Map(suvi_195_image.data, suvi_195_image.header)
        suvi_head = suvi_195_image.header

        with Helioprojective.assume_spherical_screen(suvi_map.observer_coordinate, only_off_disk=True):
            out = gong_map.reproject_to(suvi_head)

        return Image(out.data, dict(out.meta))


    @staticmethod
    def _load_suvi_composites(date):
        satellite = Satellite.GOES16
        products = {"94": Product.suvi_l2_ci094,
                    "131": Product.suvi_l2_ci131,
                    "171": Product.suvi_l2_ci171,
                    "195": Product.suvi_l2_ci195,
                    "284": Product.suvi_l2_ci284,
                    "304": Product.suvi_l2_ci304}
        composites = {}
        r = Retriever()
        for wavelength, product in products.items():
            fn = r.retrieve_nearest(satellite, product, date, tempfile.gettempdir())
            with fits.open(fn) as hdus:
                data = hdus[1].data
                header = hdus[1].header
                composites[wavelength] = Image(data, header)
            os.remove(fn)
        return composites


    @staticmethod
    def create_empty():
        mapping = {"94": Image(np.zeros((1280, 1280)), {}),
                   '131': Image(np.zeros((1280, 1280)), {}),
                   '171': Image(np.zeros((1280, 1280)), {}),
                   '195': Image(np.zeros((1280, 1280)), {}),
                   '284': Image(np.zeros((1280, 1280)), {}),
                   '304': Image(np.zeros((1280, 1280)), {}),
                   'gong': Image(np.zeros((1280, 1280)), {})}
        return ImageSet(mapping)

    def __getitem__(self, key):
        return self.images[key]

    def channels(self):
        return list(self.images.keys())


class ThematicMap:
    def __init__(self, data, metadata, theme_mapping):
        """
        A representation of a thematic map
        :param data: the image of numbers for the labelling
        :param metadata: dictionary of header information
        :param theme_mapping: dictionary of theme indices to theme names, the second hdu info
        """
        self.data = data
        self.metadata = metadata
        self.date_obs = parse_date_str(self.metadata['DATE-OBS'])
        self.theme_mapping = theme_mapping

    @staticmethod
    def load(path):
        """
        Load a thematic map
        :param path: path to the file
        :return: ThematicMap object that was loaded
        """
        with fits.open(path) as hdulist:
            data = hdulist[0].data
            metadata = dict(hdulist[0].header)
            theme_mapping = dict(hdulist[1].data)
            if 0 in theme_mapping:
                del theme_mapping[0]
        return ThematicMap(data, metadata, theme_mapping)

    def complies_with_mapping(self, other_theme_mapping):
        """
        Checks that the theme mappings match, i.e. they have identical entries
        :param other_theme_mapping: a dictionary of another theme_mapping, e.g. {1: 'outer_space'}
        :return: true or false depending on the matching
        """
        for theme_i, theme_name in self.theme_mapping.items():
            if theme_i not in other_theme_mapping:
                return False
            if other_theme_mapping[theme_i] != self.theme_mapping[theme_i]:
                return False

        for theme_i, theme_name in other_theme_mapping.items():
            if theme_i not in self.theme_mapping:
                return False
            if other_theme_mapping[theme_i] != self.theme_mapping[theme_i]:
                return False
        return True

    def save(self, path):
        """
        Write out a thematic map FITS
        :param path: where to save thematic maps fits file
        :return:
        """
        pri_hdu = fits.PrimaryHDU(data=self.data.astype(np.uint8))
        for k, v in self.metadata.items():
            if k != 'COMMENT':
                pri_hdu.header[k] = v

        map_val = []
        map_label = []
        for key, value in sorted(self.theme_mapping.items(), key=lambda k_v: (k_v[0], k_v[1])):
            map_label.append(value)
            map_val.append(key)
        c1 = fits.Column(name="Thematic Map Value", format="B", array=np.array(map_val))
        c2 = fits.Column(name="Feature Name", format="22A", array=np.array(map_label))
        bintbl_hdr = fits.Header([("XTENSION", "BINTABLE")])
        sec_hdu = fits.BinTableHDU.from_columns([c1, c2], header=bintbl_hdr)
        hdu = fits.HDUList([pri_hdu, sec_hdu])
        hdu.writeto(path, overwrite=True, checksum=True)

    def copy_195_metadata(self, image_set):
        keys_to_copy = ['YAW_FLIP', 'ECLIPSE', 'WCSNAME', 'CTYPE1', 'CTYPE2', 'CUNIT1', 'CUNIT2',
                        'PC1_1', 'PC1_2', 'PC2_1', 'PC2_2', 'CDELT1', 'CDELT2', 'CRVAL1', 'CRVAL2',
                        'CRPIX1', 'CRPIX2', 'DIAM_SUN', 'LONPOLE', 'CROTA', 'SOLAR_B0', 'ORIENT', 'DSUN_OBS']
        if image_set.images['195'].header != {}:
            for key in keys_to_copy:
                self.metadata[key] = image_set.images['195'].header[key]
