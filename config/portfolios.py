"""Predefined portfolio definitions — user's actual holdings."""

PREDEFINED_PORTFOLIOS = {
    "robinhood": {
        "id": "robinhood",
        "name": "Robinhood Portfolio",
        "description": "Personal Robinhood holdings",
        "symbols": [
            "GNSS", "SMCI", "HOOD", "NVDA", "RGTI", "AUR", "TSLA", "SMR",
            "OKLO", "HSAI", "CRCL", "INVZ", "GOOGL", "NVTS", "FLNC", "BLSH",
            "RR", "GEMI", "HOWL", "APLD", "CYCU", "ACET",
        ],
        "holdings": {},  # User can add cost basis via UI
    },
    "401k": {
        "id": "401k",
        "name": "401K Portfolio",
        "description": "Retirement account holdings",
        "symbols": [
            "BE", "RKLB", "ASM", "CIFR", "VRT", "TSM", "SOFI", "NVDA",
            "SIL", "QBTS", "FMC", "IREN", "SKYT", "TLN", "PJP", "ALLT",
            "LPTH", "DAVE", "AUR", "SMCI", "IONQ", "BBAI", "USAS",
        ],
        "holdings": {},
    },
    "current-stocks": {
        "id": "current-stocks",
        "name": "Current Stocks",
        "description": "Current active holdings",
        "symbols": [
            "ABSI", "CRNC", "NVTS", "PDYN", "BKSY", "SES", "INOD", "RKLB",
            "IONQ", "QBTS", "RGTI", "KALU", "TTMI", "WLDN", "CMCL", "BE",
            "HL", "SA", "TSM", "WCC", "STX", "KGC", "NVDA", "IREN", "MU",
            "DLR", "CIFR", "LRCX", "VRT", "COHR", "SYM", "CRWV", "BWX",
            "OKLO", "CCJ",
        ],
        "holdings": {},
    },
}

# Default custom portfolios (empty, created for new users)
DEFAULT_CUSTOM_PORTFOLIOS = {
    "watchlist": {
        "id": "watchlist",
        "name": "Watchlist",
        "description": "Stocks to watch",
        "symbols": [],
        "holdings": {},
    },
    "government-plays": {
        "id": "government-plays",
        "name": "Government Policy Plays",
        "description": "Stocks aligned with government policy themes",
        "symbols": [],
        "holdings": {},
    },
    "high-growth": {
        "id": "high-growth",
        "name": "High Growth Candidates",
        "description": "High-growth potential stocks",
        "symbols": [],
        "holdings": {},
    },
}
