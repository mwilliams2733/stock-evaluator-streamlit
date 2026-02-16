"""Export utilities — CSV and PDF report generation."""

import csv
import io
import datetime as dt

import pandas as pd


def export_portfolio_csv(holdings_data: list[dict]) -> str:
    """Export portfolio holdings to CSV string.

    Args:
        holdings_data: List of dicts with ticker, name, price, shares, cost_basis,
                       pnl, pnl_pct, score, ema_score, recommendation, win_probability.

    Returns:
        CSV string.
    """
    if not holdings_data:
        return ""

    output = io.StringIO()
    fieldnames = [
        "ticker", "name", "price", "shares", "cost_basis", "current_value",
        "pnl", "pnl_pct", "score", "ema_score", "recommendation", "win_probability",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for row in holdings_data:
        clean_row = {}
        for key in fieldnames:
            val = row.get(key, "")
            if isinstance(val, float):
                clean_row[key] = f"{val:.2f}"
            else:
                clean_row[key] = val
        writer.writerow(clean_row)

    return output.getvalue()


def export_scan_csv(scan_df: pd.DataFrame) -> str:
    """Export scan results to CSV.

    Args:
        scan_df: DataFrame from scanner.

    Returns:
        CSV string.
    """
    if scan_df is None or scan_df.empty:
        return ""
    return scan_df.to_csv(index=False)


def export_portfolio_report_text(
    portfolio_name: str,
    holdings_data: list[dict],
    summary: dict | None = None,
) -> str:
    """Generate a text-based portfolio report (lightweight alternative to PDF).

    Args:
        portfolio_name: Name of the portfolio.
        holdings_data: List of holding dicts.
        summary: Optional summary dict with total_value, total_pnl, etc.

    Returns:
        Formatted text report string.
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"  PORTFOLIO REPORT: {portfolio_name}")
    lines.append(f"  Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 70)
    lines.append("")

    if summary:
        lines.append("SUMMARY")
        lines.append("-" * 40)
        if "total_value" in summary:
            lines.append(f"  Total Value:     ${summary['total_value']:,.2f}")
        if "total_pnl" in summary:
            lines.append(f"  Total P&L:       ${summary['total_pnl']:,.2f}")
        if "total_pnl_pct" in summary:
            lines.append(f"  Total P&L %:     {summary['total_pnl_pct']:.1f}%")
        if "num_stocks" in summary:
            lines.append(f"  Holdings:        {summary['num_stocks']}")
        if "avg_score" in summary:
            lines.append(f"  Avg Score:       {summary['avg_score']:.0f}")
        lines.append("")

    lines.append("HOLDINGS")
    lines.append("-" * 70)
    header = f"{'Ticker':<8} {'Price':>10} {'Shares':>8} {'P&L':>10} {'P&L%':>8} {'Score':>6} {'Action':<15}"
    lines.append(header)
    lines.append("-" * 70)

    for h in holdings_data:
        ticker = h.get("ticker", "")[:8]
        price = h.get("price", 0)
        shares = h.get("shares", 0)
        pnl = h.get("pnl", 0)
        pnl_pct = h.get("pnl_pct", 0)
        score = h.get("score", 0)
        action = h.get("recommendation", "")[:15]

        line = f"{ticker:<8} ${price:>9.2f} {shares:>8.1f} ${pnl:>9.2f} {pnl_pct:>7.1f}% {score:>5.0f}  {action:<15}"
        lines.append(line)

    lines.append("-" * 70)
    lines.append("")
    lines.append("Note: This report is for informational purposes only.")
    lines.append("Dynamic Momentum Screener — https://github.com/mwilliams2733/stock-evaluator-streamlit")

    return "\n".join(lines)


def export_backtest_report_text(
    summary: dict,
    factor_analysis: dict,
    action_breakdown: dict,
) -> str:
    """Generate a text-based backtest report.

    Args:
        summary: Backtest summary dict.
        factor_analysis: Factor correlation data.
        action_breakdown: Win rates by action.

    Returns:
        Formatted text report string.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("  BACKTEST REPORT")
    lines.append(f"  Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("OVERALL RESULTS")
    lines.append("-" * 40)
    lines.append(f"  Total Trades:    {summary.get('total_trades', 0)}")
    lines.append(f"  Win Rate:        {summary.get('win_rate', 0):.1f}%")
    lines.append(f"  Avg Return:      {summary.get('avg_return', 0):.1f}%")
    lines.append(f"  Profit Factor:   {summary.get('profit_factor', 0):.2f}")
    lines.append(f"  Best Trade:      {summary.get('best_trade', 0):+.1f}%")
    lines.append(f"  Worst Trade:     {summary.get('worst_trade', 0):+.1f}%")
    lines.append(f"  Avg Days Held:   {summary.get('avg_days_held', 0):.0f}")
    lines.append("")

    if action_breakdown:
        lines.append("RESULTS BY ACTION")
        lines.append("-" * 50)
        header = f"{'Action':<18} {'Trades':>6} {'Wins':>6} {'WinRate':>8} {'AvgRet':>8}"
        lines.append(header)
        lines.append("-" * 50)
        for action, data in sorted(action_breakdown.items()):
            line = (
                f"{action:<18} {data.get('total', 0):>6} {data.get('wins', 0):>6} "
                f"{data.get('win_rate', 0):>7.1f}% {data.get('avg_return', 0):>7.1f}%"
            )
            lines.append(line)
        lines.append("")

    if factor_analysis:
        lines.append("FACTOR ANALYSIS (Avg in Wins vs Losses)")
        lines.append("-" * 50)
        for factor, data in factor_analysis.items():
            lines.append(
                f"  {factor}: Win={data['avg_in_wins']:.1f} "
                f"Loss={data['avg_in_losses']:.1f} "
                f"Diff={data['differential']:+.1f}"
            )

    return "\n".join(lines)
