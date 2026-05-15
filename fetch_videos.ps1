$key = "sk_V2_hgu_k4XCALxOKjP_MCxtNJUVvqk9KGY2WXzvNuZOoT8EHcGS"
$headers = @{ "x-api-key" = $key }
$ids = @("e6c554baa5024a789cb708c32b7e5a14","4778dce9cbc84e028816880522935e77","4cf145c54e5a44a28288a938a3dad736","d1d160325b644216b2ed7b70ec179f51")
$videos = @()
foreach ($id in $ids) {
    $r = Invoke-RestMethod "https://api.heygen.com/v1/video_status.get?video_id=$id" -Headers $headers
    $d = $r.data
    if ($d.status -eq "completed") {
        $ts = $d.created_at
        $dt = [DateTimeOffset]::FromUnixTimeSeconds($ts).DateTime.ToString("yyyy-MM-ddTHH:mm:ss")
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
            timestamp = $ts
        }
    }
}
$videos | ConvertTo-Json -Depth 5 | Set-Content "backend/broadcast_history.json" -Encoding UTF8
Write-Host "Done! Saved $($videos.Count) videos."
