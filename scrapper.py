import requests

url = "https://atmosphere.virtuagym.com/user/taherpk/exercise/ajax"

params = {
    "exercise_type": "all",
    "equipment": "all",
    "bodypart": "all",
    "muscle_group": "all",
    "exercise_difficulty": "all",
    "is_custom": "all",
    "searchfield": "",
    "primal_joints": "all",
    "page": 131,
    "motion": "all",
    "action": "search_exercises_plan_creator",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://atmosphere.virtuagym.com/user/taherpk/exercise/training-plan-creator",
}

cookies = {
    "virtuagym_u": "7513151",
    "virtuagym_k": "d0ab6b93212556b4a223068f7b30acdcf5c2",
    "virtuagym_sid": "0c7092a2c5a92f23698d104ee828c9b536a1",
    "vg-user-access-token": "YOUR_ACCESS_TOKEN",
    "vg-user-refresh-token": "YOUR_REFRESH_TOKEN",
}

response = requests.get(
    url,
    params=params,
    headers=headers,
    cookies=cookies,
    timeout=30
)

print("Status:", response.status_code)

# Save response to HTML file
if response.status_code == 200:
    with open("response.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("HTML saved as response.html")
else:
    print("Request failed")
