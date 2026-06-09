class VDisplayError(Exception):
    pass


class BackendNotAvailableError(VDisplayError):
    pass


class CapabilityError(VDisplayError):
    pass
