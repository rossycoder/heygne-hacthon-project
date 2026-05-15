$key = "sk_V2_hgu_k4XCALxOKjP_MCxtNJUVvqk9KGY2WXzvNuZOoT8EHcGS"
$headers = @{ "x-api-key" = $key }

# Get all completed videos
$list = Invoke-RestMethod "https://api.heygen.com/v1/video.list?limit=20" -Headers $headers
$completed = $list.data.videos | Where-Object { $_.status -eq "completed" }

Write-Host "Found $($completed.Count) completed videos"

$videos = @()
foreach ($v in $completed) {
    $id = $v.video_id
    Write-Host "Fetching: $id"
    try {
        $r = Invoke-RestMethod "https://api.heygen.com/v1/video_status.get?video_id=$id" -Headers $headers
        $d = $r.data
        $dt = [DateTimeOffset]::FromUnixTimeSeconds($v.created_at).DateTime.ToString("yyyy-MM-ddTHH:mm:ss")
        $videos += @{
            id = "heygen_$id"
            name = "NewsGen Broadcast"
            city = "Unknown"
            language = "English"
            topics = @()
            avatar_id = $null
            script = ""
            video_url = $d.video_url
            thumbnail_url = $d.thumbnail_url
            news_stories = @()
            news_count = 0
            created_at = $dt
            timestamp = $v.created_at
        }
    } catch {
        Write-Host "Failed for $id : $_"
    }
}

$videos | ConvertTo-Json -Depth 5 | Set-Content "backend/broadcast_history.json" -Encoding UTF8
Write-Host "Saved $($videos.Count) videos to broadcast_history.json"
