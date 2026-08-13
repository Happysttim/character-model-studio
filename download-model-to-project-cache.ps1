[CmdletBinding()]
param(
    [ValidateSet(
        'required', 'hunyuan2-shape', 'hunyuan2gp-shape', 'hunyuan2gp-texture', 'sf3d',
        'unirig', 'unirig-skeleton', 'unirig-skinning', 'unirig-transformer'
    )]
    [string[]]$Model = @('required'),
    [switch]$AllOptional
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$dataRoot = Join-Path $projectRoot '.local'
$cacheRoot = Join-Path $dataRoot 'cache'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$env:CHARACTER_MODEL_STUDIO_DATA_DIR = $dataRoot
$env:HF_HOME = Join-Path $cacheRoot 'huggingface'
$env:U2NET_HOME = Join-Path $cacheRoot 'segmentation\rembg'

function Get-HfCli {
    $command = Get-Command hf -ErrorAction SilentlyContinue
    if ($null -eq $command) { throw "Hugging Face CLI 'hf' is required." }
    return $command.Source
}

function Download-Model([string]$Repository, [string[]]$Include, [string]$Destination) {
    $hf = Get-HfCli
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $arguments = @('download', $Repository, '--local-dir', $Destination)
    foreach ($pattern in $Include) { $arguments += @('--include', $pattern) }
    Write-Host "Downloading $Repository to $Destination"
    & $hf @arguments
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $Repository" }
}

if ($AllOptional) {
    $Model += @(
        'hunyuan2-shape', 'hunyuan2gp-shape', 'hunyuan2gp-texture', 'sf3d',
        'unirig', 'unirig-transformer'
    )
}
foreach ($selected in ($Model | Select-Object -Unique)) {
    switch ($selected) {
        'required' {
            if (-not (Test-Path $python)) { throw 'Project virtual environment is missing.' }
            & $python -m character_model_studio.tools.download_segmentation_model --model isnet-anime
            if ($LASTEXITCODE -ne 0) { throw 'Required segmentation model setup failed.' }
        }
        'hunyuan2-shape' { Download-Model 'tencent/Hunyuan3D-2' @('hunyuan3d-dit-v2-0/*') (Join-Path $cacheRoot 'hunyuan3d-2') }
        'hunyuan2gp-shape' { Download-Model 'tencent/Hunyuan3D-2mv' @('hunyuan3d-dit-v2-mv/*') (Join-Path $cacheRoot 'hunyuan3d-2gp\tencent\Hunyuan3D-2mv') }
        'hunyuan2gp-texture' { Download-Model 'tencent/Hunyuan3D-2' @('hunyuan3d-delight-v2-0/*', 'hunyuan3d-paint-v2-0/*') (Join-Path $cacheRoot 'hunyuan3d-2gp\tencent\Hunyuan3D-2') }
        'sf3d' { Download-Model 'stabilityai/stable-fast-3d' @('config.yaml', 'model.safetensors') (Join-Path $cacheRoot 'sf3d\stable-fast-3d') }
        'unirig' {
            Download-Model 'VAST-AI/UniRig' @(
                'skeleton/articulation-xl_quantization_256/model.ckpt',
                'skin/articulation-xl/model.ckpt'
            ) (Join-Path $cacheRoot 'unirig')
            Download-Model 'facebook/opt-350m' @(
                'config.json', 'generation_config.json', 'merges.txt', 'special_tokens_map.json',
                'tokenizer_config.json', 'vocab.json'
            ) (Join-Path $cacheRoot 'unirig\transformers\facebook-opt-350m')
        }
        'unirig-skeleton' {
            Download-Model 'VAST-AI/UniRig' @('skeleton/articulation-xl_quantization_256/model.ckpt') (Join-Path $cacheRoot 'unirig')
        }
        'unirig-skinning' {
            Download-Model 'VAST-AI/UniRig' @('skin/articulation-xl/model.ckpt') (Join-Path $cacheRoot 'unirig')
        }
        'unirig-transformer' {
            # UniRig loads OPT architecture/tokenizer metadata locally; it does not use OPT weights.
            Download-Model 'facebook/opt-350m' @(
                'config.json', 'generation_config.json', 'merges.txt', 'special_tokens_map.json',
                'tokenizer_config.json', 'vocab.json'
            ) (Join-Path $cacheRoot 'unirig\transformers\facebook-opt-350m')
        }
    }
}
Write-Host 'Done. Restart the application to refresh provider readiness.'
