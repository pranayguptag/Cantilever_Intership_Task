from flask import Flask, render_template, request
import sqlite3
import pandas as pd

app = Flask(__name__)

DB_NAME = "ecommerce.db"
TABLE_NAME = "products"


# ---------- LOAD DATA ----------
def load_data(query=None, min_price=None, max_price=None):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()

    # Clean Price for filtering
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df.dropna(subset=["Price"])

    # Apply search filter
    if query:
        df = df[df["Title"].str.contains(query, case=False, na=False)]

    # Apply price filter
    if min_price:
        df = df[df["Price"] >= float(min_price)]
    if max_price:
        df = df[df["Price"] <= float(max_price)]

    return df


# ---------- ROUTES ----------
@app.route("/", methods=["GET", "POST"])
def index():
    query = request.form.get("query")
    min_price = request.form.get("min_price")
    max_price = request.form.get("max_price")

    df = load_data(query, min_price, max_price)

    return render_template("index.html", tables=df.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True)
