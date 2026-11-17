<#
.SYNOPSIS
  Sprint 1 Greenhouse read-only test: recent x role x contract-signal overlap.
.DESCRIPTION
  Runs one unauthenticated public GET per named employer board. Reports aggregate
  counts and top location labels only. No individual job scoring or API keys.
  Uses first_published (not updated_at) for the age window.
  Contract signals are not proof of contract employment.
.EXAMPLE
  powershell -NoProfile -File .\scripts\feasibility\test_greenhouse_contract_overlap.ps1
.EXAMPLE
  powershell -NoProfile -File .\scripts\feasibility\test_greenhouse_contract_overlap.ps1 -Days 7
#>
[CmdletBinding()]
param(
    [ValidateRange(1,365)][int]$Days = 30,
    [string[]]$Boards = @("gitlab","vercel","openmined","infuse","crunchyroll")
)

$ErrorActionPreference = "Stop"
$cutoff = [DateTimeOffset]::UtcNow.AddDays(-$Days)
$rows = @()
$infuseMetadata = @{}
$overlapLocations = @{}

function Parse-UtcOrNull {
    param([object]$Value)
    if ([string]::IsNullOrWhiteSpace([string]$Value)) { return $null }
    try {
        return ([DateTimeOffset]::Parse(
            [string]$Value,
            [Globalization.CultureInfo]::InvariantCulture
        )).ToUniversalTime()
    }
    catch { return $null }
}
function Add-Frequency {
    param([hashtable]$Table,[string]$Key)
    if ([string]::IsNullOrWhiteSpace($Key)) { $Key = "(missing)" }
    if (-not $Table.ContainsKey($Key)) { $Table[$Key] = 0 }
    $Table[$Key]++
}
function Show-TopCounts {
    param([hashtable]$Table,[int]$Limit = 15)
    if ($Table.Count -eq 0) {
        Write-Host "  (none)"
        return
    }
    $Table.GetEnumerator() |
        Sort-Object -Property Value -Descending |
        Select-Object -First $Limit |
        ForEach-Object { Write-Host ("  {0,4}  {1}" -f $_.Value,$_.Key) }
}

Write-Host "Greenhouse targeted feed-only overlap test: 1 GET per board, no keys."
Write-Host "UTC start: $([DateTimeOffset]::UtcNow.ToString('u')); age window: $Days days"
Write-Host "Age uses first_published, NEVER updated_at. Contract and role are heuristic signals."

foreach ($board in $Boards) {
    if ($board -notmatch '^[a-zA-Z0-9_-]+$') {
        Write-Warning "Invalid board token skipped"
        continue
    }

    $url = "https://boards-api.greenhouse.io/v1/boards/$board/jobs"
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -Headers @{Accept="application/json"} -TimeoutSec 45 -UseBasicParsing -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        if ($null -eq $data -or $data.PSObject.Properties.Name -notcontains "jobs") {
            throw "Missing jobs array in JSON"
        }
        $posts = @($data.jobs | Where-Object { $null -ne $_ })
        $jobs = @($posts | Where-Object { $null -ne $_.internal_job_id })

        $row = [pscustomobject]@{
            Board=$board; Status="OK"; HTTP=[int]$response.StatusCode
            Jobs=$jobs.Count; FirstKnown=0; Recent=0; Role=0
            ContractTitle=0; ContractMeta=0; ContractAny=0
            RecentRole=0; RecentContract=0; RoleContract=0
            RecentRoleContract=0
            OverlapTitleOnly=0; OverlapMetaOnly=0; OverlapBoth=0
            OverlapRemoteLabel=0; OverlapUSLabel=0; OverlapAtlantaLabel=0
            MissingLocations=0; ProspectPosts=($posts.Count - $jobs.Count)
        }

        foreach ($job in $jobs) {
            $first = Parse-UtcOrNull $job.first_published
            $recent = ($null -ne $first -and $first -ge $cutoff)
            if ($null -ne $first) { $row.FirstKnown++ }
            if ($recent) { $row.Recent++ }

            # Broad role-family title indicator; not a relevance determination.
            $role = ([string]$job.title -match '(?i)\b(project|program|product|portfolio|pmo|transformation|delivery)\b')
            if ($role) { $row.Role++ }

            # Keep title rule identical to the preceding Greenhouse count test.
            $titleContract = ([string]$job.title -match '(?i)\b(contract|contractor|contracting|freelance|interim|temporary|1099)\b')
            $metaContract = $false

            foreach ($field in @($job.metadata | Where-Object { $null -ne $_ })) {
                $fieldName = [string]$field.name
                $fieldValue = [string]($field.value -join " ")
                $typeField = ($fieldName -match '(?i)employment|job.type|position.type|worker.type|contract')
                if ($typeField) {
                    if ($board -eq "infuse") {
                        # Public, aggregate metadata only; cap length for readable console output.
                        $nameShort = $fieldName.Trim()
                        $valueShort = $fieldValue.Trim()
                        if ($nameShort.Length -gt 60) { $nameShort = $nameShort.Substring(0,60) }
                        if ($valueShort.Length -gt 90) { $valueShort = $valueShort.Substring(0,90) }
                        Add-Frequency $infuseMetadata ("{0} = {1}" -f $nameShort,$valueShort)
                    }
                    if ($fieldValue -match '(?i)contract|temporar|freelanc|1099|interim') {
                        $metaContract = $true
                    }
                }
            }

            $anyContract = ($titleContract -or $metaContract)
            if ($titleContract) { $row.ContractTitle++ }
            if ($metaContract) { $row.ContractMeta++ }
            if ($anyContract) { $row.ContractAny++ }
            if ($recent -and $role) { $row.RecentRole++ }
            if ($recent -and $anyContract) { $row.RecentContract++ }
            if ($role -and $anyContract) { $row.RoleContract++ }

            if ($recent -and $role -and $anyContract) {
                $row.RecentRoleContract++

                if ($titleContract -and $metaContract) {
                    $row.OverlapBoth++
                }
                elseif ($titleContract) {
                    $row.OverlapTitleOnly++
                }
                else {
                    $row.OverlapMetaOnly++
                }

                # Raw location labels, not verified geography or US hiring eligibility.
                $location = [string]$job.location.name
                $location = $location.Trim()
                if ([string]::IsNullOrWhiteSpace($location)) {
                    $location = "(missing)"
                    $row.MissingLocations++
                }
                if ($location -match '(?i)\bremote\b') { $row.OverlapRemoteLabel++ }
                if ($location -match '(?i)\b(USA|US|United States)\b') { $row.OverlapUSLabel++ }
                if ($location -match '(?i)\b(Atlanta|Georgia)\b') { $row.OverlapAtlantaLabel++ }

                if ($location.Length -gt 110) { $location = $location.Substring(0,110) }
                Add-Frequency $overlapLocations ("{0}: {1}" -f $board,$location)
            }
        }

        $rows += $row
    }
    catch {
        $status = ""
        if ($null -ne $_.Exception.Response -and $null -ne $_.Exception.Response.StatusCode) {
            $status = [string]([int]$_.Exception.Response.StatusCode)
        }
        Write-Warning ("{0}: fetch/parse failed ({1})" -f $board,$_.Exception.Message)
        $rows += [pscustomobject]@{
            Board=$board; Status="FAILED"; HTTP=$status
            Jobs=$null; FirstKnown=$null; Recent=$null; Role=$null
            ContractTitle=$null; ContractMeta=$null; ContractAny=$null
            RecentRole=$null; RecentContract=$null; RoleContract=$null
            RecentRoleContract=$null; OverlapTitleOnly=$null; OverlapMetaOnly=$null
            OverlapBoth=$null; OverlapRemoteLabel=$null; OverlapUSLabel=$null
            OverlapAtlantaLabel=$null; MissingLocations=$null; ProspectPosts=$null
        }
    }
}

Write-Host ""
Write-Host "OVERLAP BY BOARD (RRC = first-published recent AND target-role title AND contract signal):"
$rows | Format-Table Board,Status,Jobs,Recent,Role,ContractAny,RecentRole,RecentContract,RoleContract,RecentRoleContract -AutoSize

Write-Host "CONTRACT EVIDENCE FOR THE RRC OVERLAP (columns are mutually exclusive):"
$rows | Format-Table Board,ContractTitle,ContractMeta,OverlapTitleOnly,OverlapMetaOnly,OverlapBoth -AutoSize

Write-Host "GEOGRAPHY LITERAL SIGNALS WITHIN RRC OVERLAP (not geographic eligibility):"
$rows | Format-Table Board,RecentRoleContract,OverlapRemoteLabel,OverlapUSLabel,OverlapAtlantaLabel,MissingLocations -AutoSize

$ok = @($rows | Where-Object { $_.Status -eq "OK" })
Write-Host ""
Write-Host ("Success: {0}/{1} boards; non-prospect jobs: {2}; first-publication dates known: {3}" -f $ok.Count,$rows.Count,(($ok | Measure-Object Jobs -Sum).Sum),(($ok | Measure-Object FirstKnown -Sum).Sum))
Write-Host ("First published within {0} days: {1}" -f $Days,(($ok | Measure-Object Recent -Sum).Sum))
Write-Host ("Broad role-title signals: {0}; any contract signals: {1}" -f (($ok | Measure-Object Role -Sum).Sum),(($ok | Measure-Object ContractAny -Sum).Sum))
Write-Host ("RRC (recent + role + contract signals): {0}" -f (($ok | Measure-Object RecentRoleContract -Sum).Sum))
Write-Host ("RRC breakdown title-only: {0}, metadata-only: {1}, both: {2}" -f (($ok | Measure-Object OverlapTitleOnly -Sum).Sum),(($ok | Measure-Object OverlapMetaOnly -Sum).Sum),(($ok | Measure-Object OverlapBoth -Sum).Sum))

Write-Host ""
Write-Host "INFUSE EMPLOYMENT-TYPE-LIKE METADATA FIELD/VALUE PAIRS (top 15, aggregated):"
Show-TopCounts $infuseMetadata 15

Write-Host ""
Write-Host "MOST FREQUENT BOARD + LOCATION LABELS AMONG RRC OVERLAP (top 20):"
Show-TopCounts $overlapLocations 20

Write-Host ""
Write-Host "CAVEATS: contract metadata is employer-defined; role title is a broad keyword heuristic."
Write-Host "Remote/US/Atlanta are literal location text signals, not verified work eligibility."
Write-Host "Only the five selected boards were checked. No files written, no Adzuna calls."
