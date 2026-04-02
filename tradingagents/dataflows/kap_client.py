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
        # Son bildirim index'ini al
        res = requests.get(
            f"{BASE_URL}/lastDisclosureIndex",
            headers=headers,
            timeout=10,
            verify=False,
        )
        if res.status_code != 200:
            return f"KAP lastDisclosureIndex hatası: {res.status_code}"

        last_index = int(res.json().get("lastDisclosureIndex", 0))
        if not last_index:
            return "KAP son bildirim indexi alınamadı."

        # Member ID'yi al
        res_m = requests.get(f"{BASE_URL}/members", headers=headers, timeout=15, verify=False)
        members = res_m.json() if res_m.status_code == 200 else []
        if isinstance(members, dict):
            members = members.get("data", [])
        member = next(
            (m for m in members if
             m.get("stockCode", "").upper() == member_code.upper() or
             m.get("memberCode", "").upper() == member_code.upper()),
            None
        )
        member_id = str(member.get("id")) if member else None

        # Son 200 bildirimi tara, şirkete ait olanları bul
        output = [f"## KAP Bildirimleri — {member_code}\n"]
        found = 0
        for i in range(last_index, last_index - 200, -1):
            if found >= 10:
                break
            try:
                r = requests.get(
                    f"{BASE_URL}/disclosureDetail/{i}",
                    headers=headers,
                    params={"fileType": "data"},
                    timeout=10,
                    verify=False,
                )
                if r.status_code != 200:
                    continue
                d = r.json()
                if isinstance(d, list):
                    d = d[0] if d else {}

                # Şirkete ait mi kontrol et
                d_member_id = str(d.get("memberId") or d.get("member_id") or "")
                d_stock = str(d.get("stockCode") or d.get("memberCode") or "")

                if member_id and d_member_id != member_id:
                    if member_code.upper() not in d_stock.upper():
                        continue

                title = d.get("title") or d.get("subject") or d.get("baslik") or ""
                date = d.get("publishDate") or d.get("date") or ""
                category = d.get("disclosureType") or d.get("tip") or ""
                output.append(f"**{date}** — {category}: {title}")
                found += 1
            except:
                continue

        if found == 0:
            return f"{member_code} için son 200 bildirimde kayıt bulunamadı."

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