{
  aionPackage,
  config,
  modulesPath,
  pkgs,
  ...
}: {
  imports = [
    "${modulesPath}/installer/cd-dvd/installation-cd-minimal.nix"
    ../modules/aion.nix
  ];

  nixpkgs.hostPlatform = "x86_64-linux";
  image.fileName = "aion-os-${config.system.nixos.label}-${pkgs.stdenv.hostPlatform.system}.iso";
  networking.hostName = "aion-live";
  networking.firewall.enable = true;
  services.openssh.enable = false;

  services.aion = {
    enable = true;
    package = aionPackage;
    simulationOnly = true;
  };

  system.stateVersion = "25.11";
}
