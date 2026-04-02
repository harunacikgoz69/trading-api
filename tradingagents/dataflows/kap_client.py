import requests
import os
import base64
from typing import Optional

BASE_URL = "https://apigwdev.mkk.com.tr/api/vyk"


def _get_headers() -> dict:
    api_key = os.environ.get("MKK_API_KEY", "")
    api_secret = os.environ.get("MKK_API_SECRET", "")
    if not api_key or not api_secret:
        return {}
    encoded = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def get_kap_disclosures(member_code: str) -> str:
    headers = _get_headers()
    if not headers:
        return "KAP API credentials eksik."
    try:
        # Son index al
        r1 = requests.get(f"{BASE_URL}/lastDisclosureIndex", headers=headers, timeout=10, verify=False)
        if r1.status_code != 200:
            return f"KAP lastDisclosureIndex hatası: {r1.status_code}"
        last_index = r1.json().get("lastDisclosureIndex", "0")

        # Member ID'yi al
        r_m = requests.get(f"{BASE_URL}/members", headers=headers, timeout=15, verify=False)
        members = r_m.json() if r_m.status_code == 200 else []
        if isinstance(members, dict):
            members = members.get("data", [])
        member = next(
            (m for m in members if
             m.get("stockCode", "").upper() == member_code.upper()),
            None
        )
        company_id = str(member.get("id")) if member else None

        # companyId filtresiyle disclosures listesi çek
        params = {"disclosureIndex": last_index}
        if company_id:
            params["companyId"] = company_id

        r2 = requests.get(
            f"{BASE_URL}/disclosures",
            headers=headers,
            params=params,
            timeout=15,
            verify=False,
        )

        if r2.status_code != 200:
            return f"KAP disclosures hatası: HTTP {r2.status_code} — {r2.text[:200]}"

        items = r2.json()
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            items = []

        # companyId ile filtrele
        if company_id:
            items = [i for i in items if str(i.get("companyId", "")) == company_id]

        if not items:
            return f"{member_code} için KAP bildirimi bulunamadı (companyId: {company_id})."

        output = [f"## KAP Bildirimleri — {member_code}\n"]
        for item in items[:15]:
            title = item.get("title") or ""
            category = item.get("disclosureType") or ""
            disc_class = item.get("disclosureClass") or ""
            disc_index = item.get("disclosureIndex") or ""
            output.append(f"**{disc_class}/{category}**: {title} (ID: {disc_index})")

        return "\n".join(output)
    except Exception as e:
        return f"KAP disclosures hatası: {str(e)}"

def get_kap_member_detail(member_code: str) -> str:
    headers = _get_headers()
    if not headers:
        return "KAP API credentials eksik."
    try:
        res = requests.get(
            f"{BASE_URL}/members",
            headers=headers,
            timeout=15,
            verify=False,
        )
        if res.status_code != 200:
            return f"KAP members hatası: HTTP {res.status_code}"

        members = res.json()
        if isinstance(members, dict):
            members = members.get("data", [])

        member = next(
            (m for m in members if
             m.get("memberCode", "").upper() == member_code.upper() or
             m.get("stockCode", "").upper() == member_code.upper()),
            None
        )
        if not member:
            return f"{member_code} için KAP üye bilgisi bulunamadı."

        output = [f"## KAP Şirket Bilgileri — {member_code}\n"]
        for key, val in member.items():
            if val and str(val).strip():
                output.append(f"**{key}**: {val}")
        return "\n".join(output)
    except Exception as e:
        return f"KAP member detail hatası: {str(e)}"