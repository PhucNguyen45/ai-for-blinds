<#
.SYNOPSIS
  Kiểm môi trường build rồi dựng APK SgBe để cài lên điện thoại Android.

.DESCRIPTION
  Chạy từ thư mục frontend:  powershell -ExecutionPolicy Bypass -File tool\kiem_va_build.ps1
  Các bước (bước nào trượt thì dừng và nói rõ cách sửa):
    1. Flutter, Dart, JDK, Android SDK (flutter doctor) - chỉ bắt buộc phần Android.
    2. Thiết bị đang cắm / máy ảo (adb devices) - không bắt buộc.
    3. flutter pub get, flutter analyze, flutter test (bỏ test cần máy chủ thật).
    4. flutter build apk --release --split-per-abi: mỗi loại chip một APK nhỏ.
       Điện thoại thật gần như luôn dùng bản arm64-v8a.

.PARAMETER Demo
  Bật sẵn chế độ demo (không cần máy chủ) trong APK.
.PARAMETER BoQuaTest
  Bỏ qua bước analyze và test (chỉ dùng khi vừa chạy xong).
.PARAMETER CaiLenMay
  Build xong thì cài luôn lên thiết bị đang cắm (adb install).
#>
param([switch]$Demo, [switch]$BoQuaTest, [switch]$CaiLenMay)

$ErrorActionPreference = 'Continue'
$frontend = Split-Path -Parent $PSScriptRoot
Set-Location $frontend
$ketQua = @()

function Buoc($ten) { Write-Host ''; Write-Host "== $ten" -ForegroundColor Cyan }
function Dat($ten, $chiTiet) { $script:ketQua += [pscustomobject]@{ Buoc = $ten; KetQua = 'DAT'; ChiTiet = $chiTiet }; Write-Host "  DAT  $chiTiet" -ForegroundColor Green }
function Truot($ten, $chiTiet) {
  $script:ketQua += [pscustomobject]@{ Buoc = $ten; KetQua = 'TRUOT'; ChiTiet = $chiTiet }
  Write-Host "  TRUOT  $chiTiet" -ForegroundColor Red
  $script:ketQua | Format-Table -AutoSize
  exit 1
}
function CanhBao($ten, $chiTiet) { $script:ketQua += [pscustomobject]@{ Buoc = $ten; KetQua = 'LUU Y'; ChiTiet = $chiTiet }; Write-Host "  LUU Y  $chiTiet" -ForegroundColor Yellow }

# 1. Flutter
Buoc 'Flutter và Android SDK'
if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
  if (Test-Path 'C:\src\flutter\bin\flutter.bat') { $env:Path = 'C:\src\flutter\bin;' + $env:Path }
  else { Truot 'Flutter' 'Không thấy lệnh flutter. Cài Flutter vào C:\src\flutter hoặc thêm flutter\bin vào PATH.' }
}
$ver = (flutter --version 2>$null | Select-Object -First 1)
Dat 'Flutter' $ver

$doctor = flutter doctor 2>$null | Out-String
$android = ($doctor -split "`n" | Where-Object { $_ -match 'Android toolchain' } | Select-Object -First 1)
if ($android -match '\[X\]') { Truot 'Android SDK' "flutter doctor: $($android.Trim()). Mở Android Studio > SDK Manager cài Android SDK." }
elseif ($android -match '\[!\]') {
  if ($doctor -match 'licenses not accepted') { CanhBao 'Android SDK' 'Còn license Android SDK chưa chấp nhận: tự chạy  flutter doctor --android-licenses  và đọc rồi gõ y.' }
  else { CanhBao 'Android SDK' $android.Trim() }
} else { Dat 'Android SDK' $android.Trim() }
$java = (flutter doctor -v 2>$null | Select-String 'Java version' | Select-Object -First 1)
if ($java) { Dat 'JDK' ($java.ToString().Trim() -replace '^\W+', '') } else { CanhBao 'JDK' 'Không đọc được phiên bản Java (cần JDK 17 trở lên; Android Studio có sẵn).' }

# 2. Thiết bị
Buoc 'Thiết bị'
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
$thietBi = @()
if (Test-Path $adb) {
  # @(...): khi chỉ có một thiết bị, PowerShell 5.1 trả về chuỗi chứ không phải mảng
  $thietBi = @(& $adb devices | Select-Object -Skip 1 | Where-Object { $_ -match '\tdevice$' } | ForEach-Object { ($_ -split "`t")[0] })
  if ($thietBi.Count -gt 0) { Dat 'Thiết bị' ("Đang cắm: " + ($thietBi -join ', ')) }
  else { CanhBao 'Thiết bị' 'Chưa có điện thoại/máy ảo. Điện thoại: bật Tùy chọn nhà phát triển > Gỡ lỗi USB rồi cắm cáp.' }
} else { CanhBao 'Thiết bị' "Không thấy adb ở $adb" }

# 3. Mã nguồn
Buoc 'Thư viện, phân tích mã, test'
flutter pub get *> $null
if ($LASTEXITCODE -ne 0) { Truot 'pub get' 'flutter pub get lỗi: kiểm tra mạng hoặc pubspec.yaml.' }
Dat 'pub get' 'Đủ thư viện'
if (-not $BoQuaTest) {
  $an = flutter analyze 2>&1 | Out-String
  if ($LASTEXITCODE -ne 0) { Write-Host $an; Truot 'analyze' 'flutter analyze còn lỗi (xem trên).' }
  Dat 'analyze' 'Không có lỗi'
  $t = flutter test --exclude-tags live 2>&1 | Out-String
  $dong = ($t -split "`n" | Where-Object { $_ -match '^\d\d:\d\d \+' } | Select-Object -Last 1)
  if ($LASTEXITCODE -ne 0) { Write-Host $t; Truot 'test' "Có test trượt: $dong" }
  Dat 'test' ($dong.Trim() -replace '^\d\d:\d\d ', '')
}

# 4. Build
Buoc 'Dựng APK release'
$buildArgs = @('build', 'apk', '--release', '--split-per-abi')
if ($Demo) { $buildArgs += '--dart-define=SGBE_DEMO=true' }
$sw = [Diagnostics.Stopwatch]::StartNew()
flutter @buildArgs 2>&1 | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { Truot 'build' 'flutter build apk lỗi (xem trên).' }
$apkDir = Join-Path $frontend 'build\app\outputs\flutter-apk'
$arm64 = Join-Path $apkDir 'app-arm64-v8a-release.apk'
Get-ChildItem $apkDir -Filter '*-release.apk' | ForEach-Object { Write-Host ("  {0}  {1:N1} MB" -f $_.Name, ($_.Length / 1MB)) }
Dat 'build' ("Xong sau {0:N0} giây. Bản cho điện thoại: {1}" -f $sw.Elapsed.TotalSeconds, $arm64)

if ($CaiLenMay -and $thietBi.Count -gt 0) {
  Buoc 'Cài lên thiết bị'
  $dich = $thietBi[0]
  $abi = (& $adb -s $dich shell getprop ro.product.cpu.abi).Trim()
  $apk = Join-Path $apkDir "app-$abi-release.apk"
  if (-not (Test-Path $apk)) { $apk = $arm64 }
  & $adb -s $dich install -r $apk
  if ($LASTEXITCODE -ne 0) { Truot 'cài đặt' "adb install lỗi trên $dich." }
  Dat 'cài đặt' "Đã cài $([IO.Path]::GetFileName($apk)) lên $dich ($abi)"
}

Write-Host ''
$script:ketQua | Format-Table -AutoSize
