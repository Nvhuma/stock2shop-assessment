#!/usr/bin/env python3
"""
Fetch products via Shopify GraphQL API and save raw JSON.
"""
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()
SHOP = os.environ.get("SHOP", "").strip()
TOKEN = os.environ.get("SHOPIFY_ADMIN_TOKEN", "").strip()
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not SHOP or not TOKEN:
    print("ERROR: SHOP or SHOPIFY_ADMIN_TOKEN not set correctly.")
    exit(1)

# GraphQL endpoint
URL = f"https://{SHOP}/admin/api/2025-07/graphql.json"

# GraphQL query
QUERY = """
{
  products(first: 10) {
    edges {
      node {
        id
        title
        variants(first: 5) {
          edges {
            node {
              id
              sku
              price
              inventoryQuantity
            }
          }
        }
      }
    }
  }
}
"""

headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": TOKEN
}

def fetch_products():
    response = requests.post(URL, headers=headers, json={"query": QUERY})
    response.raise_for_status()
    return response.json()

def main():
    data = fetch_products()
    path = OUTPUT_DIR / "products_graphql.json"
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2)
    print(f"GraphQL fetch complete, saved to {path}")

if __name__ == "__main__":
    main()
