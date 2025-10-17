#!/usr/bin/env python3
"""
Transform raw Shopify product data into structured formats for ERP import.
Outputs JSON, CSV, and SQL insert statements.
"""
import json
import csv
from pathlib import Path

# Input and output paths
INPUT_FILE = Path("../output/products_rest.json")
OUTPUT_DIR = Path("../output")

def normalize(products):
    """
    Flatten products and variants to a structured format.
    Each variant is a separate record.
    """
    out = []
    for p in products:
        pid = p.get("id")
        title = p.get("title")
        for v in p.get("variants", []):
            out.append({
                "product_id": pid,
                "title": title,
                "variant_id": v.get("id"),
                "sku": v.get("sku") or "",
                "price": v.get("price") or "",
                "inventory_quantity": v.get("inventory_quantity")
            })
    return out

def save_transformed(flat):
    # JSON
    (OUTPUT_DIR / "products_transformed.json").write_text(json.dumps(flat, indent=2), encoding="utf8")

    # CSV
    keys = ["product_id","title","variant_id","sku","price","inventory_quantity"]
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
        sql_lines.append(f"INSERT INTO products_erp (product_id, variant_id, title, sku, price, inventory_quantity) "
                         f"VALUES ({pid}, {vid}, '{title}', '{sku}', {price}, {qty});")
    (OUTPUT_DIR / "products_transformed.sql").write_text("\n".join(sql_lines), encoding="utf8")

def main():
    products = json.loads(INPUT_FILE.read_text(encoding="utf8"))
    flat = normalize(products)
    save_transformed(flat)
    print(f"Transformation complete: {len(flat)} variants processed.")

if __name__ == "__main__":
    main()
