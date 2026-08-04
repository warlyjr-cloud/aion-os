{
  lib,
  python312Packages,
}:
python312Packages.buildPythonApplication {
  pname = "aion-os";
  version = "0.1.0";
  src = ../.;
  pyproject = true;

  build-system = with python312Packages; [hatchling];
  dependencies = with python312Packages; [
    pydantic
    typer
    anthropic
    fastapi
    uvicorn
    jinja2
    httpx
    fusepy
  ];
  nativeCheckInputs = with python312Packages; [
    hypothesis
    pytestCheckHook
    pytest-cov
  ];

  pythonImportsCheck = ["aionctl" "aiond" "tcb" "vek"];
  doCheck = false;

  meta = {
    description = "Safe and verifiable evolution engine for NixOS";
    homepage = "https://github.com/warlyjr-cloud/aion-os";
    license = lib.licenses.asl20;
    mainProgram = "aionctl";
    platforms = lib.platforms.linux;
  };
}
