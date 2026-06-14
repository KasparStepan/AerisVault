"""The single source of truth for which tools the platform exposes.

Adding a tool: create its module package exposing a MODULE descriptor, then
append it here.
"""

from aerisvault.modules.fsi import MODULE as fsi
# from aerisvault.modules.aerocfd import MODULE as aerocfd   # added when aerocfd lands

MODULES = [fsi]
