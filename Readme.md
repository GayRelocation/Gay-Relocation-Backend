# City Score Calculation - README

## Overview
This repository contains functions to calculate a comparative score between two cities based on multiple factors. The scoring system evaluates different categories such as housing affordability, quality of life, job market strength, and living affordability.

## Score Calculation Logic

### 1. **Clamping Values**
- `clamp_value(val, lower=55, upper=99)`: Ensures the final score stays within the range **[55, 99]**.
- `clamp_ratio(ratio, lower=0.5, upper=2.0)`: Restricts a ratio between **0.5** and **2.0**.

### 2. **Linear Transformation**
- `linear_transform(ratio)`: Converts a ratio (between 0.5 and 2.0) into a score (between **55 and 99**).
  - `ratio = 0.5` maps to `55`
  - `ratio = 1.0` maps to `77`
  - `ratio = 2.0` maps to `99`
  
### 3. **Ratio Calculation**
- `get_ratio(origin_val, destination_val, higher_is_better=True)`: Computes the ratio based on whether a higher value is preferable.
  - If `higher_is_better = True`, ratio = `destination_val / origin_val`
  - If `higher_is_better = False`, ratio = `origin_val / destination_val`
  - The ratio is then clamped between **0.5 and 2.0**.

### 4. **Category Score Calculation**
- `compute_category_score(origin, destination, fields_config)`: Computes a category score by averaging field ratios and transforming them into a score.

### 5. **Overall City Score Calculation**
- `get_city_score(origin, destination)`: Computes the overall city score based on four main categories:

#### Categories & Fields
1. **Housing Availability**
   - Home price *(lower is better)*
   - Property tax *(lower is better)*
   - Home appreciation rate *(higher is better)*
   - Price per square foot *(lower is better)*

2. **Quality of Life**
   - Education *(higher is better)*
   - Healthcare & fitness *(higher is better)*
   - Weather grade *(higher is better)*
   - Air quality index *(higher is better)*
   - Commute & transit score *(higher is better)*
   - Accessibility *(higher is better)*
   - Culture & entertainment *(higher is better)*

3. **Job Market Strength**
   - Unemployment rate *(lower is better)*
   - Recent job growth *(higher is better)*
   - Future job growth index *(higher is better)*
   - Median household income *(higher is better)*

4. **Living Affordability**
   - State income tax *(lower is better)*
   - Utilities *(lower is better)*
   - Food & groceries *(lower is better)*
   - Sales tax *(lower is better)*
   - Transportation cost *(lower is better)*

Each category score is averaged, and the final city score is computed within the **[55, 99]** range.

## Output Format
```json
{
  "housing_affordability": 78.5,
  "quality_of_life": 82.3,
  "job_market_strength": 75.9,
  "living_affordability": 80.1,
  "overall_city_score": 79.2
}
```

## Usage
1. **Provide city data in dictionary format**
2. **Call `get_city_score(origin, destination)`** with the respective city data.
3. **Get a comparative score based on provided metrics.**

This system allows an objective comparison of cities based on multiple socio-economic factors.

