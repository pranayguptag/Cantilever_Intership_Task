# app.py
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import sqlite3
import io, base64
import matplotlib.pyplot as plt
import seaborn as sns

from Scraper import run_scrapers_and_update_db, DB_NAME, TABLE_NAME
import os
from flask import send_file

app = Flask(__name__)


def load_data_from_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    except Exception:
        # empty DB or table does not exist
        df = pd.DataFrame(columns=["Source", "Title", "Price", "Rating", "Link"])
    conn.close()
    return df


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        use_amazon = request.form.get("amazon")=="on"
        use_myntra = request.form.get("myntra")=="on"
        use_flipkart = request.form.get("flipkart")=="on"
        # optional number of pages (keep small)
        pages = int(request.form.get("pages", 1))
        # headless option toggle (helpful for debugging)
        headless = True if request.form.get("headless") == "on" else False

        if not query:
            return render_template("home.html", message="Please enter a product to search.", example="shoes")

        if use_flipkart and not (use_amazon or use_myntra):
            return render_template("home.html", message="⚠ Flipkart requires Amazon or Myntra for comparison.", example="shoes")

        # Run scrapers synchronously (blocking) — this saves & cleans DB
        run_scrapers_and_update_db(query, use_amazon, use_myntra, use_flipkart, max_pages=pages, headless=headless)

        return redirect(url_for("products"))

    # GET request - render form
    return render_template("home.html", message=None, example="shoes")


@app.route("/products")
def products():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()

    # Ensure numeric
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df.dropna(subset=["Price"])

    cheapest = df.nsmallest(5, "Price").to_dict(orient="records")
    expensive = df.nlargest(5, "Price").to_dict(orient="records")

    return render_template("products.html",
                           tables=df.to_dict(orient="records"),
                           cheapest=cheapest,
                           expensive=expensive)


@app.route("/download_csv")
def download_csv():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()

    # Ensure numeric for price
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df.dropna(subset=["Price"])

    # Save CSV in project directory (safe)
    file_path = os.path.join(os.getcwd(), "scraped_data.csv")
    df.to_csv(file_path, index=False, encoding="utf-8-sig")

    return send_file(file_path, as_attachment=True)


@app.route("/visuals")
def visuals():
    df = load_data_from_db()
    plots = {}

    if df.empty:
        return render_template("visuals.html", plots={}, message="No data available. Run a search first.")

    # Price distribution
    fig, ax = plt.subplots(figsize=(10,5))
    sns.histplot(data=df, x="Price", hue="Source", bins=30, kde=True, element="step", ax=ax)
    ax.set_title("Price Distribution")
    plots["price_dist"] = fig_to_base64(fig)

    # Boxplot
    fig, ax = plt.subplots(figsize=(8,5))
    sns.boxplot(x="Source", y="Price", data=df, ax=ax, palette={"Amazon":"#FF9900","Myntra":"#E91E63"})
    ax.set_title("Price Comparison (Amazon vs Myntra)")
    plots["boxplot"] = fig_to_base64(fig)

    # Avg price
    avg_price = df.groupby("Source")["Price"].mean()
    fig, ax = plt.subplots(figsize=(6,4))
    avg_price.plot(kind="bar", color=["#FF9900","#E91E63"], ax=ax)
    ax.set_title("Average Price")
    plots["avg_price"] = fig_to_base64(fig)

    # Amazon ratings
    try:
        amazon_only = df[df["Source"] == "Amazon"].dropna(subset=["Rating"])
        if not amazon_only.empty:
            fig, ax = plt.subplots(figsize=(6,4))
            sns.histplot(amazon_only, x="Rating", bins=10, kde=True, ax=ax, color="#FF9900")
            ax.set_title("Amazon Ratings")
            plots["amazon_ratings"] = fig_to_base64(fig)
    except Exception:
        pass

    return render_template("visuals.html", plots=plots, message=None)


if __name__ == "__main__":
    app.run(debug=True)
