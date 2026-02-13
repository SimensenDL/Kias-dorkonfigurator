"""Registry over karm-profiler for 3D-vieweren.

Kvar karmtype har ein profil som definerer geometri og plassering
av karm, dørblad, hengsler, håndtak og terskel.
"""

from .sdi.sd1 import SD1Profile
from .sdi.sd2 import SD2Profile
from .sdi.sd3id import SD3IDProfile

KARM_PROFILES = {
    'SD1': SD1Profile(),
    'SD2': SD2Profile(),
    'SD3/ID': SD3IDProfile(),
}
