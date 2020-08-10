from astropy.io import fits
import numpy as np


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
