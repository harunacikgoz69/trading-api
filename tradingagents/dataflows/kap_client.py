import requests
import os
import base64

BASE_URL = "https://apigw.mkk.com.tr/api/vyk"
BASE_URL_DEV = "https://apigwdev.mkk.com.tr/api/vyk"


def _get_headers() -> dict:
    api_key = os.environ.get("MKK_API_KEY", "")
    api_secret = os.environ.get("MKK_API_SECRET", "")
    if not api_key or not api_secret:
        return {}
    encoded = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def _get(url, headers, params=None, timeout=20):
    """Try prod first, fallback to dev."""
    try:
        r = requests.get(url, headers=headers, params=params, timeout=timeout, verify=False)
        if r.status_code in [200, 400, 404]:
            return r
    except Exception:
        pass
    dev_url = url.replace("apigw.mkk.com.tr", "apigwdev.mkk.com.tr")
    return requests.get(dev_url, headers=headers, params=params, timeout=timeout, verify=False)


def get_kap_disclosures(member_code: str) -> str:
    headers = _get_headers()
    if not headers:
        return "KAP API credentials eksik."
    try:
        r1 = _get(f"{BASE_URL}/lastDisclosureIndex", headers=headers, timeout=20)
        if r1.status_code != 200:
            return f"KAP lastDisclosureIndex hatası: {r1.status_code}"
        last_index = int(r1.json().get("lastDisclosureIndex", 0))

        r_m = _get(f"{BASE_URL}/members", headers=headers, timeout=20)
        members = r_m.json() if r_m.status_code == 200 else []
        if isinstance(members, dict):
            members = members.get("data", [])
        member = next(
            (m for m in members if m.get("stockCode", "").upper() == member_code.upper()),
            None
        )
        company_id = str(member.get("id")) if member else None
        if not company_id:
            return f"{member_code} için KAP üye ID bulunamadı."

        all_items = []
        step = 50
        search_from = max(0, last_index - 5000)

        for start_idx in range(search_from, last_index + 1, step):
            r = _get(
                f"{BASE_URL}/disclosures",
                headers=headers,
                params={"disclosureIndex": str(start_idx), "companyId": company_id},
                timeout=15,
            )
            if r.status_code == 200:
                items = r.json()
                if isinstance(items, list) and items:
                    all_items.extend(items)

        all_items.sort(key=lambda x: int(x.get("disclosureIndex", 0)), reverse=True)
        seen = set()
        unique_items = []
        for item in all_items:
            idx = item.get("disclosureIndex")
            if idx not in seen:
                seen.add(idx)
                unique_items.append(item)

        if not unique_items:
            return f"{member_code} için KAP bildirimi bulunamadı."

        output = [f"## KAP Bildirimleri — {member_code} (Son {len(unique_items)} bildirim)\n"]
        for item in unique_items[:10]:
            category = item.get("disclosureType") or ""
            disc_class = item.get("disclosureClass") or ""
            disc_index = item.get("disclosureIndex") or ""
            try:
                r_d = _get(
                    f"{BASE_URL}/disclosureDetail/{disc_index}",
                    headers=headers,
                    params={"fileType": "data"},
                    timeout=15,
                )
                if r_d.status_code == 200:
                    d = r_d.json()
                    subject = d.get("subject") or {}
                    title = subject.get("tr") or subject.get("en") or ""
                    date = d.get("time") or ""
                    summary = d.get("summary") or {}
                    summary_text = summary.get("tr") or summary.get("en") or ""
                    output.append(f"**{date[:10]} — {disc_class}/{category}**: {title}")
                    if summary_text and summary_text != title:
                        output.append(f"  {summary_text[:200]}")
                else:
                    output.append(f"**{disc_class}/{category}**: ID {disc_index}")
            except:
                output.append(f"**{disc_class}/{category}**: ID {disc_index}")

        return "\n".join(output)
    except Exception as e:
        return f"KAP disclosures hatası: {str(e)}"


def get_kap_member_detail(member_code: str) -> str:
    headers = _get_headers()
    if not headers:
        return "KAP API credentials eksik."
    try:
        res = _get(f"{BASE_URL}/members", headers=headers, timeout=20)
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