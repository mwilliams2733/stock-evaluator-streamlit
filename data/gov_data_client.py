"""Government data clients — USAspending.gov and Federal Register APIs."""

import requests

from data.cache import get_cached, set_cached

GOV_CACHE_TTL = 3600  # 1 hour


def fetch_usaspending_contracts(
    keyword: str,
    naics_codes: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Fetch federal contract awards from USAspending.gov.

    Args:
        keyword: Search keyword (e.g., 'artificial intelligence').
        naics_codes: Optional NAICS industry codes to filter.
        limit: Max results to return.

    Returns:
        List of contract dicts with recipient, amount, agency, date, description.
    """
    cache_key = f"usaspending_{keyword}_{naics_codes}"
    cached = get_cached(cache_key, GOV_CACHE_TTL)
    if cached is not None:
        return cached

    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    filters = {
        "keywords": [keyword],
        "award_type_codes": ["A", "B", "C", "D"],  # Contracts
        "time_period": [
            {
                "start_date": "2024-01-01",
                "end_date": "2026-12-31",
            }
        ],
    }
    if naics_codes:
        filters["naics_codes"] = naics_codes

    payload = {
        "filters": filters,
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Awarding Agency",
            "Start Date",
            "Description",
        ],
        "limit": limit,
        "page": 1,
        "sort": "Award Amount",
        "order": "desc",
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for row in data.get("results", []):
            results.append({
                "award_id": row.get("Award ID", ""),
                "recipient": row.get("Recipient Name", "Unknown"),
                "amount": row.get("Award Amount", 0),
                "agency": row.get("Awarding Agency", ""),
                "date": row.get("Start Date", ""),
                "description": row.get("Description", ""),
            })

        set_cached(cache_key, results)
        return results

    except Exception:
        return []


def fetch_federal_register(
    search_terms: list[str],
    limit: int = 10,
) -> list[dict]:
    """Fetch recent actions from the Federal Register.

    Args:
        search_terms: List of search terms.
        limit: Max results to return.

    Returns:
        List of document dicts with title, type, agencies, date, abstract, url.
    """
    query = " ".join(search_terms)
    cache_key = f"fedreg_{query}"
    cached = get_cached(cache_key, GOV_CACHE_TTL)
    if cached is not None:
        return cached

    url = "https://www.federalregister.gov/api/v1/documents.json"
    params = {
        "conditions[term]": query,
        "per_page": limit,
        "order": "newest",
        "fields[]": [
            "title", "type", "agencies", "publication_date",
            "abstract", "html_url",
        ],
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for doc in data.get("results", []):
            agencies = doc.get("agencies", [])
            agency_names = [a.get("name", "") for a in agencies if isinstance(a, dict)]

            results.append({
                "title": doc.get("title", ""),
                "type": doc.get("type", ""),
                "agencies": agency_names,
                "date": doc.get("publication_date", ""),
                "abstract": doc.get("abstract", ""),
                "url": doc.get("html_url", ""),
            })

        set_cached(cache_key, results)
        return results

    except Exception:
        return []


def search_gov_opportunities(theme_key: str) -> dict:
    """Combined government opportunity search for a theme.

    Args:
        theme_key: Key from GOVERNMENT_THEMES (e.g., 'ai_semiconductor').

    Returns:
        Dict with 'contracts' and 'regulations' lists.
    """
    from config.themes import GOVERNMENT_THEMES

    theme = GOVERNMENT_THEMES.get(theme_key, {})
    if not theme:
        return {"contracts": [], "regulations": []}

    name = theme.get("name", theme_key)
    keywords = theme.get("keywords", [name])
    naics = theme.get("naics_codes", None)

    # Fetch contracts using theme name
    search_term = keywords[0] if keywords else name
    contracts = fetch_usaspending_contracts(search_term, naics)

    # Fetch federal register documents
    regulations = fetch_federal_register(keywords[:3])

    return {
        "theme": name,
        "contracts": contracts,
        "regulations": regulations,
    }
