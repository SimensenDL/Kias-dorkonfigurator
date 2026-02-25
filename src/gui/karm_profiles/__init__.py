"""Registry over karm-profiler for 3D-vieweren.

Kvar karmtype har ein profil som definerer geometri og plassering
av karm, dørblad, hengsler, håndtak og terskel.
"""

from .sdi.sd1 import SD1Profile
from .sdi.sd2 import SD2Profile
from .sdi.sd3id import SD3IDProfile
from .kd.kd1 import KD1Profile
from .kd.kd2 import KD2Profile
from .pd.pd1 import PD1Profile
from .pd.pd2 import PD2Profile
from .fd.fd1 import FD1Profile
from .fd.fd2 import FD2Profile
from .fd.fd3 import FD3Profile

KARM_PROFILES = {
    'SD1': SD1Profile(),
    'SD2': SD2Profile(),
    'SD3/ID': SD3IDProfile(),
    'KD1': KD1Profile(),
    'KD2': KD2Profile(),
    'PD1': PD1Profile(),
    'PD2': PD2Profile(),
    'BD1': SD1Profile(),
    'FD1': FD1Profile(),
    'FD2': FD2Profile(),
    'FD3': FD3Profile(),
}
