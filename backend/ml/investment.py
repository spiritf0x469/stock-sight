def calculate_investment(current_price: float, predicted_price: float, amount: float) -> dict:
    """
    Doc §3.11:
      shares     = I / P0
      future_val = shares * Ppred
      P/L        = future_val - I
      return %   = (P/L / I) * 100
    """
    if current_price <= 0:
        raise ValueError("current_price must be positive")
    if amount <= 0:
        raise ValueError("amount must be positive")

    shares = amount / current_price
    future_value = shares * predicted_price
    profit_loss = future_value - amount
    return_pct = (profit_loss / amount) * 100.0

    return {
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "shares": round(shares, 4),
        "invested": round(amount, 2),
        "future_value": round(future_value, 2),
        "profit_loss": round(profit_loss, 2),
        "return_pct": round(return_pct, 2),
    }


def decide(return_pct: float) -> dict:
    """
    Doc §3.12 — simplified rule-based decision support.
    Thresholds are implementation-defined.
    """
    if return_pct >= 5.0:
        label = "BUY"
        reason = f"Expected return of {return_pct:.2f}% is strongly positive."
    elif return_pct >= 0.0:
        label = "HOLD"
        reason = f"Expected return of {return_pct:.2f}% is slightly positive — hold and watch."
    else:
        label = "AVOID"
        reason = f"Expected return of {return_pct:.2f}% is negative — avoid this horizon."
    return {"action": label, "reason": reason}