import sys
import types

'''
_distutils_shim.py
    undetected_chromedriver's patcher.py does `from distutils.version import
    LooseVersion`. Modern setuptools intercepts any `import distutils` and
    redirects it to a vendored copy (setuptools._distutils), which drags in
    setuptools' own vendored packaging/pyparsing just to satisfy that one
    import - a chain that can take anywhere from a few seconds to several
    minutes depending on the machine/antivirus, and looks like a hang.

    This registers a minimal, self-contained LooseVersion (same list-of-ints
    version comparison behavior, enough for undetected_chromedriver's use:
    comparing Chrome version strings) directly into sys.modules, BEFORE
    anything else has a chance to trigger the real `import distutils`. Must
    be imported first, before botcity.web / undetected_chromedriver.
'''

if "distutils" not in sys.modules:
    distutils_mod = types.ModuleType("distutils")
    version_mod = types.ModuleType("distutils.version")

    class LooseVersion:
        def __init__(self, vstring):
            self.vstring = vstring
            self.version = [int(part) if part.isdigit() else part
                            for part in vstring.replace("-", ".").split(".")]

        def __repr__(self):
            return f"LooseVersion({self.vstring!r})"

        def _as_version(self, other):
            return other.version if isinstance(other, LooseVersion) else LooseVersion(str(other)).version

        def __eq__(self, other):
            return self.version == self._as_version(other)

        def __lt__(self, other):
            return self.version < self._as_version(other)

        def __le__(self, other):
            return self.version <= self._as_version(other)

        def __gt__(self, other):
            return self.version > self._as_version(other)

        def __ge__(self, other):
            return self.version >= self._as_version(other)

    version_mod.LooseVersion = LooseVersion
    distutils_mod.version = version_mod
    sys.modules["distutils"] = distutils_mod
    sys.modules["distutils.version"] = version_mod
