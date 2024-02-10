def calculate_equity_and_per_share_value(adjusted_enterprise_value, total_debt, shares_outstanding):
    """
    Calculate the equity value and the per-share value of a company.

    Args:
    adjusted_enterprise_value (float): Adjusted Enterprise Value.
    total_debt (float): Total Debt of the company.
    shares_outstanding (int): Total number of shares outstanding.

    Returns:
    tuple: Tuple containing the equity value and the per-share value.
    """
    # Calculate Equity Value
    equity_value = adjusted_enterprise_value - total_debt

    # Calculate Per-Share Value
    per_share_value = equity_value / shares_outstanding if shares_outstanding else 0

    return equity_value, per_share_value


def adjust_for_net_debt(total_enterprise_value, total_debt, cash_and_equivalents):
    """
    Adjust the enterprise value for the net debt of the company.

    Args:
    total_enterprise_value (float): The calculated total enterprise value.
    total_debt (float): The total debt of the company.
    cash_and_equivalents (float): The cash and cash equivalents held by the company.

    Returns:
    float: The adjusted enterprise value after accounting for net debt.
    """
    net_debt = total_debt - cash_and_equivalents
    adjusted_enterprise_value = total_enterprise_value - net_debt
    return adjusted_enterprise_value


def project_future_values(base_value, growth_rate, years):
    """
    Project future values based on a base value and a growth rate.

    Args:
    base_value (float): The initial value from which to project.
    growth_rate (float): The rate of growth to apply.
    years (int): Number of years to project into the future.

    Returns:
    list: A list of projected values over the specified number of years.
    """
    return [base_value * ((1 + growth_rate) ** year) for year in range(1, years + 1)]

def calculate_average_growth_rate(values):
    """
    Calculate the average growth rate based on historical values.

    Args:
    values (list): A list of numerical values representing historical data.

    Returns:
    float: The average growth rate.
    """
    rates = []
    for i in range(1, len(values)):
        if values[i - 1] and values[i]:  # Ensuring non-zero and non-None values
            prev_value = float(values[i - 1])
            current_value = float(values[i])
            if prev_value != 0:
                growth_rate = (current_value - prev_value) / prev_value
                rates.append(growth_rate)
    return sum(rates) / len(rates) if rates else 0

