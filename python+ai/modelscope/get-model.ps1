# 默认选项
$defaultPublisher = "Tencent-Hunyuan"
$defaultRepo = "Hy-MT2-7B-GGUF"
$defaultModel = "Hy-MT2-7B-Q4_K_M.gguf"

$msPath = ".\.venv\Scripts\modelscope.exe" # modelscope.exe 的路径
$downloadPath = "$env:USERPROFILE\.lmstudio\models" # 模型下载路径

# input
$publisher = Read-Host "请输入模型提供商（直接回车用默认：$defaultPublisher）"
$repo = Read-Host "请输入 ModelScope 仓库（直接回车用默认：$defaultRepo）"
$model = Read-Host "请输入模型文件（直接回车用默认：$defaultModel）"

# format and trim input
$publisher = "$publisher".Trim().Trim('"').Trim("'")
$repo = "$repo".Trim().Trim('"').Trim("'")
$model = "$model".Trim().Trim('"').Trim("'")
if ([string]::IsNullOrWhiteSpace($publisher)) { $publisher = $defaultPublisher }
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = $defaultRepo }
if ([string]::IsNullOrWhiteSpace($model)) { $model = $defaultModel }

# 创建下载目录
if (-Not (Test-Path $downloadPath)) { New-Item -ItemType Directory -Path $downloadPath }

# 创建发布者目录
$publisherPath = Join-Path -Path $downloadPath -ChildPath $publisher
if (-Not (Test-Path $publisherPath)) { New-Item -ItemType Directory -Path $publisherPath }

# 创建仓库目录  
$repoPath = Join-Path -Path $publisherPath -ChildPath $repo
if (-Not (Test-Path $repoPath)) { New-Item -ItemType Directory -Path $repoPath }

Write-Host "开始下载：$publisher/$repo/$model" -ForegroundColor Cyan
& $msPath download --model $publisher/$repo $model --local_dir $repoPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n下载完成! 请在 LM Studio 的 'My Models' 中刷新查看." -ForegroundColor Green
} else {
    Write-Host "`n下载失败, 请检查网络连接或 modelscope.exe 路径是否正确." -ForegroundColor Red
}