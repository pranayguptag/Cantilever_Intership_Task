import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------- LOAD DATA ----------
def load_data(db_name="ecommerce.db", table_name="products"):
    conn = sqlite3.connect(db_name)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# ---------- CLEAN DATA ----------
def clean_data(df):
    # Make sure Price is string
    df["Price"] = df["Price"].astype(str)

    # Remove ₹, commas, extract numbers
    df["Price"] = (
        df["Price"]
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.extract(r"(\d+)")
    )

    # Convert to numeric safely
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # Drop rows with invalid price
    df = df.dropna(subset=["Price"]).copy()

    # ✅ Force dtype float
    df["Price"] = df["Price"].astype(float)

    # Clean Rating (Amazon style: "4.3 out of 5 stars")
    df["Rating"] = df["Rating"].astype(str).str.extract(r"(\d+\.\d+)")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

    return df


# ---------- VISUALIZATION ----------
def visualize(df):
    print("\nData types after cleaning:\n", df.dtypes)
    print("\nSample rows:\n", df.head())

    # ✅ Average prices check (now safe after cleaning)
    print("\nAverage prices check:\n", df.groupby("Source")["Price"].mean())

    # Price Distribution
    plt.figure(figsize=(12,6))
    sns.histplot(data=df, x="Price", hue="Source", bins=30, kde=True, element="step")
    plt.title("Price Distribution - Amazon vs Myntra (Shoes)")
    plt.xlabel("Price (₹)")
    plt.ylabel("Count")
    plt.show()

    # Boxplot
    plt.figure(figsize=(8,5))
    sns.boxplot(x="Source", y="Price", data=df, palette={"Amazon":"#FF9900","Myntra":"#E91E63"})
    plt.title("Price Comparison (Amazon vs Myntra - Shoes)")
    plt.ylabel("Price (₹)")
    plt.show()

    # Ratings Distribution (Amazon only)
    amazon_only = df[df["Source"]=="Amazon"].dropna(subset=["Rating"])
    if not amazon_only.empty:
        plt.figure(figsize=(8,5))
        sns.histplot(amazon_only, x="Rating", bins=10, kde=True, color="#FF9900")
        plt.title("Amazon Ratings Distribution (Shoes)")
        plt.xlabel("Rating")
        plt.ylabel("Count")
        plt.show()

    # Average Price Bar Chart
    plt.figure(figsize=(6,4))
    avg_price = df.groupby("Source")["Price"].mean()
    avg_price.plot(kind="bar", color=["#FF9900","#E91E63"])
    plt.title("Average Price by Platform (Shoes)")
    plt.ylabel("Avg Price (₹)")
    plt.xticks(rotation=0)
    plt.show()


# ---------- RUN ----------
if __name__ == "__main__":
    df = load_data()
    df = clean_data(df)   # ✅ clean before using Price
    visualize(df)
