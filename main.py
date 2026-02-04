import requests
from bs4 import BeautifulSoup
import csv
import time

# ===================== CONFIG =====================

count=1

BASE_URL = "https://atmosphere.virtuagym.com/user/taherpk/exercise/ajax"
START_PAGE = 1
END_PAGE = 131
OUTPUT_CSV = "virtuagym_exercises.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://atmosphere.virtuagym.com/user/taherpk/exercise/training-plan-creator",
}

COOKIES = {
    "virtuagym_u": "7513151",
    "virtuagym_k": "d0ab6b93212556b4a223068f7b30acdcf5c2",
    "virtuagym_sid": "0c7092a2c5a92f23698d104ee828c9b536a1",
    "vg-user-access-token": "YOUR_ACCESS_TOKEN",
    "vg-user-refresh-token": "YOUR_REFRESH_TOKEN",
}

# ===================== HELPERS =====================

def extract_exercises(html: str):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for li in soup.select("li.exercise"):
        global count
        print(f"   → Processing exercise {count}")
        count += 1
        def val(selector):
            el = li.select_one(selector)
            return el["value"].strip() if el and el.has_attr("value") else ""

        # Collect set values (1–10)
        raw_sets = []
        for i in range(1, 11):
            v = val(f".set{i}")
            if v.isdigit() and int(v) > 0:
                raw_sets.append(v)

        total_sets = len(raw_sets)

        is_time_based = val(".time_based") == "1"
        exercise_type = "time_based" if is_time_based else "repetition_based"

        seconds_per_set = ",".join(raw_sets) if is_time_based else ""
        repetitions_per_set = ",".join(raw_sets) if not is_time_based else ""

        results.append({
            "id": val(".id") or li.get("id"),
            "name": val(".name"),

            # 🔹 category mapped from type[]
            "category": val(".type"),

            "primary_muscles": val(".primary_muscles"),
            "secondary_muscles": val(".secondary_muscles"),
            "difficulty": val(".difficulty"),
            "equipment": val(".equipment"),

            "exercise_type": exercise_type,
            "sets": total_sets,
            "seconds_per_set": seconds_per_set,
            "repetitions_per_set": repetitions_per_set,

            "rest": val(".rest"),
            "video": val(".video"),
            "thumbnail": val(".thumbnail"),

            "pro_only": val(".pro") == "1",
            "uses_weights": val(".uses_weights") == "1",
        })

    return results



# ===================== MAIN =====================

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.update(COOKIES)

all_exercises = []

for page in range(START_PAGE, END_PAGE + 1):
    print(f"📄 Fetching page {page}")

    params = {
        "exercise_type": "all",
        "equipment": "all",
        "bodypart": "all",
        "muscle_group": "all",
        "exercise_difficulty": "all",
        "is_custom": "all",
        "searchfield": "",
        "primal_joints": "all",
        "motion": "all",
        "page": page,
        "action": "search_exercises_plan_creator",
    }

    resp = session.get(BASE_URL, params=params, timeout=30)

    if resp.status_code != 200:
        print(f"❌ Failed page {page} ({resp.status_code})")
        continue

    page_exercises = extract_exercises(resp.text)
    print(f"   → {len(page_exercises)} exercises")

    if not page_exercises:
        print("⚠️ Empty page detected, stopping early")
        break

    all_exercises.extend(page_exercises)
    time.sleep(0.5)  # be polite

print(f"\n✅ Total exercises collected: {len(all_exercises)}")

# ===================== CSV EXPORT =====================

if all_exercises:
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_exercises[0].keys())
        writer.writeheader()
        writer.writerows(all_exercises)

    print(f"📁 CSV saved as {OUTPUT_CSV}")
else:
    print("⚠️ No data to write")
