def implied_probability_from_decimal(decimal_odds: float) -> float:
    return 1.0 / decimal_odds if decimal_odds > 0 else 0.0


def expected_value(prob_win: float, decimal_odds: float) -> float:
    return prob_win * (decimal_odds - 1.0) - (1.0 - prob_win)


def fair_decimal_odds(prob_win: float) -> float:
    return (1.0 / prob_win) if prob_win > 0 else 0.0


def kelly_fraction(prob_win: float, decimal_odds: float) -> float:
    b = decimal_odds - 1.0
    q = 1.0 - prob_win
    if b <= 0:
        return 0.0
    f = ((b * prob_win) - q) / b
    return max(0.0, f)
