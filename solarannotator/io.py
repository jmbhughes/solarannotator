from astropy.io import fits
import numpy as np
from goessolarretriever import Product, Satellite, Retriever
from collections import namedtuple
import tempfile
import os
from dateutil.parser import parse as parse_date_str

Image = namedtuple('Image', 'data header')


class ImageSet:
    def __init__(self, mapping):
        super().__init__()
        self.images = mapping

    @staticmethod
    def retrieve(date):
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
        return ImageSet(composites)

    @staticmethod
    def create_empty():
        mapping = {"94": Image(np.zeros((1280, 1280)), {}),
                   '131': Image(np.zeros((1280, 1280)), {}),
                   '171': Image(np.zeros((1280, 1280)), {}),
                   '195': Image(np.zeros((1280, 1280)), {}),
                   '284': Image(np.zeros((1280, 1280)), {}),
                   '304': Image(np.zeros((1280, 1280)), {})}
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
        pri_hdu = fits.PrimaryHDU(data=self.data)
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