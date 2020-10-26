from os import environ


def get_config_from_env(prefix, dataclass=None):
    config = {}

    for key, value in environ.items():
        if key.startswith(f"{prefix}_"):
            key = key.replace(f"{prefix}_", "").lower()
            config[key] = value

    if dataclass:
        config = dataclass(**config)

    return config
