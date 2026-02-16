"""Government investment themes, sector ETF mappings, and theme stock lists."""

# Government spending themes for opportunity identification
GOVERNMENT_THEMES = {
    "ai_semiconductor": {
        "name": "AI & Semiconductor",
        "symbols": ["NVDA", "AMD", "INTC", "AVGO", "MRVL", "TSM", "QCOM", "AMAT", "LRCX", "KLAC"],
        "searchTerms": ["artificial intelligence", "semiconductor", "microchip"],
        "naicsCodes": ["334413", "334418", "511210"],
        "federalRegisterTerms": ["artificial intelligence", "semiconductor", "CHIPS Act"],
    },
    "clean_energy": {
        "name": "Clean Energy & EV",
        "symbols": ["ENPH", "SEDG", "FSLR", "RUN", "PLUG", "BE", "TSLA", "RIVN", "LCID", "QS"],
        "searchTerms": ["clean energy", "solar", "electric vehicle"],
        "naicsCodes": ["221114", "335911", "336111"],
        "federalRegisterTerms": ["renewable energy", "electric vehicle", "clean energy"],
    },
    "infrastructure": {
        "name": "Infrastructure & Construction",
        "symbols": ["CAT", "DE", "VMC", "MLM", "URI", "PWR", "FAST", "SWK", "GWW", "EMR"],
        "searchTerms": ["infrastructure", "construction", "highway"],
        "naicsCodes": ["237310", "237110", "236220"],
        "federalRegisterTerms": ["infrastructure", "transportation", "construction"],
    },
    "defense": {
        "name": "Defense & Aerospace",
        "symbols": ["LMT", "RTX", "NOC", "GD", "BA", "LHX", "HII", "TDG", "HWM", "AXON"],
        "searchTerms": ["defense", "military", "aerospace"],
        "naicsCodes": ["336411", "336414", "334511"],
        "federalRegisterTerms": ["defense", "military", "national security"],
    },
    "biotech": {
        "name": "Biotech & Pharma",
        "symbols": ["MRNA", "BNTX", "REGN", "VRTX", "GILD", "BIIB", "ILMN", "EXAS", "DXCM", "ISRG"],
        "searchTerms": ["biotechnology", "pharmaceutical", "drug development"],
        "naicsCodes": ["325414", "325411", "339112"],
        "federalRegisterTerms": ["FDA", "drug approval", "biotechnology"],
    },
    "cybersecurity": {
        "name": "Cybersecurity",
        "symbols": ["CRWD", "PANW", "ZS", "FTNT", "NET", "S", "CYBR", "OKTA", "TENB", "RPD"],
        "searchTerms": ["cybersecurity", "network security", "information security"],
        "naicsCodes": ["511210", "541512"],
        "federalRegisterTerms": ["cybersecurity", "data protection", "critical infrastructure"],
    },
    "cloud_saas": {
        "name": "Cloud & SaaS",
        "symbols": ["CRM", "NOW", "SNOW", "DDOG", "MDB", "PLTR", "VEEV", "ZM", "TWLO", "HUBS"],
        "searchTerms": ["cloud computing", "software as a service"],
        "naicsCodes": ["518210", "511210"],
        "federalRegisterTerms": ["cloud computing", "FedRAMP", "government cloud"],
    },
    "quantum_computing": {
        "name": "Quantum Computing",
        "symbols": ["IBM", "GOOGL", "IONQ", "RGTI", "QBTS", "HON"],
        "searchTerms": ["quantum computing", "quantum technology"],
        "naicsCodes": ["334118", "511210"],
        "federalRegisterTerms": ["quantum computing", "quantum technology"],
    },
}

# Investment theme groups for scanner filtering
INVESTMENT_THEMES = {
    "Mega Cap Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
    "AI & Chips": GOVERNMENT_THEMES["ai_semiconductor"]["symbols"],
    "Cybersecurity": GOVERNMENT_THEMES["cybersecurity"]["symbols"],
    "Clean Energy": GOVERNMENT_THEMES["clean_energy"]["symbols"],
    "Defense": GOVERNMENT_THEMES["defense"]["symbols"],
    "Biotech": GOVERNMENT_THEMES["biotech"]["symbols"],
    "Cloud/SaaS": GOVERNMENT_THEMES["cloud_saas"]["symbols"],
    "Infrastructure": GOVERNMENT_THEMES["infrastructure"]["symbols"],
}

# Re-export sector watchlists and filter presets for convenience
from config.watchlists import SECTOR_WATCHLISTS, FILTER_PRESETS, SECTOR_ETF_MAP, SECTOR_NAMES  # noqa: E402, F401

# Combined themes: investment themes + sector watchlists
ALL_THEME_NAMES = list(INVESTMENT_THEMES.keys()) + [
    v["name"] for v in SECTOR_WATCHLISTS.values()
]
