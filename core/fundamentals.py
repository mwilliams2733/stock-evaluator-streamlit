"""Fundamental analysis — Moat score, Fair value, Growth score, Derived metrics."""
import math
from config.settings import MOAT_FACTOR_WEIGHTS, SECTOR_MULTIPLES, get_sector_from_sic


# ------------------------------------------------------------------
# Process raw financial statements into computed metrics
# ------------------------------------------------------------------

def process_financials(raw_financials: list[dict], finnhub_metrics: dict) -> dict:
    """Convert raw Polygon financial statements into computed ratios.

    Takes the latest and previous quarter to calculate growth rates and
    all the metrics needed for moat scoring and fair value.
    """
    if not raw_financials:
        return {}

    latest = raw_financials[0]
    previous = raw_financials[1] if len(raw_financials) > 1 else {}

    result = {
        "eps": latest.get("eps_basic"),
        "eps_growth": None,
        "revenue": latest.get("revenues"),
        "revenue_growth": None,
        "net_income": latest.get("net_income"),
        "operating_income": latest.get("operating_income"),
        "free_cash_flow": None,
        "book_value": latest.get("equity"),
        "total_debt": None,
        "total_equity": latest.get("equity"),
        "total_assets": latest.get("total_assets"),
        "operating_margin": None,
        "gross_margin": None,
        "roe": None,
        "roa": None,
        "current_ratio": None,
        "debt_to_equity": None,
        "dividend_yield": None,
        "shares_outstanding": None,
        # New extended metrics
        "cash_conversion_ratio": None,
        "fcf_margin": None,
        "roic": None,
        "interest_coverage": None,
        "ebitda": None,
        "cash_and_equivalents": latest.get("cash_and_equivalents"),
    }

    # --- Total Debt ---
    long_term = latest.get("long_term_debt") or 0
    short_term = latest.get("debt_current") or 0
    result["total_debt"] = (long_term + short_term) or None

    # --- Margins ---
    revenue = latest.get("revenues")
    cost_of_rev = latest.get("cost_of_revenue")
    if revenue and cost_of_rev and revenue > 0:
        result["gross_margin"] = ((revenue - cost_of_rev) / revenue) * 100

    op_income = latest.get("operating_income")
    if revenue and op_income and revenue > 0:
        result["operating_margin"] = (op_income / revenue) * 100

    # --- Growth ---
    prev_eps = previous.get("eps_basic")
    if prev_eps and result["eps"] and abs(prev_eps) > 0:
        result["eps_growth"] = ((result["eps"] - prev_eps) / abs(prev_eps)) * 100

    prev_rev = previous.get("revenues")
    if prev_rev and revenue and prev_rev > 0:
        result["revenue_growth"] = ((revenue - prev_rev) / prev_rev) * 100

    # --- Ratios ---
    equity = latest.get("equity")
    net_income = latest.get("net_income")
    total_assets = latest.get("total_assets")

    if net_income and equity and equity != 0:
        result["roe"] = (net_income / equity) * 100
    if net_income and total_assets and total_assets != 0:
        result["roa"] = (net_income / total_assets) * 100

    current_assets = latest.get("current_assets") or 0
    current_liabilities = latest.get("current_liabilities") or 0
    if current_liabilities > 0:
        result["current_ratio"] = current_assets / current_liabilities

    if equity and result["total_debt"]:
        result["debt_to_equity"] = result["total_debt"] / equity

    # --- Free Cash Flow ---
    op_cf = latest.get("operating_cash_flow") or 0
    inv_cf = latest.get("investing_cash_flow") or 0
    capex = abs(inv_cf)
    result["free_cash_flow"] = op_cf - capex

    # --- Cash Conversion Ratio ---
    if op_cf and net_income and net_income > 0:
        result["cash_conversion_ratio"] = op_cf / net_income

    # --- FCF Margin ---
    if result["free_cash_flow"] and revenue and revenue > 0:
        result["fcf_margin"] = (result["free_cash_flow"] / revenue) * 100

    # --- ROIC ---
    if op_income and equity:
        tax_rate = 0.21
        if net_income and op_income:
            tax_rate = max(0, min(0.5, 1 - (net_income / op_income)))
        nopat = op_income * (1 - tax_rate)
        invested_capital = (equity or 0) + (result["total_debt"] or 0)
        if invested_capital > 0:
            result["roic"] = (nopat / invested_capital) * 100

    # --- Interest Coverage ---
    interest_exp = latest.get("interest_expense")
    if op_income and interest_exp and interest_exp != 0:
        result["interest_coverage"] = op_income / abs(interest_exp)

    # --- EBITDA ---
    depreciation = latest.get("depreciation") or 0
    if op_income:
        result["ebitda"] = op_income + abs(depreciation)

    # --- Fill from Finnhub if missing ---
    if finnhub_metrics:
        if not result["dividend_yield"]:
            result["dividend_yield"] = finnhub_metrics.get("dividend_yield")
        if not result["shares_outstanding"]:
            result["shares_outstanding"] = finnhub_metrics.get("shares_outstanding")
        if not result["eps"]:
            result["eps"] = finnhub_metrics.get("eps")
        if not result["roe"]:
            result["roe"] = finnhub_metrics.get("roe")
        if not result["roa"]:
            result["roa"] = finnhub_metrics.get("roa")
        if not result["current_ratio"]:
            result["current_ratio"] = finnhub_metrics.get("current_ratio")

    return result


# ------------------------------------------------------------------
# Economic Moat Score (0-100)
# ------------------------------------------------------------------

def calculate_moat_score(financials: dict, company_details: dict) -> dict:
    """Calculate 8-factor economic moat score.

    Factors: grossMargin, roe, revenueGrowth, lowDebt, marketPosition,
    fcf, ccr, roic — matching the HTML app's logic.

    Returns:
        Dict with moat_score (0-100), moat_rating, factors, max_scores.
    """
    factors = {}

    # 1. Gross Margin (0-20 pts)
    gm = financials.get("gross_margin")
    if gm is not None:
        if gm > 60:
            factors["grossMargin"] = 20
        elif gm > 40:
            factors["grossMargin"] = 15
        elif gm > 25:
            factors["grossMargin"] = 8
        elif gm > 15:
            factors["grossMargin"] = 4
        else:
            factors["grossMargin"] = 0
    else:
        factors["grossMargin"] = None

    # 2. ROE (0-15 pts)
    roe = financials.get("roe")
    if roe is not None:
        if roe > 20:
            factors["roe"] = 15
        elif roe > 15:
            factors["roe"] = 12
        elif roe > 10:
            factors["roe"] = 7
        elif roe > 5:
            factors["roe"] = 3
        else:
            factors["roe"] = 0
    else:
        factors["roe"] = None

    # 3. Revenue Growth (0-12 pts)
    rev_growth = financials.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth > 15:
            factors["revenueGrowth"] = 12
        elif rev_growth > 8:
            factors["revenueGrowth"] = 8
        elif rev_growth > 0:
            factors["revenueGrowth"] = 4
        else:
            factors["revenueGrowth"] = 0
    else:
        factors["revenueGrowth"] = None

    # 4. Low Debt (0-13 pts)
    de = financials.get("debt_to_equity")
    if de is not None:
        if de < 0.3:
            factors["lowDebt"] = 13
        elif de < 0.5:
            factors["lowDebt"] = 10
        elif de < 1.0:
            factors["lowDebt"] = 7
        elif de < 2.0:
            factors["lowDebt"] = 3
        else:
            factors["lowDebt"] = 0
    else:
        factors["lowDebt"] = None

    # 5. Market Position (0-12 pts) — based on market cap
    market_cap = company_details.get("market_cap")
    if market_cap:
        if market_cap > 50e9:
            factors["marketPosition"] = 12
        elif market_cap > 10e9:
            factors["marketPosition"] = 8
        elif market_cap > 2e9:
            factors["marketPosition"] = 4
        else:
            factors["marketPosition"] = 2
    else:
        factors["marketPosition"] = None

    # 6. Free Cash Flow (0-8 pts)
    fcf = financials.get("free_cash_flow")
    if fcf is not None:
        if fcf > 0:
            revenue = financials.get("revenue") or 0
            if revenue > 0 and (fcf / revenue) > 0.15:
                factors["fcf"] = 8
            else:
                factors["fcf"] = 5
        else:
            factors["fcf"] = 0
    else:
        factors["fcf"] = None

    # 7. Cash Conversion Ratio (0-10 pts)
    ccr = financials.get("cash_conversion_ratio")
    if ccr is not None:
        if ccr > 1.2:
            factors["ccr"] = 10
        elif ccr > 1.0:
            factors["ccr"] = 8
        elif ccr > 0.8:
            factors["ccr"] = 5
        elif ccr > 0.5:
            factors["ccr"] = 2
        else:
            factors["ccr"] = 0
    else:
        factors["ccr"] = None

    # 8. ROIC (0-10 pts)
    roic = financials.get("roic")
    if roic is not None:
        if roic > 20:
            factors["roic"] = 10
        elif roic > 15:
            factors["roic"] = 8
        elif roic > 10:
            factors["roic"] = 5
        elif roic > 5:
            factors["roic"] = 2
        else:
            factors["roic"] = 0
    else:
        factors["roic"] = None

    # Calculate total from available factors
    total_score = 0
    max_possible = 0
    max_scores = MOAT_FACTOR_WEIGHTS

    for key in max_scores:
        if factors.get(key) is not None:
            total_score += factors[key]
            max_possible += max_scores[key]

    normalized = round((total_score / max_possible) * 100) if max_possible > 0 else None

    moat_rating = "No Moat"
    if normalized is not None:
        if normalized >= 75:
            moat_rating = "Wide Moat"
        elif normalized >= 55:
            moat_rating = "Narrow Moat"

    return {
        "moat_score": normalized,
        "moat_rating": moat_rating,
        "factors": factors,
        "max_scores": max_scores,
    }


# ------------------------------------------------------------------
# Fair Value (5-model weighted)
# ------------------------------------------------------------------

def calculate_fair_value(financials: dict, price: float,
                         company_info: dict) -> dict | None:
    """Calculate fair value using up to 5 valuation models.

    Models: P/E, P/B, P/S, DCF (simple), EV/EBITDA.

    Returns:
        Dict with models list, weighted_fair_value, premium_discount_pct, or None.
    """
    if not price or price <= 0:
        return None

    sic_code = company_info.get("sic_code")
    sector = get_sector_from_sic(sic_code)
    multiples = SECTOR_MULTIPLES.get(sector, SECTOR_MULTIPLES["default"])

    valuations = []
    total_weight = 0

    # 1. P/E Multiple (weight 25%)
    eps = financials.get("eps")
    if eps and eps > 0:
        pe_value = eps * multiples["pe"]
        valuations.append({
            "model": "P/E Multiple",
            "value": pe_value,
            "weight": 25,
            "details": f"EPS ${eps:.2f} x {multiples['pe']} P/E",
        })
        total_weight += 25

    # 2. P/B Multiple (weight 20%)
    book_value = financials.get("book_value")
    shares = financials.get("shares_outstanding")
    if book_value and shares and shares > 0:
        bvps = book_value / (shares * 1_000_000)  # Finnhub reports in millions
        if bvps > 0:
            pb_value = bvps * multiples["pb"]
            valuations.append({
                "model": "P/B Multiple",
                "value": pb_value,
                "weight": 20,
                "details": f"BVPS ${bvps:.2f} x {multiples['pb']} P/B",
            })
            total_weight += 20

    # 3. P/S Multiple (weight 20%)
    revenue = financials.get("revenue")
    if revenue and shares and shares > 0:
        rps = revenue / (shares * 1_000_000)
        if rps > 0:
            ps_value = rps * multiples["ps"]
            valuations.append({
                "model": "P/S Multiple",
                "value": ps_value,
                "weight": 20,
                "details": f"RPS ${rps:.2f} x {multiples['ps']} P/S",
            })
            total_weight += 20

    # 4. Simple DCF (weight 20%)
    fcf = financials.get("free_cash_flow")
    growth = financials.get("revenue_growth")
    if fcf and fcf > 0 and shares and shares > 0:
        growth_rate = min((growth or 5) / 100, 0.25)
        discount_rate = 0.10
        terminal_multiple = 15

        # 5-year DCF
        total_pv = 0
        projected_fcf = fcf
        for year in range(1, 6):
            projected_fcf *= (1 + growth_rate)
            pv = projected_fcf / ((1 + discount_rate) ** year)
            total_pv += pv

        terminal_value = projected_fcf * terminal_multiple
        pv_terminal = terminal_value / ((1 + discount_rate) ** 5)
        intrinsic = (total_pv + pv_terminal) / (shares * 1_000_000)

        if intrinsic > 0:
            valuations.append({
                "model": "Simple DCF",
                "value": intrinsic,
                "weight": 20,
                "details": f"FCF ${fcf / 1e6:.0f}M, {growth_rate * 100:.0f}% growth",
            })
            total_weight += 20

    # 5. EV/EBITDA (weight 15%)
    ebitda = financials.get("ebitda")
    market_cap = company_info.get("market_cap")
    total_debt = financials.get("total_debt") or 0
    cash = financials.get("cash_and_equivalents") or 0
    if ebitda and ebitda > 0 and market_cap and shares and shares > 0:
        ev = market_cap + total_debt - cash
        fair_ev = ebitda * multiples["evEbitda"]
        fair_equity = fair_ev - total_debt + cash
        ev_ebitda_value = fair_equity / (shares * 1_000_000)
        if ev_ebitda_value > 0:
            valuations.append({
                "model": "EV/EBITDA",
                "value": ev_ebitda_value,
                "weight": 15,
                "details": f"EBITDA ${ebitda / 1e6:.0f}M x {multiples['evEbitda']}",
            })
            total_weight += 15

    if not valuations:
        return None

    # Calculate weighted average
    weighted_sum = sum(v["value"] * v["weight"] for v in valuations)
    weighted_fv = weighted_sum / total_weight
    premium_discount = ((price - weighted_fv) / weighted_fv) * 100

    return {
        "models": valuations,
        "weighted_fair_value": round(weighted_fv, 2),
        "premium_discount_pct": round(premium_discount, 1),
        "total_weight": total_weight,
    }


# ------------------------------------------------------------------
# Growth Score (0-100)
# ------------------------------------------------------------------

def calculate_growth_score(financials: dict) -> int:
    """Calculate a growth quality score."""
    score = 50

    rev_growth = financials.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth > 20:
            score += 20
        elif rev_growth > 10:
            score += 10
        elif rev_growth < 0:
            score -= 10

    profit_margin = financials.get("operating_margin")
    if profit_margin is not None:
        if profit_margin > 20:
            score += 15
        elif profit_margin > 10:
            score += 8

    roe = financials.get("roe")
    if roe is not None and roe > 15:
        score += 10

    current_ratio = financials.get("current_ratio")
    if current_ratio is not None and current_ratio > 1.5:
        score += 5

    return max(0, min(100, score))


# ------------------------------------------------------------------
# Derived Valuation Metrics
# ------------------------------------------------------------------

def calculate_derived_metrics(financials: dict, price: float,
                               market_cap: float | None) -> dict:
    """Calculate FCF Yield, PEG, P/FCF, EV/EBITDA ratio.

    These are the metrics added to the HTML app's research panel.
    """
    result = {
        "fcf_yield": None,
        "peg_ratio": None,
        "price_to_fcf": None,
        "ev_ebitda": None,
    }

    fcf = financials.get("free_cash_flow")
    shares = financials.get("shares_outstanding")

    # FCF Yield = FCF per share / Price
    if fcf and shares and shares > 0 and price and price > 0:
        fcf_per_share = fcf / (shares * 1_000_000)
        result["fcf_yield"] = (fcf_per_share / price) * 100

    # PEG Ratio = (P/E) / EPS Growth Rate
    eps = financials.get("eps")
    eps_growth = financials.get("eps_growth")
    if eps and eps > 0 and eps_growth and eps_growth > 0 and price:
        pe = price / eps
        result["peg_ratio"] = pe / eps_growth

    # Price-to-FCF
    if fcf and fcf > 0 and shares and shares > 0 and price:
        fcf_per_share = fcf / (shares * 1_000_000)
        result["price_to_fcf"] = price / fcf_per_share

    # EV/EBITDA
    ebitda = financials.get("ebitda")
    total_debt = financials.get("total_debt") or 0
    cash = financials.get("cash_and_equivalents") or 0
    if market_cap and ebitda and ebitda > 0:
        ev = market_cap + total_debt - cash
        result["ev_ebitda"] = ev / ebitda

    return result


# ------------------------------------------------------------------
# Lightweight moat (market cap only, no extra API calls)
# ------------------------------------------------------------------

def calculate_lightweight_moat(company_details: dict) -> dict:
    """Quick moat estimate from market cap alone (for scan mode)."""
    market_cap = company_details.get("market_cap")
    if not market_cap:
        return {"moat_score": None, "moat_rating": None}

    if market_cap > 200e9:
        quick_score = 70
    elif market_cap > 50e9:
        quick_score = 60
    elif market_cap > 10e9:
        quick_score = 45
    else:
        quick_score = 30

    moat_rating = "No Moat"
    if quick_score >= 75:
        moat_rating = "Wide Moat"
    elif quick_score >= 55:
        moat_rating = "Narrow Moat"

    return {"moat_score": quick_score, "moat_rating": moat_rating}
