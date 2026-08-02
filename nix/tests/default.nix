{
  pkgs,
  aionModule,
  aionPackage,
}:
pkgs.testers.runNixOSTest {
  name = "aiond-safe-service";

  nodes.machine = {...}: {
    imports = [aionModule];
    services.aion = {
      enable = true;
      package = aionPackage;
      simulationOnly = true;
    };
    system.stateVersion = "25.11";
  };

  testScript = ''
    start_all()
    machine.wait_for_unit("multi-user.target")
    machine.wait_for_unit("aiond.service")
    machine.succeed("systemctl show aiond.service -p Environment --value | grep -F 'AION_RUNTIME_MODE=simulation'")
    machine.succeed("test \"$(systemctl show aiond.service -p NoNewPrivileges --value)\" = yes")
    machine.succeed("test \"$(systemctl show aiond.service -p ProtectSystem --value)\" = strict")
    machine.succeed("systemctl show aiond.service -p RestrictAddressFamilies --value | grep -Fw AF_UNIX")
    machine.fail("systemctl show aiond.service -p RestrictAddressFamilies --value | grep -Fw AF_INET")
    machine.succeed("test -d /var/lib/aion")
  '';
}
