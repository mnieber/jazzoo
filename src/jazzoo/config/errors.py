class ConfigError(Exception):
    pass


class ConfigFileError(ConfigError):
    pass


class ConfigKeyError(ConfigError):
    pass


class ConfigExpansionError(ConfigError):
    pass
