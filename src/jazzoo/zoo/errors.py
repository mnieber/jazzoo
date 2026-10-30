from jazzoo.errors import JazzooError


class ZooError(JazzooError):
    pass


class NotInZooEnvError(ZooError):
    pass


class RootDirMissingError(ZooError):
    pass


class NoSuchZooEnvError(ZooError):
    pass


class NoRecentZooEnvError(ZooError):
    pass


class ZooEnvExistsError(ZooError):
    pass


class InvalidZooEnvNameError(ZooError):
    pass


class NoRootFileError(ZooError):
    pass


class VenvInUseError(ZooError):
    pass


class ZooLinkExistsError(ZooError):
    pass


class VenvExistsError(ZooError):
    pass


class VenvCreationError(ZooError):
    pass


class NotAVenvError(ZooError):
    pass


class NoZooInVenvError(ZooError):
    pass


class FishFileExistsError(ZooError):
    pass


class ZooUsageError(ZooError):
    pass
