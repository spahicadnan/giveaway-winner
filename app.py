
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

IG_USER_ID = "17841480659359837"
GRAPH_URL = "https://graph.facebook.com/v27.0"


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
<label>Export Key</label>
<input name="key" type="password" required
placeholder="Tvoj EXPORT_KEY" />
<button type="submit">Preuzmi komentare (CSV)</button>
</form>
</div>
</body>
</html>
"""


def api_get(endpoint, params=None):
    if not ACCESS_TOKEN:
        raise Exception("Instagram token nije postavljen na Renderu.")

    query = dict(params or {})
    query["access_token"] = ACCESS_TOKEN

    response = requests.get(
        f"{GRAPH_URL}/{endpoint}",
        params=query,
        timeout=40
    )

    try:
        data = response.json()
    except Exception:
        raise Exception("Meta API nije vratio ispravan odgovor.")

    if response.status_code != 200 or "error" in data:
        error = data.get("error", {})
        message = error.get("message", "Nepoznata Meta API greška")
        code = error.get("code", "")
        raise Exception(f"Meta API greška {code}: {message}")

    return data


def get_all_pages(endpoint, params=None):
    results = []
    data = api_get(endpoint, params or {"limit": 100})

    while True:
        results.extend(data.get("data", []))

        next_url = data.get("paging", {}).get("next")

        if not next_url:
            break

        response = requests.get(next_url, timeout=40)

        try:
            data = response.json()
        except Exception:
            raise Exception("Greška pri učitavanju naredne stranice.")

        if response.status_code != 200 or "error" in data:
            error = data.get("error", {})
            raise Exception(
                error.get("message", "Greška pri paginaciji.")
            )

    return results


def extract_shortcode(url):
    match = re.search(
        r"instagram\.com/(?:p|reel|tv)/([^/?#]+)",
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
    return {
        "status": "ok",
        "application": "Giveaway Winner"
    }


@app.route("/export", methods=["POST"])
def export_comments():

    if not ACCESS_TOKEN or not EXPORT_KEY:
        return "Nedostaju environment varijable na Renderu.", 500

    supplied_key = request.form.get("key", "")

    if not hmac.compare_digest(supplied_key, EXPORT_KEY):
        return "Neispravan Export Key.", 403

    try:
        post_url = request.form.get("post_url", "")
        shortcode = extract_shortcode(post_url)

        # Provjera pristupa Instagram profilu
        profile = api_get(
            IG_USER_ID,
            {"fields": "id,username"}
        )

        # Učitavanje objava Instagram profila
        media = get_all_pages(
            f"{IG_USER_ID}/media",
            {
                "fields": "id,permalink,comments_count,timestamp",
                "limit": 100
            }
        )

        # Pronalaženje tražene objave
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
                "Objava nije pronađena na profilu "
                + profile.get("username", "")
                + ". Provjeri link i pristup profilu.",
                404
            )

        # Preuzimanje komentara sa svim dostupnim stranicama
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
                f"Pronađeno je {len(comments)} komentara, "
                f"ali {missing_usernames} nema korisničko ime. "
                "CSV nije preuzet. Potrebna je dodatna provjera.",
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
