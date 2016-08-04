from errbot import BotPlugin


class Storagetest(BotPlugin):
    """
    Just a plugin with a simple string config.
    """
    def get_configuration_template(self):
        return {'StorageType': 'Unconfigured'}
