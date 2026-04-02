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
        BASE = BASE_URL
        # Son index al
        r1 = requests.get(f"{BASE}/lastDisclosureIndex", headers=headers, timeout=10, verify=False)
        if r1.status_code != 200:
            return f"KAP lastDisclosureIndex hatası: {r1.status_code}"
        last_index = int(r1.json().get("lastDisclosureIndex", 0))

        output = [f"## KAP Bildirimleri — {member_code}\n"]
        found = 0
        for i in range(last_index, last_index - 500, -1):
            if found >= 10:
                break
            try:
                r = requests.get(
                    f"{BASE}/disclosureDetail/{i}",
                    headers=headers,
                    params={"fileType": "data"},
                    timeout=8,
                    verify=False,
                )
                if r.status_code != 200:
                    continue
                d = r.json()

                # Şirkete ait mi? senderExchCodes veya senderId ile kontrol
                exch_codes = d.get("senderExchCodes") or d.get("behalfSenderExchCodes") or []
                sender_title = d.get("senderTitle") or ""

                if member_code.upper() not in [c.upper() for c in exch_codes]:
                    if member_code.upper() not in sender_title.upper():
                        continue

                subject = d.get("subject") or {}
                title = subject.get("tr") or subject.get("en") or ""
                date = d.get("time") or d.get("publishDate") or ""
                category = d.get("disclosureType") or ""
                disclosure_index = d.get("disclosureIndex") or i

                output.append(f"**{date[:10]}** — {category}: {title} (ID: {disclosure_index})")
                found += 1
            except:
                continue

        if found == 0:
            return f"{member_code} için son 500 bildirimde kayıt bulunamadı."

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