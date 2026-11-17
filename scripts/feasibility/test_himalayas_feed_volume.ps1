<#
Sprint 1 Himalayas public remote-job API feasibility test.
Read-only. No API key, Adzuna calls, disk writes, personal job scoring, or application actions.
Search endpoint: country=US, employment_type=Contractor,Temporary, sort=recent.
The API's pubDate is LAST UPDATED, not original publication time.
The API's totalCount is provider-reported; only fetched pages are directly verified.
Docs: https://himalayas.app/docs/remote-jobs-api
Usage from repository root:
  powershell -NoProfile -File .\scripts\feasibility\test_himalayas_feed_volume.ps1
Optional pagination sampling:
  powershell -NoProfile -File .\scripts\feasibility\test_himalayas_feed_volume.ps1 -MaxPages 2
#>
[CmdletBinding()]
param(
    [ValidateRange(1,365)][int]$Days = 30,
    [ValidateRange(1,4)][int]$MaxPages = 1
)
$ErrorActionPreference = "Stop"
$cutoff = [DateTimeOffset]::UtcNow.AddDays(-$Days)
$allIds = New-Object 'System.Collections.Generic.HashSet[string]'
$rows = @()

# Baseline measures US-applicable contract-like roles without a keyword.
$searches = @(
    [pscustomobject]@{ Name="ALL_US_CONTRACT"; Query="" },
    [pscustomobject]@{ Name="PROJECT_MANAGER"; Query="project manager" },
    [pscustomobject]@{ Name="PROGRAM_MANAGER"; Query="program manager" },
    [pscustomobject]@{ Name="PRODUCT_MANAGER"; Query="product manager" },
    [pscustomobject]@{ Name="PMO"; Query="PMO" },
    [pscustomobject]@{ Name="PORTFOLIO_MANAGER"; Query="portfolio manager" },
    [pscustomobject]@{ Name="IMPLEMENTATION_MANAGER"; Query="implementation manager" },
    [pscustomobject]@{ Name="TRANSFORMATION"; Query="transformation" }
)

function Parse-UnixDate {
    param([object]$Timestamp)
    try {
        if ([string]::IsNullOrWhiteSpace([string]$Timestamp)) { return $null }
        $sec = [long]$Timestamp
        if ($sec -lt 946684800 -or $sec -gt 253402300799) { return $null }
        return [DateTimeOffset]::FromUnixTimeSeconds($sec).ToUniversalTime()
    }
    catch { return $null }
}
function Get-LocationClass {
    param([object]$Restrictions)
    if ($null -eq $Restrictions) { return "Unknown" }
    $vals = @($Restrictions | Where-Object { $null -ne $_ })
    if ($vals.Count -eq 0) { return "Worldwide" }
    foreach ($item in $vals) {
        if ($item -is [string]) {
            if ($item.Trim() -match '(?i)^(us|usa|united states|united-states)$') {
                return "USExplicit"
            }
        }
        else {
            $tokens = @([string]$item.alpha2,[string]$item.name,[string]$item.slug)
            foreach ($token in $tokens) {
                if ($token -match '(?i)^(us|usa|united states|united-states)$') {
                    return "USExplicit"
                }
            }
        }
    }
    return "OtherCountries"
}

Write-Host "Himalayas source-volume check. No credentials or Adzuna calls."
Write-Host "UTC start: $([DateTimeOffset]::UtcNow.ToString('u')); last-updated window: $Days days"
Write-Host "One API call per query by default. Use -MaxPages 2 for pagination spot-check."
Write-Host "WARNING: pubDate means last updated, NOT originally posted."

foreach ($search in $searches) {
    $r = [pscustomobject]@{
        Search=$search.Name; Status="OK"; HTTP=200
        ReportedMatches=$null; Pages=0; SampleRows=0
        UniqueIDs=0; RepeatedIDs=0; MissingIDs=0
        Contractor=0; Temporary=0; TypeMismatch=0
        USExplicit=0; Worldwide=0; OtherCountries=0; CountryUnknown=0
        RoleTitle=0; UpdatedKnown=0; UpdatedRecent=0
        ExpiredSample=0; SalaryDisclosed=0; TruncatedSample=$false
    }
    $localIds = New-Object 'System.Collections.Generic.HashSet[string]'
    try {
        for ($page=1; $page -le $MaxPages; $page++) {
            $parameters = @(
                "country=US",
                "employment_type=$([Uri]::EscapeDataString('Contractor,Temporary'))",
                "sort=recent",
                "page=$page"
            )
            if (-not [string]::IsNullOrWhiteSpace([string]$search.Query)) {
                $parameters += "q=$([Uri]::EscapeDataString([string]$search.Query))"
            }
            $url = "https://himalayas.app/jobs/api/search?" + ($parameters -join "&")
            $response = Invoke-WebRequest -Uri $url -Method Get -Headers @{Accept="application/json"} -TimeoutSec 45 -UseBasicParsing -ErrorAction Stop
            $data = $response.Content | ConvertFrom-Json
            if ($null -eq $data -or $data.PSObject.Properties.Name -notcontains "jobs") {
                throw "Search API response missing jobs array."
            }
            if ($null -eq $data.totalCount) {
                throw "Missing totalCount; provider-reported volume unavailable."
            }
            if ($page -eq 1) { $r.ReportedMatches = [int]$data.totalCount }
            elseif ([int]$data.totalCount -ne $r.ReportedMatches) {
                Write-Warning ("{0}: provider count changed between pages" -f $search.Name)
            }
            $r.HTTP = [int]$response.StatusCode
            $r.Pages++
            $jobs = @($data.jobs | Where-Object { $null -ne $_ })
            $r.SampleRows += $jobs.Count

            foreach ($job in $jobs) {
                $id = [string]$job.guid
                if ([string]::IsNullOrWhiteSpace($id)) { $r.MissingIDs++ }
                elseif (-not $localIds.Add($id)) { $r.RepeatedIDs++; continue }
                else {
                    $r.UniqueIDs++
                    $null = $allIds.Add($id)
                }

                if ([string]$job.employmentType -eq "Contractor") { $r.Contractor++ }
                elseif ([string]$job.employmentType -eq "Temporary") { $r.Temporary++ }
                else { $r.TypeMismatch++ }

                $loc = Get-LocationClass $job.locationRestrictions
                switch ($loc) {
                    "USExplicit" { $r.USExplicit++ }
                    "Worldwide" { $r.Worldwide++ }
                    "OtherCountries" { $r.OtherCountries++ }
                    default { $r.CountryUnknown++ }
                }
                if ([string]$job.title -match '(?i)\b(project|program|product|portfolio|pmo|implementation|transformation|delivery)\b') {
                    $r.RoleTitle++
                }
                $updated = Parse-UnixDate $job.pubDate
                if ($null -ne $updated) {
                    $r.UpdatedKnown++
                    if ($updated -ge $cutoff) { $r.UpdatedRecent++ }
                }
                $expiry = Parse-UnixDate $job.expiryDate
                if ($null -ne $expiry -and $expiry -lt [DateTimeOffset]::UtcNow) { $r.ExpiredSample++ }
                if ($null -ne $job.minSalary -or $null -ne $job.maxSalary) { $r.SalaryDisclosed++ }
            }

            if ($jobs.Count -eq 0 -or $r.SampleRows -ge $r.ReportedMatches) { break }
            if ($page -eq $MaxPages) { $r.TruncatedSample = $true }
        }

        if ($r.TypeMismatch -gt 0 -or $r.OtherCountries -gt 0) {
            Write-Warning ("{0}: sample has disallowed type or country restriction; cannot trust filtered count." -f $search.Name)
            $r.Status = "FILTER_MISMATCH"
        }
        if ($r.RepeatedIDs -gt 0) {
            Write-Warning ("{0}: repeated GUIDs among sampled pages" -f $search.Name)
            $r.Status = "PARTIAL"
        }
        if ($r.ReportedMatches -gt 0 -and $r.SampleRows -eq 0) {
            Write-Warning ("{0}: positive reported count but zero jobs returned" -f $search.Name)
            $r.Status = "PARTIAL"
        }
        Write-Host ("{0}: reported={1}, sample={2}, contractor={3}, temporary={4}, US={5}, worldwide={6}" -f $search.Name,$r.ReportedMatches,$r.SampleRows,$r.Contractor,$r.Temporary,$r.USExplicit,$r.Worldwide)
    }
    catch {
        $r.Status = "FAILED"
        $r.HTTP = ""
        if ($null -ne $_.Exception.Response -and $null -ne $_.Exception.Response.StatusCode) {
            $r.HTTP = [int]$_.Exception.Response.StatusCode
        }
        Write-Warning ("{0}: API fetch/parse failed: {1}" -f $search.Name,$_.Exception.Message)
    }
    $rows += $r
}

Write-Host ""
Write-Host "FILTERED QUERY COUNTS AND RETRIEVAL DEPTH:"
$rows | Format-Table Search,Status,HTTP,ReportedMatches,Pages,SampleRows,UniqueIDs,TruncatedSample -AutoSize

Write-Host "ACTUAL SAMPLE: EMPLOYMENT TYPE AND US/WORLDWIDE RESTRICTIONS:"
$rows | Format-Table Search,Contractor,Temporary,TypeMismatch,USExplicit,Worldwide,OtherCountries,CountryUnknown,RoleTitle -AutoSize

Write-Host "ACTUAL SAMPLE: LAST-UPDATED AGE AND METADATA:"
$rows | Format-Table Search,UpdatedKnown,UpdatedRecent,ExpiredSample,SalaryDisclosed,RepeatedIDs,MissingIDs -AutoSize

$good = @($rows | Where-Object { $_.Status -eq "OK" })
Write-Host ("Validated filtered queries: {0}/{1}" -f $good.Count,$rows.Count)
Write-Host ("Distinct GUIDs observed across ALL sampled query slices: {0}" -f $allIds.Count)
Write-Host "Do NOT sum ReportedMatches: keyword queries overlap and only samples were fetched."
Write-Host "UpdatedRecent is NOT a verified newly published count. No first-published field provided."
Write-Host "Country filter is not proof that a Georgia-based worker is eligible or timezone-compatible."
Write-Host "No salary filter: undisclosed compensation remains in scope."
Write-Host "This is REMOTE-only inventory; local hybrid/onsite needs separate sources."
Write-Host "No bulk crawl or retry loop. If HTTP 429 occurs, review before rerunning."
Write-Host "No job details were saved; zero Adzuna calls used."
