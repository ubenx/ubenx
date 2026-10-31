"""Haalt GitHub-statistieken op en zet ze in dark_mode.svg en light_mode.svg."""
import os
import requests
from lxml import etree

TOKEN = os.environ["ACCESS_TOKEN"]
USER = os.environ["USER_NAME"]

QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100, after: $cursor) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { stargazers { totalCount } }
    }
  }
}
"""

def graphql(variables):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": variables},
        headers={"Authorization": f"bearer {TOKEN}"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["user"]

# Alle repos ophalen (per 100) en de stars optellen
stars, cursor = 0, None
while True:
    user = graphql({"login": USER, "cursor": cursor})
    repos = user["repositories"]
    stars += sum(n["stargazers"]["totalCount"] for n in repos["nodes"])
    if not repos["pageInfo"]["hasNextPage"]:
        break
    cursor = repos["pageInfo"]["endCursor"]

stats = {
    "repo_data": repos["totalCount"],
    "star_data": stars,
    "follower_data": user["followers"]["totalCount"],
}
print(stats)

def set_value(root, key, value):
    el = root.find(f".//*[@id='{key}']")
    dots = root.find(f".//*[@id='{key}_dots']")
    if el is None:
        return
    old_len = len(el.text or "")
    new = f"{value:,}"
    el.text = new
    if dots is not None:
        # puntjes langer/korter maken zodat de rechterkant uitgelijnd blijft
        n = max(len(dots.text.strip()) + old_len - len(new), 1)
        dots.text = " " + "." * n + " "

for f in ["dark_mode.svg", "light_mode.svg"]:
    tree = etree.parse(f)
    for k, v in stats.items():
        set_value(tree.getroot(), k, v)
    tree.write(f, encoding="utf-8", xml_declaration=True)
