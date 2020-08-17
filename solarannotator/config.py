import json
import matplotlib


class Config:
    def __init__(self, config_file_path):
        """
        Handles configuring the annotation tool
        :param config_file_path: string path to configuration file
        """
        with open(config_file_path) as f:
            config = json.load(f)

        if not self.is_valid():
            raise RuntimeError("The configuration file provided is invalid")

        self.solar_classes = [(c, int(n)) for c, n in config['classes'].items()]
        self.solar_class_index = {c: n for c, n in self.solar_classes}
        self.solar_class_name = {n: c for c, n in config['classes'].items()}
        self.solar_colors = config['display']['colors']
        self.color_table = [self.solar_colors[self.solar_class_name[i]] if i in self.solar_class_name else '#FFFFFF'
                            for i in range(max(list(self.solar_class_name.keys()))+1)]
        self.solar_cmap = matplotlib.colors.ListedColormap(self.color_table)
        self.max_index = max(list(self.solar_class_name.keys()))

    def is_valid(self):
        """
        Check that the configuration file is valid
        :return: boolean indicating validity
        """
        # TODO : write
        return True
