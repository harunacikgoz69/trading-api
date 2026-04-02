import requests
import os
import base64
from datetime import datetime, timedelta
from typing import Optional

BASE_URL = "https://apigwdev.mkk.com.tr/api/vyk"

_token_cache = {"token": None, "expires_at": None}


def _get_token() -> Optional[str]:
    now = datetime.now()
    if _token_cache["token"] and _token_cache["expires_at"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    api_key = os.environ.get("MKK_API_KEY", "")
    api_secret = os.environ.get("MKK_API_SECRET", "")

    if not api_key or not api_secret:
        return None

    credentials = f"{api_key}:{api_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    try:
        res = requests.get(
            f"{BASE_URL}/generateToken",
            headers={"Authorization": f"Basic {encoded}"},
            timeout=10,
            verify=False,
        )
        if res.status_code == 200:
            data = res.json()
            token = data.get("token") or data.get("access_token") or data.get("data")
            if token:
                _token_cache["token"] = token
                _token_cache["expires_at"] = now + timedelta(hours=23)
                return token
    except Exception as e:
        print(f"KAP token hatası: {e}")
    return None


def _get_headers() -> dict:
    token = _get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def get_kap_disclosures(member_code: str, days_back: int = 30) -> str:
    """
    Fetch KAP disclosures for a given BIST stock symbol.
    Returns formatted string of recent disclosures.
    """
    token = _get_token()
    if not token:
        return "KAP API token alınamadı — MKK_API_KEY ve MKK_API_SECRET kontrol edin."

    try:
        params = {
            "memberCode": member_code,
            "pageSize": 20,
            "pageNumber": 1,
        }
        res = requests.get(
            f"{BASE_URL}/disclosures",
            headers=_get_headers(),
            params=params,
            timeout=15,
            verify=False,
        )

        if res.status_code != 200:
            return f"KAP disclosures hatası: HTTP {res.status_code} — {res.text[:200]}"

        data = res.json()
        items = data if isinstance(data, list) else data.get("data", data.get("disclosures", []))

        if not items:
            return f"{member_code} için KAP bildirimi bulunamadı."

        output = [f"## KAP Bildirimleri — {member_code}\n"]
        for item in items[:10]:
            title = item.get("title") or item.get("subject") or item.get("baslik") or ""
            date = item.get("publishDate") or item.get("yayimTarihi") or item.get("date") or ""
            category = item.get("disclosureType") or item.get("tip") or ""
            index = item.get("disclosureIndex") or item.get("id") or ""

            output.append(f"**{date}** — {category}")
            output.append(f"{title}")
            if index:
                output.append(f"Bildirim ID: {index}\n")

        return "\n".join(output)

    except Exception as e:
        return f"KAP disclosures hatası: {str(e)}"


def get_kap_member_detail(member_code: str) -> str:
    """
    Fetch KAP member (company) details.
    """
    token = _get_token()
    if not token:
        return "KAP API token alınamadı."

    try:
        res = requests.get(
            f"{BASE_URL}/members",
            headers=_get_headers(),
            timeout=15,
            verify=False,
        )

        if res.status_code != 200:
            return f"KAP members hatası: HTTP {res.status_code}"

        data = res.json()
        members = data if isinstance(data, list) else data.get("data", [])

        member = next(
            (m for m in members if
             m.get("memberCode", "").upper() == member_code.upper() or
             m.get("kod", "").upper() == member_code.upper()),
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