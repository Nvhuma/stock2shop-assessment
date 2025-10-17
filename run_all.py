import subprocess

scripts = [
    "src/fetch_products_rest.py",
    "src/transform.py",
    "src/fetch_products_graphql.py"
]

for s in scripts:
    print(f"Running {s}...")
    subprocess.run(["python", s], check=True)
