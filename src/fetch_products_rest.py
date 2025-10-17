#!/usr/bin/env python3
"""
Fetch products via Shopify Admin REST API and write raw JSON to output/products_rest.json
Also produces: output/products_transformed.csv, .json, .sql
"""
import os
import sys
import json
import csv
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if it exists
load_dotenv()

# Get Shopify credentials
SHOP = os.environ.get("SHOP", "").strip()
TOKEN = os.environ.get("SHOPIFY_ADMIN_TOKEN", "").strip()

# Validate credentials before proceeding
if not SHOP or not TOKEN:
    print("ERROR: SHOP or SHOPIFY_ADMIN_TOKEN not set correctly.")
    print("Please set them in a .env file or your environment variables.")
    sys.exit(1)

# Output directory
OUTPUT_DIR = Path("../output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# REST endpoint
API_VERSION = "2025-07"
URL = f"https://{SHOP}/admin/api/{API_VERSION}/products.json?limit=250"

headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": TOKEN
}

def fetch_all_products():
    products = []
    url = URL
    while url:
        print("GET", url)
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)
            sys.exit(1)
        data = r.json()
        products.extend(data.get("products", []))

        # Pagination via Link header
        link = r.headers.get("Link", "")
        next_url = None
        if 'rel="next"' in link:
            parts = [p.strip() for p in link.split(",")]
            for p in parts:
                if 'rel="next"' in p:
                    start = p.find("<") + 1
                    end = p.find(">")
                    next_url = p[start:end]
                    break
        url = next_url
    return products

def normalize(products):
    """Extract requested fields per product/variant"""
    out = []
    for p in products:
        pid = p.get("id")
        title = p.get("title")
        for v in p.get("variants", []):
            sku = v.get("sku") or ""
            price = v.get("price") or ""
            inv_qty = v.get("inventory_quantity")
            out.append({
                "product_id": pid,
                "title": title,
                "variant_id": v.get("id"),
                "sku": sku,
                "price": price,
                "inventory_quantity": inv_qty,
                "created_at": p.get("created_at")
            })
    return out

def save_raw(products):
    path = OUTPUT_DIR / "products_rest.json"
    with open(path, "w", encoding="utf8") as f:
        json.dump(products, f, indent=2)
    print("Saved raw REST JSON:", path)

def save_transformed(flat):
    # JSON
    (OUTPUT_DIR / "products_transformed.json").write_text(json.dumps(flat, indent=2), encoding="utf8")
    # CSV
    keys = ["product_id","title","variant_id","sku","price","inventory_quantity","created_at"]
    with open(OUTPUT_DIR / "products_transformed.csv", "w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(flat)
    # SQL
    sql_lines = []
    for r in flat:
        pid = r["product_id"]
        vid = r["variant_id"]
        title = r["title"].replace("'", "''")
        sku = r["sku"].replace("'", "''")
        price = r["price"]
        qty = r["inventory_quantity"] if r["inventory_quantity"] is not None else "NULL"
        sql = f"INSERT INTO products_erp (product_id, variant_id, title, sku, price, inventory_quantity) VALUES ({pid}, {vid}, '{title}', '{sku}', {price}, {qty});"
        sql_lines.append(sql)
    (OUTPUT_DIR / "products_transformed.sql").write_text("\n".join(sql_lines), encoding="utf8")
    print("Saved transformed files to output/")

def main():
    print("SHOP:", SHOP)
    print("Fetching products...")
    products = fetch_all_products()
    save_raw(products)
    flat = normalize(products)
    save_transformed(flat)
    print("Done. Found", len(flat), "variants across", len(products), "products.")

if __name__ == "__main__":
    main()
