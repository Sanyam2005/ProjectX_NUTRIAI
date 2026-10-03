$ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
$targetDir = "C:\Users\t-agrawalsa\NutriAI\test_images"
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force }

function Download-FoodImage($name, $urls) {
  $dst = Join-Path $targetDir $name
  $idx = 0
  foreach ($u in $urls) {
    $idx++
    try {
      $headers = @{ "User-Agent" = $ua; "Accept" = "image/jpeg,image/*" }
      Invoke-WebRequest -Uri $u -OutFile $dst -UseBasicParsing -Headers $headers -TimeoutSec 30 -ErrorAction Stop
      if (Test-Path $dst) {
          $size = (Get-Item $dst).Length
          if ($size -gt 5000) { 
              return "OK (Source $idx)"
          }
          Remove-Item $dst -ErrorAction SilentlyContinue
      }
    } catch { }
  }
  return "FAILED"
}

$targets = @(
  @{ n = "biryani.jpg"; urls = @("https://images.pexels.com/photos/15054033/pexels-photo-15054033/free-photo-of-traditional-indian-pulao-rice-and-curry.jpeg?auto=compress&cs=tinysrgb&w=800", "https://foodish-api.com/images/biryani/biryani1.jpg") },
  @{ n = "masala_dosa.jpg"; urls = @("https://images.pexels.com/photos/12737919/pexels-photo-12737919.jpeg?auto=compress&cs=tinysrgb&w=800", "https://foodish-api.com/images/dosa/dosa1.jpg") },
  @{ n = "idli_sambar.jpg"; urls = @("https://images.pexels.com/photos/9609835/pexels-photo-9609835.jpeg?auto=compress&cs=tinysrgb&w=800", "https://foodish-api.com/images/idly/idly1.jpg") },
  @{ n = "pizza.jpg"; urls = @("https://images.pexels.com/photos/315755/pexels-photo-315755.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/825661/pexels-photo-825661.jpeg?auto=compress&cs=tinysrgb&w=800") },
  @{ n = "cheeseburger.jpg"; urls = @("https://images.pexels.com/photos/1639557/pexels-photo-1639557.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/1633578/pexels-photo-1633578.jpeg?auto=compress&cs=tinysrgb&w=800") },
  @{ n = "caesar_salad.jpg"; urls = @("https://images.pexels.com/photos/1213710/pexels-photo-1213710.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/2097090/pexels-photo-2097090.jpeg?auto=compress&cs=tinysrgb&w=800") },
  @{ n = "sushi.jpg"; urls = @("https://images.pexels.com/photos/2098085/pexels-photo-2098085.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/271715/pexels-photo-271715.jpeg?auto=compress&cs=tinysrgb&w=800") },
  @{ n = "pad_thai.jpg"; urls = @("https://images.pexels.com/photos/5848472/pexels-photo-5848472.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/4407906/pexels-photo-4407906.jpeg?auto=compress&cs=tinysrgb&w=800") },
  @{ n = "banana.jpg"; urls = @("https://images.pexels.com/photos/1093038/pexels-photo-1093038.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/61127/pexels-photo-61127.jpeg?auto=compress&cs=tinysrgb&w=800") },
  @{ n = "avocado_toast.jpg"; urls = @("https://images.pexels.com/photos/1351238/pexels-photo-1351238.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/704971/pexels-photo-704971.jpeg?auto=compress&cs=tinysrgb&w=800") }
)

foreach ($t in $targets) {
  $res = Download-FoodImage $t.n $t.urls
  Write-Host "$($t.n): $res"
}

Write-Host "---"
Get-ChildItem $targetDir | Select-Object Name, @{N='SizeKB';E={[math]::round($_.Length/1KB,1)}} | ft
