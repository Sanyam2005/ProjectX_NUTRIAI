$email = "weight-bmi-$(Get-Random -Maximum 99999)@example.com"
$body = @{ mode = "signup"; email = $email; password = "Sup3rSecret!"; name = "Test" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -ContentType "application/json" -Body $body
$tok = $response.access_token

$g = @{ height_cm = 180; target_weight_kg = 70; weight_kg = $null; age = 28; gender = "male"; activity_level = "moderate"; target_calories = 2200; target_protein_g = 100; target_carbs_g = 260; target_fat_g = 70; target_fiber_g = 30; target_water_ml = 2500 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/goals" -Method PUT -ContentType "application/json" -Headers @{Authorization="Bearer $tok"} -Body $g | Out-Null

foreach ($kg in 78, 76.5, 75.2) {
  Invoke-RestMethod -Uri "http://localhost:8000/api/weight" -Method POST -ContentType "application/json" -Headers @{Authorization="Bearer $tok"} -Body (@{weight_kg=$kg} | ConvertTo-Json) | Out-Null
}

$r = Invoke-RestMethod -Uri "http://localhost:8000/api/weight/report" -Headers @{Authorization="Bearer $tok"}
$r | ConvertTo-Json -Depth 4
