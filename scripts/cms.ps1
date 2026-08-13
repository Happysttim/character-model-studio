[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet(
        'bootstrap', 'run', 'format', 'lint', 'typecheck', 'test', 'test-ui', 'test-storage',
        'test-capture', 'test-ai-mock', 'test-provider-compatibility', 'test-gpu',
        'test-segmentation', 'download-segmentation-model', 'test-sf3d', 'test-sf3d-workflow',
        'test-reconstruction', 'test-rigging', 'test-animation', 'test-model-validation',
        'test-rigged-model-validation', 'test-integration', 'build', 'package', 'verify'
    )]
    [string]$Command
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw 'The project virtual environment is missing. Run `uv venv --python 3.11 .venv` first.'
}

Push-Location $projectRoot
try {
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    $env:CHARACTER_MODEL_STUDIO_DATA_DIR = Join-Path $projectRoot '.local'
    $env:HY3DGEN_MODELS = Join-Path $env:CHARACTER_MODEL_STUDIO_DATA_DIR 'cache\hunyuan3d-2'
    $env:HF_HOME = Join-Path $env:CHARACTER_MODEL_STUDIO_DATA_DIR 'cache\huggingface'
    $env:U2NET_HOME = Join-Path $env:CHARACTER_MODEL_STUDIO_DATA_DIR 'cache\segmentation\rembg'

    function Invoke-ProjectPython {
        param([string[]]$Arguments)

        & $python @Arguments
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    switch ($Command) {
        'bootstrap' { Invoke-ProjectPython @('-m', 'character_model_studio.tools.bootstrap') }
        'run' { Invoke-ProjectPython @('-m', 'character_model_studio') }
        'format' { Invoke-ProjectPython @('-m', 'ruff', 'format', 'src', 'tests') }
        'lint' { Invoke-ProjectPython @('-m', 'ruff', 'check', 'src', 'tests') }
        'typecheck' { Invoke-ProjectPython @('-m', 'mypy') }
        'test' { Invoke-ProjectPython @('-m', 'pytest') }
        'test-ui' { Invoke-ProjectPython @('-m', 'pytest', 'tests/ui') }
        'test-storage' { Invoke-ProjectPython @('-m', 'pytest', 'tests/test_database.py', 'tests/test_paths.py') }
        'test-capture' { Invoke-ProjectPython @('-m', 'pytest', 'tests/test_capture.py') }
        'test-ai-mock' { Invoke-ProjectPython @('-m', 'pytest', 'tests/test_mock_workflow.py') }
        'test-provider-compatibility' { Invoke-ProjectPython @('-m', 'character_model_studio.tools.provider_compatibility') }
        'test-gpu' { Invoke-ProjectPython @('-m', 'character_model_studio.tools.gpu_smoke') }
        'test-segmentation' { Invoke-ProjectPython @('-m', 'character_model_studio.tools.segmentation_smoke') }
        'test-sf3d' { Invoke-ProjectPython @('-m', 'character_model_studio.tools.sf3d_smoke') }
        'test-sf3d-workflow' { Invoke-ProjectPython @('-m', 'character_model_studio.tools.sf3d_workflow_smoke') }
        'download-segmentation-model' {
            Invoke-ProjectPython @('-m', 'character_model_studio.tools.download_segmentation_model')
        }
        'test-reconstruction' {
            Invoke-ProjectPython @('-m', 'character_model_studio.tools.reconstruction_smoke')
            Invoke-ProjectPython @('-m', 'character_model_studio.tools.real_workflow_smoke')
        }
        'test-model-validation' { Invoke-ProjectPython @('-m', 'pytest', 'tests/test_model_validation.py') }
        'test-rigging' { Invoke-ProjectPython @('-m', 'pytest', 'tests/test_rigging.py', 'tests/test_mock_workflow.py') }
        'test-integration' { Invoke-ProjectPython @('-m', 'pytest', 'tests/test_integration.py') }
        'build' { Invoke-ProjectPython @('packaging/build.py') }
        'package' { Invoke-ProjectPython @('packaging/build.py') }
        'verify' {
            Invoke-ProjectPython @('-m', 'ruff', 'format', '--check', 'src', 'tests')
            Invoke-ProjectPython @('-m', 'ruff', 'check', 'src', 'tests')
            Invoke-ProjectPython @('-m', 'mypy')
            Invoke-ProjectPython @('-m', 'pytest')
        }
        default {
            throw "'$Command' is intentionally deferred to its assigned implementation phase."
        }
    }
}
finally {
    Pop-Location
}
