{
  config,
  lib,
  pkgs,
  ...
}: let
  cfg = config.services.aion;
in {
  options.services.aion = {
    enable = lib.mkEnableOption "AION evolution engine";

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ../package.nix {};
      defaultText = lib.literalExpression "pkgs.callPackage ../package.nix {}";
      description = "AION package used by the daemon.";
    };

    simulationOnly = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Keep all candidate actions in simulation mode.";
    };

    dangerouslyAllowHostMutation = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Explicit break-glass acknowledgement for non-simulated operation.";
    };

    stateDirectory = lib.mkOption {
      type = lib.types.strMatching "[a-zA-Z0-9_.-]+";
      default = "aion";
      description = "Name of the systemd-managed state directory.";
    };

    socketName = lib.mkOption {
      type = lib.types.strMatching "[a-zA-Z0-9_.-]+";
      default = "aiond.sock";
      description = "Name of the local Unix domain socket.";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.simulationOnly || cfg.dangerouslyAllowHostMutation;
        message = "Disabling AION simulation mode requires dangerouslyAllowHostMutation = true.";
      }
    ];

    systemd.services.aiond = {
      description = "AION safe evolution daemon";
      wantedBy = ["multi-user.target"];
      after = ["local-fs.target"];

      environment = {
        AION_RUNTIME_MODE =
          if cfg.simulationOnly
          then "simulation"
          else "approved-host-mutation";
        AION_ALLOW_HOST_MUTATION =
          if cfg.simulationOnly
          then "0"
          else "1";
        AION_STATE_DIR = "/var/lib/${cfg.stateDirectory}";
        AION_PROJECT_ROOT = "/var/lib/${cfg.stateDirectory}";
        AION_SOCKET_PATH = "/run/aion/${cfg.socketName}";
        HOME = "/var/lib/${cfg.stateDirectory}";
      };

      unitConfig = {
        StartLimitBurst = 3;
        StartLimitIntervalSec = 60;
      };

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/aiond";
        WorkingDirectory = "/var/lib/${cfg.stateDirectory}";
        Restart = "on-failure";
        RestartSec = 5;
        TimeoutStartSec = 30;
        TimeoutStopSec = 20;

        DynamicUser = true;
        User = "aion";
        Group = "aion";
        StateDirectory = cfg.stateDirectory;
        StateDirectoryMode = "0700";
        RuntimeDirectory = "aion";
        RuntimeDirectoryMode = "0700";
        UMask = "0077";

        NoNewPrivileges = true;
        CapabilityBoundingSet = "";
        AmbientCapabilities = "";
        LockPersonality = true;
        MemoryDenyWriteExecute = true;
        DevicePolicy = "closed";
        PrivateDevices = true;
        PrivateNetwork = true;
        PrivateTmp = true;
        ProcSubset = "pid";
        ProtectClock = true;
        ProtectControlGroups = true;
        ProtectHome = true;
        ProtectHostname = true;
        ProtectKernelLogs = true;
        ProtectKernelModules = true;
        ProtectKernelTunables = true;
        ProtectProc = "invisible";
        ProtectSystem = "strict";
        RemoveIPC = true;
        RestrictAddressFamilies = ["AF_UNIX"];
        RestrictNamespaces = true;
        RestrictRealtime = true;
        RestrictSUIDSGID = true;
        SystemCallArchitectures = "native";
        SystemCallErrorNumber = "EPERM";
        SystemCallFilter = ["@system-service" "~@privileged" "~@resources"];
      };
    };
  };
}
