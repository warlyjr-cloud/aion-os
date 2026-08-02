{
  aionPackage,
  modulesPath,
  ...
}: {
  imports = [
    "${modulesPath}/virtualisation/qemu-vm.nix"
    ../modules/aion.nix
    ../lab/default.nix
  ];

  nixpkgs.hostPlatform = "x86_64-linux";
  networking.hostName = "aion-lab";
  networking.firewall.enable = true;
  services.openssh.enable = false;

  services.aion = {
    enable = true;
    package = aionPackage;
    simulationOnly = true;
  };

  users.users.aion-lab = {
    isNormalUser = true;
    description = "AION Lab operator";
  };
  services.getty.autologinUser = "aion-lab";

  virtualisation = {
    cores = 2;
    diskSize = 8192;
    graphics = false;
    memorySize = 2048;
  };

  system.stateVersion = "25.11";
}
