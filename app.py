
import os
import re
import csv
import io
import hmac
import requests

from flask import Flask, request, Response, render_template_string

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
EXPORT_KEY = os.environ.get("EXPORT_KEY")
GRAPH_URL = "https://graph.instagram.com/v27.0"


PAGE = """
<!DOCTYPE html>
<html lang="bs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Giveaway Winner</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #f3f4f6;
    padding: 30px;
}
.container {
    max-width: 550px;
    margin: 50px auto;
    background: white;
    padding: 30px;
    border-radius: 12px;
}
input, button {
    width: 100%;
    padding: 13px;
    margin: 10px 0;
    box-sizing: border-box;
}
button {
    background: #222;
    color: white;
    border: 0;
    border-radius: 6px;
    cursor: pointer;
}
</style>
</head>
<body>
<div class="container">
<h2>Giveaway Winner</h2>
<p>Preuzimanje komentara sa Instagram objave</p>
<form action="/export" method="POST">
<label>Instagram link objave</label>
<input name="post_url" type="url" required
placeholder="https://www.instagram.com/p/..." />
<label>Export key</label>
<input name="key" type="password" required
placeholder="Tvoj EXPORT_KEY" />
<button type="submit">Preuzmi komentare (CSV)</button>
</form>
</div>
</body>
</html>
"""


def api_get(endpoint, params=None):
    params = params or {}
    params["access_token"] = ACCESS_TOKEN

    response = requests.get(
        f"{GRAPH_URL}/{endpoint}",
        params=params,
        timeout=30
    )

    data = response.json()

    if response.status_code != 200 or "error" in data:
        error = data.get("error", {})
        raise Exception(
            error.get("message", "Instagram API greška")
        )

    return data


def get_all_pages(endpoint, params=None):
    params = params or {"limit": 100}
    results = []

    data = api_get(endpoint, params)

    while True:
        results.extend(data.get("data", []))

        next_url = data.get("paging", {}).get("next")

        if not next_url:
            break

        response = requests.get(next_url, timeout=30)
        data = response.json()

        if response.status_code != 200 or "error" in data:
            raise Exception("Greška pri učitavanju naredne stranice.")

    return results


def extract_shortcode(url):
    match = re.search(
        r"instagram\.com/(?:p|reel|tv)/([^/?]+)",
        url
    )

    if not match:
        raise Exception("Instagram link nije ispravan.")

    return match.group(1)


@app.route("/")
def home():
    return render_template_string(PAGE)


@app.route("/health")
def health():
    return {"status": "ok", "application": "Giveaway Winner"}


@app.route("/export", methods=["POST"])
def export_comments():

    if not ACCESS_TOKEN or not EXPORT_KEY:
        return "Nedostaju environment varijable na Renderu.", 500

    supplied_key = request.form.get("key", "")

    if not hmac.compare_digest(supplied_key, EXPORT_KEY):
        return "Neispravan Export Key.", 403

    try:
        shortcode = extract_shortcode(
            request.form.get("post_url", "")
        )

        # Provjera Instagram profila
        profile = api_get("me", {
            "fields": "user_id,username"
        })

        # Pronalazak objave na povezanom profilu
        media = get_all_pages("me/media", {
            "fields": "id,permalink,comments_count,timestamp",
            "limit": 100
        })

        target = None

        for item in media:
            permalink = item.get("permalink", "")
            try:
                if extract_shortcode(permalink) == shortcode:
                    target = item
                    break
            except Exception:
                continue

        if not target:
            return (
                "Objava nije pronađena na Instagram profilu "
                "povezanom s ovim tokenom.",
                404
            )

        # Preuzimanje svih dostupnih komentara
        comments = get_all_pages(
            f"{target['id']}/comments",
            {
                "fields": "id,text,timestamp,username",
                "limit": 100
            }
        )

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "username",
            "comment",
            "timestamp",
            "comment_id"
        ])

        missing_usernames = 0

        for comment in comments:
            username = comment.get("username", "")

            if not username:
                missing_usernames += 1

            writer.writerow([
                username,
                comment.get("text", ""),
                comment.get("timestamp", ""),
                comment.get("id", "")
            ])

        if missing_usernames:
            return (
                f"API je pronašao {len(comments)} komentara, "
                f"ali za {missing_usernames} komentara nije "
                "vratio korisničko ime. CSV nije preuzet jer "
                "nije spreman za izvlačenje dobitnika. "
                "Potrebno je provjeriti API dozvole i podatke.",
                422
            )

        csv_data = "\ufeff" + output.getvalue()

        return Response(
            csv_data,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition":
                'attachment; filename="instagram_comments.csv"'
            }
        )

    except Exception as error:
        return f"Greška: {str(error)}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
