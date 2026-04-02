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
        # Önce member ID'yi al
        res = requests.get(
            f"{BASE_URL}/members",
            headers=headers,
            timeout=15,
            verify=False,
        )
        members = res.json() if res.status_code == 200 else []
        if isinstance(members, dict):
            members = members.get("data", [])

        member = next(
            (m for m in members if
             m.get("stockCode", "").upper() == member_code.upper() or
             m.get("memberCode", "").upper() == member_code.upper()),
            None
        )
        member_id = member.get("id") if member else None

        # disclosures endpoint'ini dene
        params = {}
        if member_id:
            params["memberId"] = member_id

        res2 = requests.get(
            f"{BASE_URL}/disclosures",
            headers=headers,
            params=params,
            timeout=15,
            verify=False,
        )

        if res2.status_code != 200:
            # Son bildirim index ile dene
            res3 = requests.get(
                f"{BASE_URL}/lastDisclosureIndex",
                headers=headers,
                timeout=10,
                verify=False,
            )
            return f"disclosures HTTP {res2.status_code}: {res2.text[:300]}\nlastIndex: {res3.text[:200] if res3.status_code==200 else res3.status_code}"

        items = res2.json()
        if isinstance(items, dict):
            items = items.get("data", items.get("disclosures", [items]))
        if not isinstance(items, list):
            items = [items]
        if not items:
            return f"{member_code} için KAP bildirimi bulunamadı."

        output = [f"## KAP Bildirimleri — {member_code}\n"]
        for item in items[:10]:
            title = (item.get("title") or item.get("subject") or
                     item.get("baslik") or str(item))
            date = (item.get("publishDate") or item.get("yayimTarihi") or
                    item.get("date") or "")
            category = item.get("disclosureType") or item.get("tip") or ""
            output.append(f"**{date}** — {category}: {title}")

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