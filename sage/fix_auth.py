import json
import os

mcp_cookies_path = r"C:\Users\mehta\.notebooklm-mcp-cli\profiles\default\cookies.json"
notebooklm_cookies_path = r"C:\Users\mehta\.notebooklm\storage_state.json"

with open(mcp_cookies_path, "r", encoding="utf-8") as f:
    mcp_cookies = json.load(f)

playwright_cookies = []
for c in mcp_cookies:
    pc = {
        "name": c["name"],
        "value": c["value"],
        "domain": c["domain"],
        "path": c["path"],
        "expires": c["expires"],
        "httpOnly": c["httpOnly"],
        "secure": c["secure"]
    }
    if "sameSite" in c:
        pc["sameSite"] = c["sameSite"]
    playwright_cookies.append(pc)

state = {
    "cookies": playwright_cookies,
    "origins": [{"origin": "https://notebooklm.google.com", "localStorage": [{"name": "_gcl_ls", "value": "{\"schema\":\"gcl\",\"version\":1,\"gcl_ctr\":{\"value\":{\"value\":0,\"timeouts\":0,\"errors\":0,\"creationTimeMs\":1772867884505},\"expires\":1780643884505}}"}, {"name": "bcsp", "value": "system"}]}]
}

os.makedirs(os.path.dirname(notebooklm_cookies_path), exist_ok=True)
with open(notebooklm_cookies_path, "w", encoding="utf-8") as f:
    json.dump(state, f)

print("Auth state created successfully!")
