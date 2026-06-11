"""Command verbs for the application."""

from enum import StrEnum


class CommandVerb(StrEnum):
    HEALTH = "HEALTH"
    INFO = "INFO"
    OUTPUTS = "OUTPUTS"
    MONITORS = "MONITORS"
    WINDOWS = "WINDOWS"
    ALL = "ALL"
    CAPABILITIES = "CAPABILITIES"
    VALIDATE = "VALIDATE"
    SCREENSHOT = "SCREENSHOT"
    SCREENCAST_START = "SCREENCAST_START"
    SCREENCAST_STOP = "SCREENCAST_STOP"
    VIRTUAL_START = "VIRTUAL_START"
    VIRTUAL_STOP = "VIRTUAL_STOP"
    TERMINAL_OPEN = "TERMINAL_OPEN"
    BROWSER_OPEN = "BROWSER_OPEN"
    LAUNCH = "LAUNCH"
    MIRROR = "MIRROR"
    ADOPT = "ADOPT"
    RELEASE = "RELEASE"
    CONTROLS_LIST = "CONTROLS_LIST"
    CONTROLS_FIND = "CONTROLS_FIND"
    CONTROL_CLICK = "CONTROL_CLICK"
    CONTROL_FOCUS = "CONTROL_FOCUS"
    CONTROL_SET_VALUE = "CONTROL_SET_VALUE"
    DIAGNOSE_CONTROL = "DIAGNOSE_CONTROL"


QUERY_VERBS = frozenset(
    {
        CommandVerb.HEALTH,
        CommandVerb.INFO,
        CommandVerb.OUTPUTS,
        CommandVerb.MONITORS,
        CommandVerb.WINDOWS,
        CommandVerb.ALL,
        CommandVerb.CAPABILITIES,
        CommandVerb.VALIDATE,
        CommandVerb.CONTROLS_LIST,
        CommandVerb.CONTROLS_FIND,
        CommandVerb.DIAGNOSE_CONTROL,
    }
)

COMMAND_VERBS = frozenset(
    {
        CommandVerb.SCREENSHOT,
        CommandVerb.SCREENCAST_START,
        CommandVerb.SCREENCAST_STOP,
        CommandVerb.VIRTUAL_START,
        CommandVerb.VIRTUAL_STOP,
        CommandVerb.TERMINAL_OPEN,
        CommandVerb.BROWSER_OPEN,
        CommandVerb.LAUNCH,
        CommandVerb.MIRROR,
        CommandVerb.ADOPT,
        CommandVerb.RELEASE,
        CommandVerb.CONTROL_CLICK,
        CommandVerb.CONTROL_FOCUS,
        CommandVerb.CONTROL_SET_VALUE,
    }
)