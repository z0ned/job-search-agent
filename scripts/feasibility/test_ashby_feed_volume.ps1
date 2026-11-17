<#
Sprint 1 read-only Ashby public-feed volume test.
No API keys, no Adzuna usage, no production application code.
Run: powershell -NoProfile -File .\scripts\feasibility\test_ashby_feed_volume.ps1
Optional: powershell -NoProfile -File .\scripts\feasibility\test_ashby_feed_volume.ps1 -Days 7
#>
[CmdletBinding()]
param(
    [ValidateRange(1,365)][int]$Days = 30,
    [string[]]$Boards = @("ramp", "junipersquare", "greenlight-workforce-solutions", "coder", "teamworks")
)
$ErrorActionPreference = "Stop"
$cutoff = [DateTimeOffset]::UtcNow.AddDays(-$Days)
$rows = @()
Write-Host "Ashby feed access and count check. One public GET per employer board."
Write-Host "UTC start: $([DateTimeOffset]::UtcNow.ToString('u')); age window: $Days days"

foreach ($board in $Boards) {
    if ($board -notmatch '^[a-zA-Z0-9_-]+$') {
        Write-Warning "Skipping invalid board slug"
        continue
    }
    $url = "https://api.ashbyhq.com/posting-api/job-board/$board"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -Headers @{Accept="application/json"} -TimeoutSec 45 -UseBasicParsing -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        if ($null -eq $data -or $null -eq $data.jobs) {
            throw "No jobs array in feed"
        }
        $jobs = @($data.jobs | Where-Object { $null -ne $_ })
        $listed = @($jobs | Where-Object { $_.isListed -ne $false })
        $ids = @($listed | ForEach-Object { $_.id } | Where-Object { $_ } | Sort-Object -Unique)
        $recent = 0
        $unknownDate = 0
        $contractSignals = 0
        $typeLabels = @{}

        foreach ($j in $listed) {
            $type = [string]$j.employmentType
            if ([string]::IsNullOrWhiteSpace($type)) { $type = "(missing)" }
            if (-not $typeLabels.ContainsKey($type)) { $typeLabels[$type] = 0 }
            $typeLabels[$type]++
            if ($type -match "contract|temporary" -or [string]$j.title -match "contract|temporary") {
                $contractSignals++
            }
            if ([string]::IsNullOrWhiteSpace([string]$j.publishedAt)) {
                $unknownDate++
            } else {
                try {
                    $date = [DateTimeOffset]::Parse([string]$j.publishedAt, [Globalization.CultureInfo]::InvariantCulture)
                    if ($date.ToUniversalTime() -ge $cutoff) { $recent++ }
                } catch {
                    $unknownDate++
                }
            }
        }
        $sw.Stop()
        $types = (($typeLabels.Keys | Sort-Object | ForEach-Object {
            "{0}:{1}" -f $_, $typeLabels[$_]
        }) -join "; ")
        $rows += [pscustomobject]@{
            Board=$board; Status="OK"; HTTP=[int]$response.StatusCode
            Returned=$jobs.Count; Listed=$listed.Count; UniqueIDs=$ids.Count
            Recent30=$recent; DateUnknown=$unknownDate; ContractSignal=$contractSignals
            Types=$types; Seconds=[math]::Round($sw.Elapsed.TotalSeconds,1)
        }
    } catch {
        $sw.Stop()
        $rows += [pscustomobject]@{
            Board=$board; Status="FAILED"; HTTP=""
            Returned=""; Listed=""; UniqueIDs=""; Recent30=""; DateUnknown=""
            ContractSignal=""; Types=""; Seconds=[math]::Round($sw.Elapsed.TotalSeconds,1)
        }
        Write-Warning ("Failed to retrieve {0} ({1})" -f $board,$_.Exception.GetType().Name)
    }
}
Write-Host ""
$rows | Format-Table Board,Status,HTTP,Returned,Listed,UniqueIDs,Recent30,DateUnknown,ContractSignal,Seconds -AutoSize
Write-Host "Employment-type labels from feeds:"
foreach($row in $rows) { Write-Host ("{0}: {1}" -f $row.Board,$row.Types) }
$valid=@($rows | Where-Object {$_.Status -eq "OK"})
Write-Host ("Successful boards: {0} / {1}" -f $valid.Count,$rows.Count)
Write-Host ("Listed postings across boards: {0}" -f (($valid | Measure-Object Listed -Sum).Sum))
Write-Host ("Published in last {0} days: {1}" -f $Days,(($valid | Measure-Object Recent30 -Sum).Sum))
Write-Host ("Contract title/type signals: {0}" -f (($valid | Measure-Object ContractSignal -Sum).Sum))
Write-Host "Not all Ashby jobs. Contract signals can undercount. Run again another day to test stability."
