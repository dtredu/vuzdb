{ lib
, buildPythonPackage
, fetchPypi
, setuptools
, ghostscript
, substituteAll
}:
buildPythonPackage rec {
  pname = "python-ghostscript";
  version = "0.7";
  src = fetchPypi {
    pname = "ghostscript";
    inherit version;
    hash = "sha256-t4dahwmHQOsL494tlmLRXbcnMFypptS3U0o8wzpLllo==";
  };

  # idk, why, but getting the following error otherwise
  # AttributeError: module 'ghostscript' has no attribute '__version__'
  #preBuild = ''
  #  sed -i 's/__version__ = gs.__version__/__version__ = "0.7"/g' ghostscript/__init__.py
  #'';
  doCheck = true;
  pyproject = true;
  build-system = [ setuptools ];
  propagatedBuildInputs = [ ghostscript ];
  patches = [
    # 1) idk why, but without __version__ hardcoded in __init__.py it errors:
    # AttributeError: module 'ghostscript' has no attribute '__version__'
    # 2) link agains libgs.so from ghostscript
    (substituteAll {
      src = ./python-ghostscript.patch;
      libgs = "${ghostscript}/lib/libgs.so";
    })
  ];
}
