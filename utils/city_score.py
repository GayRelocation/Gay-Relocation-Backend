import re

max_percentage = 99
min_percentage = 55


def parse_price(price_str):
    """Parse price strings like '$1.5M' into numerical values."""
    multipliers = {'K': 1e3, 'M': 1e6, 'B': 1e9,
                   'T': 1e12, 'k': 1e3, 'm': 1e6, 'b': 1e9, 't': 1e12}
    price_str = price_str.replace('$', '').replace(',', '').replace(' ', '')
    match = re.match(r'^(\d+(\.\d+)?)([KMBT]?)$', price_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid price format: {price_str}")
    number, _, suffix = match.groups()
    multiplier = multipliers.get(suffix.upper(), 1)
    return float(number) * multiplier


def parse_percentage(percent_str):
    """Parse percentage strings like '10%' into a numerical value (e.g., 10.0)."""
    return float(percent_str.replace('%', ''))


def clamp_value(val, lower=min_percentage, upper=max_percentage):
    """Clamp a final score into [55, 99]."""
    return max(lower, min(upper, val))


def clamp_ratio(ratio, lower=0.5, upper=2.0):
    """Clamp a ratio into [0.5, 2.0]."""
    return max(lower, min(upper, ratio))


def linear_transform(ratio):
    """
    Transform a ratio in [0.5, 2.0] to a score in [55, 99].
    For ratio=1 => ~77 (a neutral midpoint).
    """
    # Solve a simple linear mapping:
    #   ratio=0.5 => 55
    #   ratio=2.0 => 99
    #   ratio=1.0 => ~77
    # Slope = (99 - 55) / (2.0 - 0.5) = 44 / 1.5 = ~29.33
    # Intercept (for ratio=1 => ~77) => intercept = 77 - slope*1
    slope = 44 / 1.5   # ~29.33
    intercept = 77 - slope
    return intercept + slope * ratio


def get_ratio(origin_val, destination_val, higher_is_better=True):
    """
    Returns a ratio that is >1 if the destination is 'better' based on direction:
      - If higher_is_better=True, ratio = destination_val / origin_val
      - Otherwise, ratio = origin_val / destination_val
    Then clamps it to [0.5, 2.0].
    """
    # Avoid division by zero:
    if origin_val == 0 and destination_val == 0:
        return 1.0
    if origin_val == 0:
        return 2.0  # effectively push the ratio to upper bound
    if destination_val == 0:
        return 0.5  # effectively push the ratio to lower bound

    if higher_is_better:
        ratio = destination_val / origin_val
    else:
        ratio = origin_val / destination_val

    return clamp_ratio(ratio)


def get_city_score(origin, destination):
    """
    Compare two cities (city_data["origin"], city_data["destination"]) using
    ratio-based calculations to produce final scores in the 55–99 range for:
       - housing_affordability
       - quality_of_life
       - job_market_strength
       - living_affordability
       - overall_city_score

    Returns a dictionary with these five keys, each in [55..99].
    The idea is: If 'destination' is overall better, the final
    scores will shift higher; if worse, the scores will shift lower.
    """

    # ---------------------------
    # 1) Housing Affordability
    #    lower home_price => 'better'
    #    higher median_income => 'better'
    #    We combine them in a single ratio or do separate steps.
    #
    #    Example approach:
    #      ratio_home_prices = origin_price / destination_price  (lower is better)
    #      ratio_incomes     = destination_income / origin_income (higher is better)
    #    Then multiply or average them. (Here we multiply to get a single ratio.)
    # ---------------------------
    origin_price = parse_price(origin["home_price"])
    dest_price = parse_price(destination["home_price"])

    origin_income = parse_price(origin["median_household_income"])
    dest_income = parse_price(destination["median_household_income"])

    ratio_home_prices = get_ratio(
        origin_price, dest_price, higher_is_better=False)
    ratio_incomes = get_ratio(
        origin_income, dest_income, higher_is_better=True)

    combined_housing_ratio = ratio_home_prices * ratio_incomes
    # Clamp final ratio again if needed:
    combined_housing_ratio = clamp_ratio(combined_housing_ratio, 0.5, 2.0)
    housing_affordability_score = clamp_value(
        linear_transform(combined_housing_ratio))

    # ---------------------------
    # 2) Quality of Life
    #    Suppose "higher is better" for these metrics:
    #    education, healthcare_fitness, weather_grade, air_quality_index,
    #    commute_transit_score, accessibility, culture_entertainment
    # ---------------------------
    qol_fields = [
        "education",
        "healthcare_fitness",
        "weather_grade",
        "air_quality_index",
        "commute_transit_score",
        "accessibility",
        "culture_entertainment"
    ]
    ratios_qol = []
    for field in qol_fields:
        orig_val = float(origin[field])
        dest_val = float(destination[field])
        ratio_field = get_ratio(orig_val, dest_val, higher_is_better=True)
        ratios_qol.append(ratio_field)

    # average all ratios, then transform
    avg_qol_ratio = sum(ratios_qol) / len(ratios_qol)
    quality_of_life_score = clamp_value(linear_transform(avg_qol_ratio))

    # ---------------------------
    # 3) Job Market Strength
    #    lower unemployment => better
    #    higher recent_job_growth => better
    #    higher future_job_growth_index => better
    # ---------------------------
    origin_unemp = parse_percentage(origin["unemployment_rate"])
    dest_unemp = parse_percentage(destination["unemployment_rate"])
    ratio_unemp = get_ratio(origin_unemp, dest_unemp, higher_is_better=False)

    origin_recent = parse_percentage(origin["recent_job_growth"])
    dest_recent = parse_percentage(destination["recent_job_growth"])
    ratio_recent = get_ratio(origin_recent, dest_recent, higher_is_better=True)

    origin_future = float(origin["future_job_growth_index"])
    dest_future = float(destination["future_job_growth_index"])
    ratio_future = get_ratio(origin_future, dest_future, higher_is_better=True)

    # Weight them for an overall ratio
    # e.g.: 40% unemployment, 20% recent, 40% future
    job_ratio = (
        ratio_unemp * 0.4 +
        ratio_recent * 0.2 +
        ratio_future * 0.4
    )
    # Might want to treat that as a direct ratio or average.
    # If we want an average ratio, we could do job_ratio / sum_of_weights
    # but let's just treat it as a combined "ratio scale."
    # We'll do a simple normalization:
    # sum_of_weights = 1.0
    # job_ratio is already effectively "weighted average"
    # clamp and transform
    job_ratio = clamp_ratio(job_ratio, 0.5, 2.0)
    job_market_strength_score = clamp_value(linear_transform(job_ratio))

    # ---------------------------
    # 4) Living Affordability
    #    lower costs => better
    #    lower taxes => better
    # ---------------------------
    origin_costs = [
        float(origin["utilities"]),
        float(origin["food_groceries"]),
        float(origin["transportation_cost"])
    ]
    dest_costs = [
        float(destination["utilities"]),
        float(destination["food_groceries"]),
        float(destination["transportation_cost"])
    ]
    origin_cost_avg = sum(origin_costs) / len(origin_costs)
    dest_cost_avg = sum(dest_costs) / len(dest_costs)
    ratio_costs = get_ratio(
        origin_cost_avg, dest_cost_avg, higher_is_better=False)

    origin_taxes = [
        parse_percentage(origin["sales_tax"]),
        parse_percentage(origin["state_income_tax"]),
        parse_percentage(origin["property_tax"])
    ]
    dest_taxes = [
        parse_percentage(destination["sales_tax"]),
        parse_percentage(destination["state_income_tax"]),
        parse_percentage(destination["property_tax"])
    ]
    origin_tax_avg = sum(origin_taxes) / len(origin_taxes)
    dest_tax_avg = sum(dest_taxes) / len(dest_taxes)
    ratio_taxes = get_ratio(
        origin_tax_avg, dest_tax_avg, higher_is_better=False)

    # Weighted ratio for living affordability
    # e.g. 70% cost, 30% taxes
    living_ratio = (ratio_costs * 0.7 + ratio_taxes * 0.3)
    living_ratio = clamp_ratio(living_ratio, 0.5, 2.0)
    living_affordability_score = clamp_value(linear_transform(living_ratio))

    # ---------------------------
    # 5) Overall City Score
    #    We can just average the 4 sub-scores:
    # ---------------------------
    overall_city_score = (
        housing_affordability_score
        + quality_of_life_score
        + job_market_strength_score
        + living_affordability_score
    ) / 4.0
    overall_city_score = clamp_value(overall_city_score)

    return {
        "housing_affordability": round(housing_affordability_score, 2),
        "quality_of_life": round(quality_of_life_score, 2),
        "job_market_strength": round(job_market_strength_score, 2),
        "living_affordability": round(living_affordability_score, 2),
        "overall_city_score": round(overall_city_score, 2),
    }
