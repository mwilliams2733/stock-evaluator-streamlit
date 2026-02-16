"""Sector watchlists and scanner filter presets."""

SECTOR_WATCHLISTS = {
    "ai-datacenter": {
        "name": "AI & Data Center Power",
        "description": "AI chips, data center infrastructure, and power utilities",
        "symbols": [
            "NVDA", "AMD", "AVGO", "MRVL", "ARM", "INTC", "QCOM", "MU",
            "SMCI", "DELL", "HPE", "ANET", "CSCO", "JNPR", "NTAP", "PSTG",
            "AMZN", "MSFT", "GOOGL", "META", "ORCL", "CRM", "NOW",
            "EQIX", "DLR", "AMT", "CCI",
            "VRT", "ETN", "POWL", "GEV", "APH", "GLW",
            "VST", "CEG", "NRG", "TLN", "OKLO", "SMR", "NNE",
            "TT", "LII", "CARR", "JCI",
            "ROK", "EMR", "AME", "HUBB", "AOS",
            "PLTR", "AI", "PATH", "SNOW", "DDOG", "MDB", "NET",
        ],
    },
    "semiconductors": {
        "name": "Semiconductors",
        "description": "Chip makers and semiconductor equipment",
        "symbols": [
            "NVDA", "AMD", "AVGO", "QCOM", "TXN", "ADI", "MRVL", "NXPI",
            "ON", "MCHP", "SWKS", "QRVO", "MPWR", "LSCC", "SLAB",
            "ASML", "AMAT", "LRCX", "KLAC", "TER", "ENTG", "MKSI",
        ],
    },
    "mag7": {
        "name": "Magnificent 7",
        "description": "Mega-cap tech leaders",
        "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    },
    "fintech": {
        "name": "Fintech & Payments",
        "description": "Payment processors and financial technology",
        "symbols": [
            "V", "MA", "PYPL", "SQ", "COIN", "AFRM", "SOFI", "HOOD",
            "FIS", "FISV", "GPN", "ADP", "INTU", "BILL",
        ],
    },
    "biotech": {
        "name": "Biotech & Pharma",
        "description": "Biotechnology and pharmaceutical companies",
        "symbols": [
            "LLY", "NVO", "ABBV", "MRK", "PFE", "BMY", "AMGN", "GILD",
            "REGN", "VRTX", "BIIB", "MRNA", "ISRG", "TMO", "DHR",
        ],
    },
    "smallcap-momentum": {
        "name": "Small-Cap Momentum",
        "description": "High-volatility small caps with breakout potential",
        "symbols": [
            "EKSO", "FONR", "ONTF", "MBOT", "APVO", "CAPR", "MYO",
            "KTOS", "RKLB", "ASTS", "LUNR", "RDW", "SPCE",
            "JOBY", "ACHR", "LILM", "EVTL", "BLDE",
            "IONQ", "RGTI", "QUBT", "QBTS", "ARQQ",
        ],
    },
    "ma-targets": {
        "name": "M&A Target Profile",
        "description": "Small-caps with acquisition target characteristics",
        "symbols": [
            "EKSO", "FONR", "ONTF", "MBOT", "STXS", "ANGO", "ATRC",
            "PRAX", "RARE", "CORT", "FULC", "ARDX", "RETA",
            "SPNS", "CXM", "PRFT", "FRSH", "BRZE",
        ],
    },
    "healthcare-gov": {
        "name": "Healthcare (Gov Aligned)",
        "description": "Healthcare companies with government contract exposure",
        "symbols": [
            "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "TMO", "ISRG",
            "MOH", "CNC", "HUM",
        ],
    },
    "infrastructure": {
        "name": "Infrastructure & Construction",
        "description": "Infrastructure, construction, and heavy equipment companies",
        "symbols": [
            "CAT", "DE", "URI", "VMC", "MLM", "PWR", "EME",
            "STRL", "GVA", "PRIM", "ACM",
        ],
    },
    "reshoring": {
        "name": "Reshoring & Manufacturing",
        "description": "Domestic manufacturing, industrial automation, and reshoring beneficiaries",
        "symbols": [
            "GE", "HON", "MMM", "EMR", "ROK", "FAST", "SWK",
            "PH", "DOV", "ITW", "CMI",
        ],
    },
}


# Sector ETF mapping — maps individual tickers to their sector ETF
SECTOR_ETF_MAP = {
    # Technology
    "AAPL": "XLK", "MSFT": "XLK", "GOOGL": "XLK", "GOOG": "XLK", "META": "XLK", "NVDA": "XLK",
    "AVGO": "XLK", "ORCL": "XLK", "CRM": "XLK", "ADBE": "XLK", "CSCO": "XLK", "ACN": "XLK",
    "IBM": "XLK", "INTC": "XLK", "AMD": "XLK", "QCOM": "XLK", "TXN": "XLK", "AMAT": "XLK",
    "MRVL": "XLK", "ARM": "XLK", "MU": "XLK", "ADI": "XLK", "NXPI": "XLK", "LRCX": "XLK",
    "KLAC": "XLK", "ASML": "XLK", "MPWR": "XLK", "MCHP": "XLK", "ON": "XLK", "SWKS": "XLK",
    "QRVO": "XLK", "TER": "XLK", "ENTG": "XLK", "MKSI": "XLK", "LSCC": "XLK", "SLAB": "XLK",
    "TSM": "XLK", "NOW": "XLK", "SNOW": "XLK", "DDOG": "XLK", "MDB": "XLK", "NET": "XLK",
    "PLTR": "XLK", "AI": "XLK", "PATH": "XLK", "SMCI": "XLK", "DELL": "XLK", "HPE": "XLK",
    "ANET": "XLK", "JNPR": "XLK", "NTAP": "XLK", "PSTG": "XLK", "GLW": "XLK", "APH": "XLK",
    "IONQ": "XLK", "RGTI": "XLK", "QUBT": "XLK", "QBTS": "XLK", "ARQQ": "XLK",
    "BBAI": "XLK", "APLD": "XLK", "CIFR": "XLK", "IREN": "XLK",
    # Communication Services
    "NFLX": "XLC", "DIS": "XLC", "CMCSA": "XLC", "VZ": "XLC", "T": "XLC", "TMUS": "XLC",
    # Consumer Discretionary
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "MCD": "XLY", "NKE": "XLY", "SBUX": "XLY",
    "LOW": "XLY", "TJX": "XLY", "BKNG": "XLY", "CMG": "XLY",
    # Consumer Staples
    "PG": "XLP", "KO": "XLP", "PEP": "XLP", "COST": "XLP", "WMT": "XLP", "PM": "XLP",
    "MO": "XLP", "CL": "XLP", "MDLZ": "XLP", "KHC": "XLP",
    # Health Care
    "UNH": "XLV", "JNJ": "XLV", "LLY": "XLV", "PFE": "XLV", "ABBV": "XLV", "MRK": "XLV",
    "TMO": "XLV", "ABT": "XLV", "DHR": "XLV", "BMY": "XLV", "AMGN": "XLV", "GILD": "XLV",
    "REGN": "XLV", "VRTX": "XLV", "BIIB": "XLV", "MRNA": "XLV", "ISRG": "XLV",
    "MOH": "XLV", "CNC": "XLV", "HUM": "XLV", "NVO": "XLV",
    # Financials
    "JPM": "XLF", "V": "XLF", "MA": "XLF", "BAC": "XLF", "WFC": "XLF",
    "GS": "XLF", "MS": "XLF", "AXP": "XLF", "C": "XLF", "BLK": "XLF", "SCHW": "XLF",
    "PYPL": "XLF", "SQ": "XLF", "COIN": "XLF", "AFRM": "XLF", "SOFI": "XLF", "HOOD": "XLF",
    "FIS": "XLF", "FISV": "XLF", "GPN": "XLF", "ADP": "XLF", "INTU": "XLF", "BILL": "XLF",
    "DAVE": "XLF",
    # Industrials
    "CAT": "XLI", "BA": "XLI", "HON": "XLI", "UPS": "XLI", "RTX": "XLI", "GE": "XLI",
    "LMT": "XLI", "DE": "XLI", "MMM": "XLI", "UNP": "XLI", "NOC": "XLI", "GD": "XLI",
    "LHX": "XLI", "HII": "XLI", "KTOS": "XLI", "URI": "XLI", "PWR": "XLI", "EME": "XLI",
    "EMR": "XLI", "ROK": "XLI", "PH": "XLI", "DOV": "XLI", "ITW": "XLI", "CMI": "XLI",
    "FAST": "XLI", "SWK": "XLI", "AME": "XLI", "HUBB": "XLI", "AOS": "XLI",
    "STRL": "XLI", "GVA": "XLI", "PRIM": "XLI", "ACM": "XLI",
    "RKLB": "XLI", "ASTS": "XLI", "LUNR": "XLI", "RDW": "XLI", "SPCE": "XLI",
    "JOBY": "XLI", "ACHR": "XLI", "LILM": "XLI", "EVTL": "XLI", "BLDE": "XLI",
    "TT": "XLI", "LII": "XLI", "CARR": "XLI", "JCI": "XLI",
    # Energy
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE", "SLB": "XLE", "EOG": "XLE", "MPC": "XLE",
    "PXD": "XLE", "VLO": "XLE", "PSX": "XLE", "OXY": "XLE",
    # Materials
    "LIN": "XLB", "APD": "XLB", "SHW": "XLB", "ECL": "XLB", "NEM": "XLB", "FCX": "XLB",
    "DD": "XLB", "NUE": "XLB", "DOW": "XLB", "VMC": "XLB", "MLM": "XLB", "FMC": "XLB",
    # Real Estate
    "AMT": "XLRE", "PLD": "XLRE", "CCI": "XLRE", "EQIX": "XLRE", "SPG": "XLRE", "O": "XLRE",
    "DLR": "XLRE",
    # Utilities
    "NEE": "XLU", "DUK": "XLU", "SO": "XLU", "D": "XLU", "AEP": "XLU", "EXC": "XLU",
    "CEG": "XLU", "VST": "XLU", "NRG": "XLU", "TLN": "XLU", "ETN": "XLU", "POWL": "XLU",
    "GEV": "XLU", "VRT": "XLU", "OKLO": "XLU", "SMR": "XLU", "NNE": "XLU",
    "BE": "XLU", "FLNC": "XLU",
}

SECTOR_NAMES = {
    "XLK": "Technology",
    "XLC": "Communication",
    "XLY": "Cons. Discretionary",
    "XLP": "Cons. Staples",
    "XLV": "Healthcare",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLE": "Energy",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
    "SPY": "Market",
}


# Scanner filter presets — one-click configurations
FILTER_PRESETS = {
    "aggressive_growth": {
        "name": "Aggressive Growth",
        "description": "Small-caps, high risk",
        "min_price": 5,
        "max_price": 50,
        "min_volume": 500_000,
        "min_score": 50,
        "min_ema_score": 60,
    },
    "quality_flow": {
        "name": "Quality + Flow",
        "description": "Established + institutions",
        "min_price": 20,
        "max_price": 200,
        "min_volume": 1_000_000,
        "min_score": 65,
        "min_ema_score": 70,
    },
    "smart_money": {
        "name": "Smart Money",
        "description": "Institutional accumulation",
        "min_price": 15,
        "max_price": 300,
        "min_volume": 750_000,
        "min_score": 55,
        "min_ema_score": 65,
    },
    "options_focus": {
        "name": "Options Focus",
        "description": "High liquidity",
        "min_price": 30,
        "max_price": 200,
        "min_volume": 2_000_000,
        "min_score": 70,
        "min_ema_score": 70,
    },
    "ma_targets": {
        "name": "M&A Targets",
        "description": "Acquisition candidates",
        "min_price": 1,
        "max_price": 20,
        "min_volume": 200_000,
        "min_score": 35,
        "min_ema_score": 40,
    },
}
