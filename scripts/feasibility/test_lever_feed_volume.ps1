<#
Sprint 1 Lever feasibility test. Read-only. No keys, no disk writes, no Adzuna calls.
Run: powershell -NoProfile -File .\scripts\feasibility\test_lever_feed_volume.ps1
Alternate: powershell -NoProfile -File .\scripts\feasibility\test_lever_feed_volume.ps1 -Days 7
createdAt is posting CREATION time, NOT confirmed original PUBLICATION time.
Selected boards are a contract-biased pilot, not a representative Lever sample.
#>
[CmdletBinding()]
param(
    [ValidateRange(1,365)][int]$Days = 30,
    [string[]]$Boards = @("lever","pointclickcare","idealistconsulting","compassx","protrials"),
    [ValidateRange(10,200)][int]$PageSize = 100,
    [ValidateRange(1,30)][int]$MaxPages = 12
)
$ErrorActionPreference = "Stop"
$cutoff = [DateTimeOffset]::UtcNow.AddDays(-$Days)
$rows = @()
$labels = @{}

function Bump {
    param([hashtable]$Map,[string]$Key)
    if ([string]::IsNullOrWhiteSpace($Key)) { $Key = "(missing)" }
    if (-not $Map.ContainsKey($Key)) { $Map[$Key] = 0 }
    $Map[$Key]++
}
function Show-Counts {
    param([hashtable]$Map)
    if($Map.Count -eq 0) { return "(none)" }
    return (($Map.Keys | Sort-Object | ForEach-Object { "{0}:{1}" -f $_,$Map[$_] }) -join "; ")
}

Write-Host "Lever public postings test: no API keys, no Adzuna calls."
Write-Host "UTC start: $([DateTimeOffset]::UtcNow.ToString('u')) ; creation window: $Days days"
Write-Host "CAUTION: createdAt is creation timestamp, NOT verified first publication."

foreach($board in $Boards) {
    if($board -notmatch '^[A-Za-z0-9._-]+$') {
        Write-Warning "Skipped invalid Lever board token"
        continue
    }

    $seen = New-Object 'System.Collections.Generic.HashSet[string]'
    $commitments = @{}
    $workplaces = @{}
    $r = [pscustomobject]@{
        Board=$board; Status="OK"; HTTP=200; Pages=0; Returned=0
        UniqueIDs=0; MissingIDs=0; DuplicateIDs=0; Truncated=$false
        CreatedKnown=0; CreatedRecent=0; Role=0
        CommitContract=0; TitleOnlyContract=0; AnyContract=0
        RecentRole=0; RecentCommitContract=0
        RecentRoleCommit=0; RecentRoleTitleOnly=0; RecentRoleAny=0
        RecentRoleAnyCountryUS=0; RecentRoleAnyCountryUnknown=0
        RecentRoleAnyRemote=0; RecentRoleAnyUSRemote=0
        CountryUSAll=0; RemoteAll=0; MissingCommitment=0
    }

    try {
        for($page=0; $page -lt $MaxPages; $page++) {
            $skip = $page * $PageSize
            $url = "https://api.lever.co/v0/postings/$board" + "?mode=json&limit=$PageSize&skip=$skip"
            $resp = Invoke-WebRequest -Uri $url -Method Get -Headers @{Accept="application/json"} -UseBasicParsing -TimeoutSec 60 -ErrorAction Stop
            if(-not $resp.Content.TrimStart().StartsWith("[")) { throw "Expected JSON array from Lever" }
            $json = $resp.Content | ConvertFrom-Json
            $jobs = @($json | Where-Object { $null -ne $_ })
            if($jobs.Count -gt $PageSize) { throw "Lever returned more than PageSize; cannot trust pagination" }
            $r.Pages++
            $r.Returned += $jobs.Count
            $r.HTTP = [int]$resp.StatusCode

            foreach($job in $jobs) {
                $id = [string]$job.id
                if([string]::IsNullOrWhiteSpace($id)) { $r.MissingIDs++ }
                elseif(-not $seen.Add($id)) { $r.DuplicateIDs++; continue }
                else { $r.UniqueIDs++ }

                $title = [string]$job.text
                $commit = [string]$job.categories.commitment
                $workplace = [string]$job.workplaceType
                $country = [string]$job.country
                Bump $commitments $commit
                Bump $workplaces $workplace
                if([string]::IsNullOrWhiteSpace($commit)) { $r.MissingCommitment++ }
                if($country -ieq "US") { $r.CountryUSAll++ }
                if($workplace -ieq "remote") { $r.RemoteAll++ }

                $role = ($title -match '(?i)\b(project|program|product|portfolio|pmo|transformation|delivery)\b')
                $explicit = ($commit -match '(?i)\b(contract|contractor|freelance|temporary|temp|interim|1099)\b')
                $titleHint = ($title -match '(?i)\b(contract|contractor|contracting|freelance|temporary|temp|interim|1099)\b')
                $titleOnly = ($titleHint -and -not $explicit)
                $contractAny = ($explicit -or $titleHint)

                $created = $null
                if($null -ne $job.createdAt) {
                    try {
                        $ms = [long]$job.createdAt
                        if($ms -gt 100000000000 -and $ms -lt 253402300800000) {
                            $created = [DateTimeOffset]::FromUnixTimeMilliseconds($ms)
                        }
                    } catch { $created = $null }
                }
                $recent = ($null -ne $created -and $created.ToUniversalTime() -ge $cutoff)
                if($null -ne $created) { $r.CreatedKnown++ }
                if($recent) { $r.CreatedRecent++ }
                if($role) { $r.Role++ }
                if($explicit) { $r.CommitContract++ }
                if($titleOnly) { $r.TitleOnlyContract++ }
                if($contractAny) { $r.AnyContract++ }
                if($recent -and $role) { $r.RecentRole++ }
                if($recent -and $explicit) { $r.RecentCommitContract++ }
                if($recent -and $role -and $explicit) { $r.RecentRoleCommit++ }
                if($recent -and $role -and $titleOnly) { $r.RecentRoleTitleOnly++ }
                if($recent -and $role -and $contractAny) {
                    $r.RecentRoleAny++
                    if($country -ieq "US") {
                        $r.RecentRoleAnyCountryUS++
                        if($workplace -ieq "remote") { $r.RecentRoleAnyUSRemote++ }
                    }
                    elseif([string]::IsNullOrWhiteSpace($country)) {
                        $r.RecentRoleAnyCountryUnknown++
                    }
                    if($workplace -ieq "remote") { $r.RecentRoleAnyRemote++ }
                }
            }
            if($jobs.Count -lt $PageSize) { break }
            if($page -eq ($MaxPages-1)) { $r.Truncated = $true }
        }
        Write-Host ("{0}: {1} unique IDs in {2} page(s), {3} recent-created" -f $board,$r.UniqueIDs,$r.Pages,$r.CreatedRecent)
        if($r.DuplicateIDs -gt 0) { Write-Warning ("{0}: duplicate IDs found across pages" -f $board) }
        if($r.Truncated) { Write-Warning ("{0}: page cap reached; not complete" -f $board) }
        if($r.Truncated -or $r.DuplicateIDs -gt 0) { $r.Status = "PARTIAL" }
    }
    catch {
        $r.Status = "FAILED"
        $r.HTTP = ""
        if($null -ne $_.Exception.Response -and $null -ne $_.Exception.Response.StatusCode) {
            $r.HTTP = [int]$_.Exception.Response.StatusCode
        }
        Write-Warning ("{0}: incomplete result ({1})" -f $board,$_.Exception.Message)
        # Exclude incomplete boards from aggregate totals; partial metrics remain displayed.
    }
    $rows += $r
    $labels[$board] = [pscustomobject]@{
        Commit=Show-Counts $commitments
        Workplace=Show-Counts $workplaces
    }
}

Write-Host ""
Write-Host "ACCESS / VOLUME / AGE (createdAt, not publication date):"
$rows | Format-Table Board,Status,HTTP,Pages,Returned,UniqueIDs,MissingIDs,DuplicateIDs,CreatedKnown,CreatedRecent,Truncated -AutoSize
Write-Host "CONTRACT SOURCE / ROLE OVERLAP:"
$rows | Format-Table Board,Role,CommitContract,TitleOnlyContract,AnyContract,RecentRole,RecentRoleCommit,RecentRoleTitleOnly,RecentRoleAny -AutoSize
Write-Host "LOCATION IN RECENT-CREATED + ROLE + CONTRACT-SIGNAL OVERLAP:"
$rows | Format-Table Board,RecentRoleAny,RecentRoleAnyCountryUS,RecentRoleAnyCountryUnknown,RecentRoleAnyRemote,RecentRoleAnyUSRemote -AutoSize

Write-Host ""
Write-Host "COMMITMENT LABELS (not job-title hints):"
foreach($row in $rows) { Write-Host ("{0}: {1}" -f $row.Board,$labels[$row.Board].Commit) }
Write-Host "WORKPLACE LABELS:"
foreach($row in $rows) { Write-Host ("{0}: {1}" -f $row.Board,$labels[$row.Board].Workplace) }

$ok = @($rows | Where-Object { $_.Status -eq "OK" })
Write-Host ""
Write-Host ("Complete and successful boards: {0}/{1}; PARTIAL boards not included in totals" -f $ok.Count,$rows.Count)
Write-Host ("Unique IDs within boards: {0}" -f (($ok | Measure-Object UniqueIDs -Sum).Sum))
Write-Host ("CreatedAt known: {0}; created in last {1} days: {2}" -f (($ok | Measure-Object CreatedKnown -Sum).Sum),$Days,(($ok | Measure-Object CreatedRecent -Sum).Sum))
Write-Host ("Broad target-role title signals: {0}" -f (($ok | Measure-Object Role -Sum).Sum))
Write-Host ("Explicit contractor commitment: {0}; title-only weak hints: {1}" -f (($ok | Measure-Object CommitContract -Sum).Sum),(($ok | Measure-Object TitleOnlyContract -Sum).Sum))
Write-Host ("Recent-created + role + explicit contract commitment: {0}" -f (($ok | Measure-Object RecentRoleCommit -Sum).Sum))
Write-Host ("Recent-created + role + any contract signal: {0}" -f (($ok | Measure-Object RecentRoleAny -Sum).Sum))
Write-Host (".. country=US: {0}; country unknown: {1}; country=US and remote: {2}" -f (($ok | Measure-Object RecentRoleAnyCountryUS -Sum).Sum),(($ok | Measure-Object RecentRoleAnyCountryUnknown -Sum).Sum),(($ok | Measure-Object RecentRoleAnyUSRemote -Sum).Sum))
Write-Host "CAVEATS: createdAt is NOT first publication; contract title may mean full-time contract management."
Write-Host "US/remote metadata is NOT verified hiring eligibility. Counts are not cross-provider deduplicated."
Write-Host "No credentials, no saved job data, no job suitability analysis, no Adzuna calls."
