import json
import os



class ConfigurationManager:
    """
    A manager to handle a JSON configuration file and its
    version with default values.
    
    The default version of the file must end with
    '.default' before any extension.
    If a non-default version of the file exists it will be loaded,
    otherwise the default version will be loaded instead.
    Whenever a change occurs the configuration will be saved to
    the non-default version of the file.
    """

    def __init__(self, config_path):
        split_path = os.path.splitext(config_path)

        # Handle the default config.
        self.default_config_path = split_path[0] + '.default' + split_path[1]
        if os.path.exists(self.default_config_path):
            self.default_config = self._load_default_config()
            
        # Load the config file. Load the default version if no custom
        # config file is present.
        self.config_path = config_path
        self.config = []
        if os.path.exists(config_path):
            self.config = self._load_config()
        else:
            self.config = self._load_default_config()


    def _load_default_config(self):
        with open(self.default_config_path) as file:
            return json.load(file)


    def _load_config(self):
        with open(self.config_path) as file:
            return json.load(file)


    def _save_config(self):
        with open(self.config_path, 'w') as file:
            json.dump(self.config, file, indent=4, sort_keys=True)


    def _get_nested_dict(self, d, key_path, sep='.'):
        """
            Return the nested dictionary and key that reference the
            endpoint of a path in a dictionary.

            Args:
                d:          Dictionary.
                key_path:   Path to the nested dictionary endpoint.
                sep:        Key separator in the key path.
        """
        keys = key_path.split(sep)
        for k in keys[:-1]:
            d = d[k]
        k = keys[-1]
        if k not in d:
            raise KeyError(k)
        
        return d, keys[-1]


    def set(self, key_path, value, sep='.', match_type=False):
        """
        Set the value in a nested dictionary present in the
        configuration.
        
        Args:
            key_path:       Path to the nested dictionary endpoint.
            value:          Value the nested dictionary must be set to.
            sep:            Key separator in the key path.
            match_type:     If True, the value will be casted to the
                            original value's type.
        """
        d, k = self._get_nested_dict(self.config, key_path, sep=sep)
        d[k] = type(d[k])(value) if match_type else value
        self._save_config()


    def reset(self, key_path, sep='.'):
        """
        Reset the value of a nested dictionary present in the
        configuration.
        
        Args:
            key_path:       Path to the nested dictionary endpoint.
            sep:            Key separator in the key path.
        """
        d, k = self._get_nested_dict(self.config, key_path, sep=sep)
        default_d, k = self._get_nested_dict(self.default_config, key_path, sep=sep)
        d[k] = default_d[k]
        self._save_config()


    def get(self, key_path, sep='.'):
        """
        Get the value assigned to a nested dictionary present in the
        configuration.
        
        Args:
            key_path:       Path to the nested dictionary endpoint.
            sep:            Key separator in the key path.
        """
        d, k = self._get_nested_dict(self.config, key_path, sep=sep)
        return d[k]
    

    def to_json(self, *args, **kwargs):
        """Return the configuration as a JSON string."""
        return json.dumps(self.config, *args, **kwargs)