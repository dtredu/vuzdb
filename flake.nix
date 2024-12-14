{
  description = "Test project to parse universities data";

  nixConfig = {
    extra-substituters = [
      "https://cache.nixos.org"
      "https://nix-community.cachix.org"
    ];
    extra-trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
    ];
  };

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
  };

  outputs = inputs@{ self, nixpkgs, ... }:
  let
    buildSystems = [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];

    #crossSystems = {
    #  x86_64-linux   = { config = "x86_64-unknown-linux-gnu";  libc = "glibc"; };
    #  i686-linux     = { config = "x86_64-unknown-linux-gnu";  libc = "glibc"; };
    #  aarch64-linux  = { config = "aarch64-unknown-linux-gnu"; libc = "glibc"; };
    #  
    #  x86_64-darwin  = { config = "x86_64-unknown-linux-gnu";  libc = "libSystem"; };
    #  aarch64-darwin = { config = "aarch64-unknown-linux-gnu"; libc = "libSystem"; };

    #  x86_64-windows = { config = "x86_64-w64-mingw32"; libc = "msvcrt"; };
    #  i686-windows   = { config = "i686-w64-mingw32";   libc = "msvcrt"; };
    #};

    forAllSystems = nixpkgs.lib.genAttrs [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];

  in {

    devShells = forAllSystems (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        #python = pkgs.python3.override {
        #  self = python;
        #  packageOverrides = pyfinal: pyprev: {
        #    ghostscript = pyfinal.callPackage gs-py { };
        #  };
        #};
        python-ghostscript = pkgs.python3Packages.callPackage;
      in {
        default = pkgs.mkShell {
          packages = with pkgs; with python3Packages; [
            #(pkgs.python3.withPackages (python-pkgs: [
            #  (python-pkgs.camelot.overrideAttrs (old: old // {
            #    propagatedBuildInputs = old.propagatedBuildInputs ++ [
            #      (python-pkgs.callPackage ./python-ghostscript.nix {})
            #    ];
            #  }))
            #]))
            requests
            camelot
            (callPackage ./python-ghostscript.nix {})
            ghostscript
            #tabula-py
            ##tabula-java
          ];
        };
      }
    ); 
  };
}
