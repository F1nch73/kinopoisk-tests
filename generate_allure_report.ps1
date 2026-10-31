# Генерация Allure-отчёта по результатам тестов.
#
# Использование:
#   .\generate_allure_report.ps1
#   .\generate_allure_report.ps1 -Target "tests"
#   .\generate_allure_report.ps1 -Target "api_tests"
#   .\generate_allure_report.ps1 -Open
param(
    [string]$Target = ".",
    [string]$ResultsDir = "allure-results",
    [string]$ReportDir  = "allure-report",
    [switch]$Open
)

$ErrorActionPreference = "Stop"

Write-Host "=== Запуск тестов ===" -ForegroundColor Cyan
Write-Host "Цель: $Target"
Write-Host "Результаты: $ResultsDir"
Write-Host "Отчёт: $ReportDir"
Write-Host ""

python -m pytest $Target --alluredir=$ResultsDir --clean-alluredir
$testExitCode = $LASTEXITCODE

if ($testExitCode -ne 0) {
    Write-Warning "Тесты завершены с кодом $testExitCode"
}

Write-Host ""
Write-Host "=== Генерация отчёта ===" -ForegroundColor Cyan

if (Get-Command allure -ErrorAction SilentlyContinue) {
    allure generate $ResultsDir -o $ReportDir --clean
    $generateExitCode = $LASTEXITCODE

    if ($generateExitCode -eq 0) {
        $reportPath = (Resolve-Path $ReportDir).Path
        Write-Host ""
        Write-Host "Отчёт сгенерирован: $reportPath" -ForegroundColor Green
        Write-Host "Для открытия выполните:" -ForegroundColor Yellow
        Write-Host "  allure open $reportPath" -ForegroundColor Yellow

        if ($Open) {
            Write-Host "Открываю отчёт в браузере..." -ForegroundColor Cyan
            Start-Process allure "open $reportPath"
        }
    } else {
        Write-Warning "Ошибка генерации отчёта"
    }
} else {
    Write-Warning "Allure CLI не найден."
    Write-Host "Результаты тестов сохранены в: $ResultsDir"
}

exit $testExitCode
