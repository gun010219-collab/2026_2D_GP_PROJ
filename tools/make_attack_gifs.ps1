
param(
    [Parameter(Mandatory)] [string[]]$Runs,
    [Parameter(Mandatory)] [string]$Output,
    [string]$Python = '.\.venv\Scripts\python.exe',
    [string]$BeforeLabel = 'BEFORE',
    [string]$AfterLabel = 'ARTICULATED'
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$null = New-Item -ItemType Directory -Path $Output -Force
$temp = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ('checkmate-gif-' + [guid]::NewGuid()))
$font = [System.Drawing.Font]::new('Segoe UI', 10)
$encode = Join-Path $PSScriptRoot 'pack_attack_gif.py'

try {
    foreach ($run in $Runs) {
        foreach ($clip in Get-ChildItem -LiteralPath (Join-Path $run 'clips') -Directory) {
            $frames = New-Item -ItemType Directory -Path (Join-Path $temp.FullName $clip.Name)
            foreach ($previous in Get-ChildItem -LiteralPath $clip.FullName -Filter '*_previous.png') {
                $afterFile = Join-Path $clip.FullName ($previous.Name.Replace('_previous', '_articulated'))
                $after = [System.Drawing.Image]::FromFile($afterFile)
                $before = [System.Drawing.Image]::FromFile($previous.FullName)
                $canvas = [System.Drawing.Bitmap]::new(532, 208)
                $graphics = [System.Drawing.Graphics]::FromImage($canvas)
                try {
                    $graphics.Clear([System.Drawing.Color]::FromArgb(24, 24, 26))
                    $graphics.DrawString($BeforeLabel, $font, [System.Drawing.Brushes]::White, 7, 2)
                    $graphics.DrawString($AfterLabel, $font, [System.Drawing.Brushes]::Gold, 275, 2)
                    $graphics.DrawImageUnscaled($before, 0, 24)
                    $graphics.DrawImageUnscaled($after, 268, 24)
                    $canvas.Save((Join-Path $frames.FullName ($previous.BaseName + '.gif')),
                                 [System.Drawing.Imaging.ImageFormat]::Gif)
                } finally {
                    $graphics.Dispose()
                    $canvas.Dispose()
                    $before.Dispose()
                    $after.Dispose()
                }
            }
            $gif = Join-Path $Output ($clip.Name + '.gif')
            & $Python $encode $frames.FullName $gif
            if ($LASTEXITCODE -ne 0) { throw "GIF encoding failed for $($clip.Name)" }
            $encoded = [System.Drawing.Image]::FromFile($gif)
            try {
                $count = $encoded.GetFrameCount([System.Drawing.Imaging.FrameDimension]::Time)
                if ($count -ne @(Get-ChildItem -LiteralPath $frames.FullName).Count) {
                    throw "Frame count mismatch for $gif"
                }
                Write-Output "$($clip.Name) $count frames at 30 fps"
            } finally {
                $encoded.Dispose()
            }
        }
    }
} finally {
    $font.Dispose()
    # The temporary path contains only this run's intermediate converted frames.
    $resolved = (Resolve-Path -LiteralPath $temp.FullName).Path
    $prefix = (Resolve-Path -LiteralPath $env:TEMP).Path + '\checkmate-gif-'
    if ($resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $resolved -Recurse
    }
}
