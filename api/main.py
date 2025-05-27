from flask import Flask, jsonify
import lxml
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from flask import render_template

app = Flask(__name__)

@app.route('/players/<player_name>', methods=['GET'])
def get_player(player_name):
    query = f"{player_name} cricbuzz"
    profile_link = None
    try:
        results = search(query, num_results=5)
        for link in results:
            if "cricbuzz.com/profiles/" in link:
                profile_link = link
                break
        if not profile_link:
            return {"error": "No player profile found"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

    c = requests.get(profile_link).text
    cric = BeautifulSoup(c, "lxml")
    profile = cric.find("div", id="playerProfile")
    pc = profile.find("div", class_="cb-col cb-col-100 cb-bg-white")
    name = pc.find("h1", class_="cb-font-40").text
    country = pc.find("h3", class_="cb-font-18 text-gray").text
    image_url = next((img['src'] for img in pc.findAll('img')), None)
    personal = cric.find_all("div", class_="cb-col cb-col-60 cb-lst-itm-sm")
    role = personal[2].text.strip()
    icc = cric.find_all("div", class_="cb-col cb-col-25 cb-plyr-rank text-right")
    tb, ob, twb = icc[0].text.strip(), icc[1].text.strip(), icc[2].text.strip()
    tbw, obw, twbw = icc[3].text.strip(), icc[4].text.strip(), icc[5].text.strip()

    summary = cric.find_all("div", class_="cb-plyr-tbl")
    batting_stats, bowling_stats = {}, {}

    for row in summary[0].find("tbody").find_all("tr"):
        cols = row.find_all("td")
        fmt = cols[0].text.strip().lower()
        batting_stats[fmt] = {
            "matches": cols[1].text.strip(),
            "runs": cols[3].text.strip(),
            "highest_score": cols[5].text.strip(),
            "average": cols[6].text.strip(),
            "strike_rate": cols[7].text.strip(),
            "hundreds": cols[12].text.strip(),
            "fifties": cols[11].text.strip(),
        }

    for row in summary[1].find("tbody").find_all("tr"):
        cols = row.find_all("td")
        fmt = cols[0].text.strip().lower()
        bowling_stats[fmt] = {
            "balls": cols[3].text.strip(),
            "runs": cols[4].text.strip(),
            "wickets": cols[5].text.strip(),
            "best_bowling_innings": cols[9].text.strip(),
            "economy": cols[7].text.strip(),
            "five_wickets": cols[11].text.strip(),
        }

    return jsonify({
        "name": name, "country": country, "image": image_url, "role": role,
        "rankings": {"batting": {"test": tb, "odi": ob, "t20": twb},
                     "bowling": {"test": tbw, "odi": obw, "t20": twbw}},
        "batting_stats": batting_stats, "bowling_stats": bowling_stats
    })

@app.route('/schedule')
def schedule():
    link = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/international"
    page = BeautifulSoup(requests.get(link).text, "lxml")
    matches = []
    for container in page.find_all("div", class_="cb-col-100 cb-col"):
        date = container.find("div", class_="cb-lv-grn-strip text-bold")
        match_info = container.find("div", class_="cb-col-100 cb-col")
        if date and match_info:
            matches.append(f"{date.text.strip()} - {match_info.text.strip()}")
    return jsonify(matches)

@app.route('/live')
def live_matches():
    page = BeautifulSoup(requests.get("https://www.cricbuzz.com/cricket-match/live-scores").text, "lxml")
    page = page.find("div", class_="cb-col cb-col-100 cb-bg-white")
    matches = page.find_all("div", class_="cb-scr-wll-chvrn cb-lv-scrs-col")

    live_data = []
    for match in matches:
        title = match.find("h3")
        score = match.find("div", class_="cb-lv-scrs-col text-black")
        details = match.find("div", class_="cb-text-invite")

        live_data.append({
            "title": title.text.strip() if title else "N/A",
            "livescore": score.text.strip() if score else "N/A",
            "details": details.text.strip() if details else "N/A"
        })

    return jsonify(live_data)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Cricket API!"})

if __name__ == "__main__":
    app.run(debug=True)
