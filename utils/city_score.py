
max_percentage = 95
min_percentage = 5


def parse_price(price_str):
    """Parse price strings like '$100K' into numerical values."""
    price_str = price_str.replace('$', '').replace(
        ',', '').replace('K', '000').replace('M', '000000').replace('B', '000000000').replace('T', '000000000000').replace(' ', '')
    return float(price_str)


def parse_percentage(percent_str):
    """Parse percentage strings like '10%' into numerical values."""
    return float(percent_str.replace('%', ''))


def calculate_housing_affordability(home_price, median_income):
    """Calculate housing affordability score."""
    home_price_value = parse_price(home_price)
    median_income_value = parse_price(median_income)
    ratio = home_price_value / median_income_value
    ratio = max(2, min(10, ratio))
    score = ((10 - ratio) / 8) * 70 + min_percentage
    return min(score, max_percentage)


def calculate_quality_of_life(city_data):
    """Calculate quality of life score."""
    factors = [
        float(city_data["education"]),
        float(city_data["healthcare_fitness"]),
        float(city_data["weather_grade"]),
        float(city_data["air_quality_index"]),
        float(city_data["commute_transit_score"]),
        float(city_data["accessibility"]),
        float(city_data["culture_entertainment"]),
    ]
    average_score = sum(factors) / len(factors)
    score = (average_score / 100) * 70 + min_percentage
    return min(score, max_percentage)


def calculate_job_market_strength(city_data):
    """Calculate job market strength score."""
    unemployment_rate = parse_percentage(city_data["unemployment_rate"])
    recent_job_growth = parse_percentage(city_data["recent_job_growth"])
    future_job_growth_index = float(city_data["future_job_growth_index"])

    unemployment_score = ((10 - unemployment_rate) / 10) * 100
    recent_job_growth_score = ((recent_job_growth + 5) / 10) * 100
    future_job_growth_score = future_job_growth_index

    weighted_score = (
        unemployment_score * 0.4 +
        recent_job_growth_score * 0.2 +
        future_job_growth_score * 0.4
    )
    score = (weighted_score / 100) * 70 + min_percentage
    return min(score, max_percentage)


def calculate_living_affordability(city_data):
    """Calculate living affordability score."""
    cost_factors = [
        float(city_data["utilities"]),
        float(city_data["food_groceries"]),
        float(city_data["transportation_cost"]),
    ]
    tax_factors = [
        parse_percentage(city_data["sales_tax"]),
        parse_percentage(city_data["state_income_tax"]),
        parse_percentage(city_data["property_tax"]),
    ]
    cost_index = sum(cost_factors) / len(cost_factors)
    normalized_cost_index = (1 - (cost_index / 150)) * 100

    average_tax_rate = sum(tax_factors) / len(tax_factors)
    normalized_tax_score = (1 - (average_tax_rate / 15)) * 100

    weighted_score = (
        normalized_cost_index * 0.7 +
        normalized_tax_score * 0.3
    )
    score = (weighted_score / 100) * 70 + min_percentage
    return min(score, max_percentage)


def get_city_score(city_data):
    """Calculate overall city score."""

    housing_affordability = calculate_housing_affordability(
        city_data["home_price"], city_data["median_household_income"]
    )
    quality_of_life = calculate_quality_of_life(city_data)
    job_market_strength = calculate_job_market_strength(city_data)
    living_affordability = calculate_living_affordability(city_data)

    overall_city_score = (housing_affordability + quality_of_life +
                          job_market_strength + living_affordability) / 4

    response = {
        "housing_affordability": round(housing_affordability, 2),
        "quality_of_life": round(quality_of_life, 2),
        "job_market_strength": round(job_market_strength, 2),
        "living_affordability": round(living_affordability, 2),
        "overall_city_score": round(overall_city_score, 2),
    }
    return response
