max_percentage = 99
min_percentage = 55

def clamp_value(val, lower=min_percentage, upper=max_percentage):
    """Clamp a final score into [55, 99]."""
    return max(lower, min(upper, val))

def clamp_ratio(ratio, lower=0.5, upper=2.0):
    """Clamp a ratio into [0.5, 2.0]."""
    return max(lower, min(upper, ratio))

def linear_transform(ratio):
    """
    Transform a ratio in [0.5, 2.0] to a score in [55, 99].
      ratio=0.5 => 55
      ratio=1.0 => ~77
      ratio=2.0 => 99
    """
    slope = 44 / 1.5  # ~29.33
    intercept = 77 - slope
    return intercept + slope * ratio

def get_ratio(origin_val, destination_val, higher_is_better=True):
    """
    Returns a ratio that is >1 if the destination is 'better' based on direction:
      - If higher_is_better=True:  ratio = (destination_val / origin_val)
      - If higher_is_better=False: ratio = (origin_val / destination_val)

    Then clamps it to [0.5, 2.0].
    """
    if origin_val == 0 and destination_val == 0:
        return 1.0
    if origin_val == 0:
        return 2.0
    if destination_val == 0:
        return 0.5

    if higher_is_better:
        ratio = destination_val / origin_val
    else:
        ratio = origin_val / destination_val

    return clamp_ratio(ratio)

def compute_category_score(origin, destination, fields_config):
    """
    Given a list of dicts describing the fields for one category, compute:
      1) The ratio for each field (considering higher_is_better or not).
      2) Average the ratios.
      3) Convert that average ratio to a [55..99] score via linear_transform + clamp.
    """
    ratios = []
    for field_info in fields_config:
        field_name = field_info['field']
        higher_is_better = field_info['higher_is_better']

        orig_val = origin[field_name]
        dest_val = destination[field_name]

        ratio = get_ratio(orig_val, dest_val, higher_is_better)
        ratios.append(ratio)

    avg_ratio = sum(ratios) / len(ratios)
    score = linear_transform(avg_ratio)
    return clamp_value(score)

def get_city_score(origin, destination):
    """
    Compare two cities using straightforward average-of-ratios logic for
    each category, then produce an overall city score.
    """

    category_configs = {
        "housing_availability": [
            {"field": "home_price",                "higher_is_better": False},
            {"field": "property_tax",              "higher_is_better": False},
            {"field": "home_appreciation_rate",    "higher_is_better": True},
            {"field": "price_per_square_foot",     "higher_is_better": False},
        ],
        "quality_of_life": [
            {"field": "education",             "higher_is_better": True},
            {"field": "healthcare_fitness",    "higher_is_better": True},
            {"field": "weather_grade",         "higher_is_better": True},
            {"field": "air_quality_index",     "higher_is_better": True},
            {"field": "commute_transit_score", "higher_is_better": True},
            {"field": "accessibility",         "higher_is_better": True},
            {"field": "culture_entertainment", "higher_is_better": True},
        ],
        "job_market_strength": [
            {"field": "unemployment_rate",       "higher_is_better": False},
            {"field": "recent_job_growth",       "higher_is_better": True},
            {"field": "future_job_growth_index", "higher_is_better": True},
            {"field": "median_household_income", "higher_is_better": True},
        ],
        "living_affordability": [
            {"field": "state_income_tax",    "higher_is_better": False},
            {"field": "utilities",           "higher_is_better": False},
            {"field": "food_groceries",      "higher_is_better": False},
            {"field": "sales_tax",           "higher_is_better": False},
            {"field": "transportation_cost", "higher_is_better": False},
        ],
    }

    housing_score = compute_category_score(origin, destination, category_configs["housing_availability"])
    qol_score = compute_category_score(origin, destination, category_configs["quality_of_life"])
    job_score = compute_category_score(origin, destination, category_configs["job_market_strength"])
    living_score = compute_category_score(origin, destination, category_configs["living_affordability"])

    overall_city_score = (
        housing_score + qol_score + job_score + living_score
    ) / 4.0
    overall_city_score = clamp_value(overall_city_score)

    return {
        "housing_affordability":  round(housing_score, 2),
        "quality_of_life":        round(qol_score, 2),
        "job_market_strength":    round(job_score, 2),
        "living_affordability":   round(living_score, 2),
        "overall_city_score":     round(overall_city_score, 2),
    }
