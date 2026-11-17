<#
Sprint 1 read-only Greenhouse feed volume test: one public GET per employer board.
No API keys, no Adzuna calls, no files written. Doesn't evaluate job suitability.
Run: powershell -NoProfile -File .\scripts\feasibility\test_greenhouse_feed_volume.ps1
Run: powershell -NoProfile -File .\scripts\feasibility\test_greenhouse_feed_volume.ps1 -Days 7
NOTE: updated_at is last UPDATED, not proof of original publication.
#>
[CmdletBinding()]
param(
    [ValidateRange(1,365)][int]$Days = 30,
    [string[]]$Boards = @("gitlab","vercel","openmined","infuse","crunchyroll")
)
$ErrorActionPreference = "Stop"
$cutoff = [DateTimeOffset]::UtcNow.AddDays(-$Days)
$rows = @()

function ParseUtcOrNull {
    param([object]$RawValue)
    if ([string]::IsNullOrWhiteSpace([string]$RawValue)) { return $null }
    try {
        $parsed = [DateTimeOffset]::Parse([string]$RawValue,[Globalization.CultureInfo]::InvariantCulture)
        return $parsed.ToUniversalTime()
    }
    catch { return $null }
}
Write-Host "Greenhouse public job-board feed test: one GET per board; no API keys"
Write-Host "UTC start: $([DateTimeOffset]::UtcNow.ToString('u')); age window: $Days days"
Write-Host "IMPORTANT: 30-day updated count is NOT a count of 30-day new job posts."

foreach($board in $Boards) {
    if($board -notmatch '^[a-zA-Z0-9_-]+$') {
        Write-Warning "Invalid board token skipped"
        continue
    }
    $url = "https://boards-api.greenhouse.io/v1/boards/$board/jobs"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
        # Omit content=true for a compact list response; no individual postings retrieved.
        $response = Invoke-WebRequest -Uri $url -Method Get -Headers @{ Accept="application/json" } -TimeoutSec 45 -UseBasicParsing -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        if ($null -eq $data -or $data.PSObject.Properties.Name -notcontains "jobs") {
            throw "JSON missing jobs field"
        }
        $posts = @($data.jobs | Where-Object { $null -ne $_ })
        # Greenhouse: null internal_job_id indicates a general prospect posting.
        $jobs = @($posts | Where-Object { $null -ne $_.internal_job_id })
        $ids = @($jobs | ForEach-Object { $_.id } | Where-Object { $null -ne $_ } | Sort-Object -Unique)
        $firstKnown = 0
        $firstRecent = 0
        $updatedKnown = 0
        $updatedRecent = 0
        $contractSigns = 0
        $updatedContract = 0
        $roleSigns = 0
        $updatedRole = 0

        foreach($job in $jobs) {
            # first_published may not be exposed on the board's list endpoint.
            $first = ParseUtcOrNull $job.first_published
            $update = ParseUtcOrNull $job.updated_at
            if ($null -ne $first) {
                $firstKnown++
                if($first -ge $cutoff) { $firstRecent++ }
            }
            if ($null -ne $update) {
                $updatedKnown++
                if($update -ge $cutoff) { $updatedRecent++ }
            }
            $role = ([string]$job.title -match '(?i)\b(project|program|product|portfolio|pmo|transformation|delivery)\b')
            if($role) {
                $roleSigns++
                if($null -ne $update -and $update -ge $cutoff) { $updatedRole++ }
            }
            # Heuristic, NOT confirmed employment type: "contract manager" may be full-time.
            $contract = ([string]$job.title -match '(?i)\b(contract|contractor|contracting|freelance|interim|temporary|1099)\b')
            foreach($field in @($job.metadata | Where-Object { $null -ne $_ })) {
                $fieldName = [string]$field.name
                $fieldValue = [string]($field.value -join ' ')
                if($fieldName -match '(?i)employment|job.type|position.type|worker.type|contract') {
                    if($fieldValue -match '(?i)contract|temporar|freelanc|1099|interim') {
                        $contract = $true
                    }
                }
            }
            if($contract) {
                $contractSigns++
                if($null -ne $update -and $update -ge $cutoff) { $updatedContract++ }
            }
        }
        $sw.Stop()
        $rows += [pscustomobject]@{
            Board=$board; Status="OK"; HTTP=[int]$response.StatusCode
            Postings=$posts.Count; Jobs=$jobs.Count; UniqueIDs=$ids.Count
            FirstKnown=$firstKnown; FirstRecent=$firstRecent
            UpdatedKnown=$updatedKnown; UpdatedRecent=$updatedRecent
            RoleSignals=$roleSigns; ContractSignals=$contractSigns
            UpdatedRole=$updatedRole; UpdatedContract=$updatedContract
            ProspectPosts=($posts.Count-$jobs.Count)
            Seconds=[math]::Round($sw.Elapsed.TotalSeconds,1)
        }
    }
    catch {
        $sw.Stop()
        $rows += [pscustomobject]@{
            Board=$board; Status="FAILED"; HTTP=""; Postings=$null; Jobs=$null
            UniqueIDs=$null; FirstKnown=$null; FirstRecent=$null
            UpdatedKnown=$null; UpdatedRecent=$null
            RoleSignals=$null; ContractSignals=$null; UpdatedRole=$null
            UpdatedContract=$null; ProspectPosts=$null
            Seconds=[math]::Round($sw.Elapsed.TotalSeconds,1)
        }
        Write-Warning ("{0}: request or parse failed ({1})" -f $board,$_.Exception.Message)
    }
}
Write-Host ""
Write-Host "ACCESS / VOLUME / TITLE-OR-METADATA SIGNALS:"
$rows | Format-Table Board,Status,HTTP,Postings,Jobs,UniqueIDs,RoleSignals,ContractSignals -AutoSize
Write-Host "DATES: FirstRecent measures first-published if present; UpdatedRecent is update activity only:"
$rows | Format-Table Board,FirstKnown,FirstRecent,UpdatedKnown,UpdatedRecent,UpdatedRole,UpdatedContract -AutoSize

$ok = @($rows | Where-Object { $_.Status -eq 'OK' })
Write-Host ("Successful boards: {0}/{1}" -f $ok.Count,$rows.Count)
Write-Host ("Non-prospect job postings: {0}" -f (($ok | Measure-Object Jobs -Sum).Sum))
Write-Host ("Role-title signals: {0}" -f (($ok | Measure-Object RoleSignals -Sum).Sum))
Write-Host ("Contract title/custom-field signals (not verified contracts): {0}" -f (($ok | Measure-Object ContractSignals -Sum).Sum))
Write-Host ("First-published known: {0}; first-published in last {1} days: {2}" -f (($ok | Measure-Object FirstKnown -Sum).Sum),$Days,(($ok | Measure-Object FirstRecent -Sum).Sum))
Write-Host ("Updated in last {0} days (NOT newly published count): {1}" -f $Days,(($ok | Measure-Object UpdatedRecent -Sum).Sum))
Write-Host "Only five named employer boards, not the Greenhouse-wide job inventory."
Write-Host "No saved job descriptions, no keys, no Adzuna calls."
