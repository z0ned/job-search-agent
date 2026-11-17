<#
Sprint 1 Himalayas: verify filtered page 2 and compare sampled GUIDs across days.
One public GET per page: 2 queries x 2 pages = 4 requests per run.
First run saves GUID-only snapshot; subsequent run compares it and rolls the
baseline forward when >=24 hours have passed. The local .local-test-data folder
is Git-ignored. No credentials, Adzuna calls, job evaluations or application actions.
IMPORTANT: new GUID in a top-40 sample is not proof of a newly published job.
Run (from repo root):
 powershell -NoProfile -File .\scripts\feasibility\test_himalayas_daily_delta.ps1
To deliberately start over, add -ResetBaseline.
#>
[CmdletBinding()]
param([switch]$ResetBaseline)
$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$localDir = Join-Path $repoRoot ".local-test-data"
$snapshotFile = Join-Path $localDir "himalayas_pm_contract_page_samples.json"
$now = [DateTimeOffset]::UtcNow
$cutoff = $now.AddDays(-30)
$signature = "country=US;type=Contractor,Temporary;sort=recent;page=1,2;q=project manager|program manager"
$queries = @(
    [pscustomobject]@{ Name="PROJECT_MANAGER"; Text="project manager" },
    [pscustomobject]@{ Name="PROGRAM_MANAGER"; Text="program manager" }
)
function New-StringSet {
    param([object[]]$Items)
    $set = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach($item in @($Items)) {
        if(-not [string]::IsNullOrWhiteSpace([string]$item)) { [void]$set.Add([string]$item) }
    }
    # PowerShell enumerates collection return values unless wrapped.
    return ,$set
}
function Get-CountryClass {
    param([object]$Restrictions)
    if($null -eq $Restrictions) { return "Unknown" }
    $items = @($Restrictions | Where-Object { $null -ne $_ })
    if($items.Count -eq 0) { return "Worldwide" }
    foreach($item in $items) {
        if($item -is [string]) { $tokens = @([string]$item) }
        else { $tokens = @([string]$item.alpha2,[string]$item.name,[string]$item.slug) }
        foreach($token in $tokens) {
            if($token -match '(?i)^(us|usa|united states|united-states)$') { return "USExplicit" }
        }
    }
    return "Other"
}
function Parse-PubDate {
    param([object]$Value)
    try {
        if([string]::IsNullOrWhiteSpace([string]$Value)) { return $null }
        $seconds=[long]$Value
        if($seconds -lt 946684800 -or $seconds -gt 253402300799) { return $null }
        return [DateTimeOffset]::FromUnixTimeSeconds($seconds).ToUniversalTime()
    } catch { return $null }
}

Write-Host "Himalayas filtered pagination + repeat-day ID test (4 public GETs)"
Write-Host "UTC: $($now.ToString('u'))"
Write-Host "Date caution: pubDate means LAST UPDATE, not first published."

$prior = $null
if((Test-Path -LiteralPath $snapshotFile) -and -not $ResetBaseline) {
    $prior = Get-Content -LiteralPath $snapshotFile -Raw | ConvertFrom-Json
    if($null -eq $prior -or [int]$prior.version -ne 1 -or [string]$prior.signature -ne $signature) {
        throw "Old snapshot has incompatible parameters; inspect it or use -ResetBaseline explicitly."
    }
}

$rows = @()
$newQueries = @()
$union = New-StringSet @()
try {
    foreach($q in $queries) {
        $ids = New-StringSet @()
        $pageSizes = @()
        $totalCount = $null
        $us = 0
        $worldwide = 0
        $titleSignal = 0
        $updatedKnown = 0
        $updatedRecent = 0

        foreach($page in @(1,2)) {
            $parameters = @(
                "country=US",
                "employment_type=$([Uri]::EscapeDataString('Contractor,Temporary'))",
                "sort=recent",
                "q=$([Uri]::EscapeDataString([string]$q.Text))",
                "page=$page"
            )
            $url = "https://himalayas.app/jobs/api/search?" + ($parameters -join "&")
            $response = Invoke-WebRequest -Uri $url -Method Get -Headers @{Accept="application/json"} -TimeoutSec 45 -UseBasicParsing -ErrorAction Stop
            if([int]$response.StatusCode -ne 200) { throw "Unexpected HTTP status" }
            $data = $response.Content | ConvertFrom-Json
            if($null -eq $data -or $data.PSObject.Properties.Name -notcontains "jobs" -or $null -eq $data.totalCount) {
                throw "Missing jobs or totalCount in response"
            }
            if($null -eq $totalCount) { $totalCount = [int]$data.totalCount }
            elseif($totalCount -ne [int]$data.totalCount) {
                Write-Warning ("{0}: totalCount changed between pages" -f $q.Name)
            }
            $jobs = @($data.jobs | Where-Object { $null -ne $_ })
            if($jobs.Count -gt 20) { throw "Unexpected sample page size over 20" }
            $pageSizes += $jobs.Count
            foreach($job in $jobs) {
                $id = [string]$job.guid
                if([string]::IsNullOrWhiteSpace($id)) { throw "Missing job GUID" }
                if(-not $ids.Add($id)) {
                    throw ("{0}: same GUID found twice across page 1 and page 2; pagination not validated" -f $q.Name)
                }
                [void]$union.Add($id)
                if([string]$job.employmentType -notin @("Contractor","Temporary")) {
                    throw ("{0}: employment_type filter mismatch" -f $q.Name)
                }
                $geo = Get-CountryClass $job.locationRestrictions
                if($geo -eq "USExplicit") { $us++ }
                elseif($geo -eq "Worldwide") { $worldwide++ }
                else { throw ("{0}: country filter mismatch" -f $q.Name) }
                if([string]$job.title -match '(?i)\b(project|program|product|portfolio|pmo|implementation|transformation|delivery)\b') {
                    $titleSignal++
                }
                $updated = Parse-PubDate $job.pubDate
                if($null -ne $updated) {
                    $updatedKnown++
                    if($updated -ge $cutoff) { $updatedRecent++ }
                }
            }
        }
        $idList = @($ids | Sort-Object)
        $newQueries += [pscustomobject]@{
            name=$q.Name
            reportedCount=$totalCount
            ids=$idList
        }
        $rows += [pscustomobject]@{
            Search=$q.Name; Reported=$totalCount
            Page1=$pageSizes[0]; Page2=$pageSizes[1]
            Distinct=$idList.Count; US=$us; Worldwide=$worldwide
            RoleTitle=$titleSignal; UpdatedKnown=$updatedKnown; Updated30=$updatedRecent
        }
    }
}
catch {
    Write-Warning ("Himalayas fetch/validation failed: {0}" -f $_.Exception.Message)
    Write-Host "Local baseline untouched; stop if rate limited (HTTP 429)."
    exit 1
}

Write-Host ""
Write-Host "PAGE 1 / PAGE 2 VALIDATION RESULTS:"
$rows | Format-Table Search,Reported,Page1,Page2,Distinct,US,Worldwide,RoleTitle,UpdatedKnown,Updated30 -AutoSize
Write-Host ("Union of distinct GUIDs across both keyword searches: {0}" -f $union.Count)
Write-Host "Zero duplicate GUIDs per query across page 1 and page 2; contract & country filters checked."

$current = [pscustomobject]@{
    version=1; signature=$signature
    capturedAtUtc=$now.ToString("o")
    searches=$newQueries
}
if($null -eq $prior) {
    if(-not (Test-Path -LiteralPath $localDir)) {
        New-Item -ItemType Directory -Path $localDir -Force | Out-Null
    }
    $current | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $snapshotFile -Encoding UTF8
    Write-Host ""
    Write-Host "BASELINE SAVED: .local-test-data/himalayas_pm_contract_page_samples.json"
    Write-Host "Run the exact same command after 24+ hours to measure changed sampled GUIDs."
}
else {
    $priorTime = [DateTimeOffset]::Parse([string]$prior.capturedAtUtc)
    $elapsedHours = ($now - $priorTime).TotalHours
    if($elapsedHours -lt 0) { throw "Snapshot UTC date is in the future; check your clock." }
    $oldUnion = New-StringSet @()
    foreach($old in @($prior.searches)) {
        foreach($id in @($old.ids)) { [void]$oldUnion.Add([string]$id) }
    }
    $differences = @()
    foreach($new in $newQueries) {
        $matches = @($prior.searches | Where-Object { $_.name -eq $new.name })
        if($matches.Count -ne 1) { throw "Snapshot missing matching query; reset manually." }
        $old = $matches[0]
        $oldSet = New-StringSet @($old.ids)
        $newSet = New-StringSet @($new.ids)
        $added = @($new.ids | Where-Object { -not $oldSet.Contains([string]$_) }).Count
        $removed = @($old.ids | Where-Object { -not $newSet.Contains([string]$_) }).Count
        $differences += [pscustomobject]@{
            Search=$new.name; Previous=$oldSet.Count; Current=$newSet.Count
            NewToSample=$added; LeftSample=$removed
            ReportedBefore=$old.reportedCount; ReportedNow=$new.reportedCount
        }
    }
    Write-Host ""
    Write-Host ("CHANGES FROM LOCAL SNAPSHOT ({0:N1} hours earlier):" -f $elapsedHours)
    $differences | Format-Table -AutoSize
    $addedUnion = @($union | Where-Object { -not $oldUnion.Contains([string]$_) }).Count
    $removedUnion = @($oldUnion | Where-Object { -not $union.Contains([string]$_) }).Count
    Write-Host ("Across-query union: new-to-sample GUIDs={0}; no-longer-in-sample GUIDs={1}" -f $addedUnion,$removedUnion)
    Write-Host "A job may enter the sampled top 40 because of an update, not first publication."
    if($elapsedHours -ge 24) {
        $current | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $snapshotFile -Encoding UTF8
        Write-Host "Daily comparison complete; local reference updated to this run."
    } else {
        Write-Warning "Less than 24 hours elapsed; snapshot NOT advanced (not a daily-refresh test)."
    }
}
Write-Host "No job descriptions stored; no credentials or Adzuna calls used."
