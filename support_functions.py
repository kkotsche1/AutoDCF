import pandas as pd

def extract_historicals(df):
    # Extract the last three rows of the dataframe
    last_three_rows = df.tail(3)

    # Dynamically include the index in the JSON output
    operating_cashflow_json = last_three_rows['operatingCashflow'].to_json(orient='index')
    capital_expenditures_json = last_three_rows['capitalExpenditures'].to_json(orient='index')

    return operating_cashflow_json, capital_expenditures_json


def calculate_net_debt(balance_sheet):
    """
    Calculate the net debt of a company.

    Args:
    balance_sheet (dict): Balance sheet data including current and non-current liabilities and cash equivalents.

    Returns:
    float: Net debt of the company.
    """
    total_current_liabilities = float(balance_sheet['totalCurrentLiabilities'][0])
    total_non_current_liabilities = float(balance_sheet['totalNonCurrentLiabilities'][0])
    total_liabilities = total_current_liabilities + total_non_current_liabilities

    cash_and_equivalents = float(balance_sheet['cashAndCashEquivalentsAtCarryingValue'][0])

    net_debt = total_liabilities - cash_and_equivalents
    return net_debt

def calculate_terminal_value(last_fcf, growth_rate, discount_rate):
    """
    Calculate the terminal value using the Gordon Growth Model.

    Args:
    last_fcf (float): The last projected free cash flow.
    growth_rate (float): The perpetual growth rate.
    discount_rate (float): The discount rate (WACC).

    Returns:
    float: The terminal value.
    """
    terminal_value = last_fcf * (1 + growth_rate) / (discount_rate - growth_rate)
    return terminal_value

def calculate_free_cash_flow(df):
    """
    Calculate the Free Cash Flow (FCF) for each period in the DataFrame.

    Args:
    df (DataFrame): The financial data.

    Returns:
    DataFrame: The DataFrame with an additional column for Free Cash Flow.
    """
    # Calculate Free Cash Flow for each period
    df['Free Cash Flow'] = df['operatingCashflow'] - df['capitalExpenditures']

    return df


import pandas as pd

def discount_cash_flows(df, discount_rate, historical_years):
    """
    Discount the future cash flows and calculate their present value.

    Args:
    df (DataFrame): The financial data, including a 'Free Cash Flow' column.
    discount_rate (float): The discount rate (WACC).
    historical_years (int): The number of years of historical data in the DataFrame.

    Returns:
    DataFrame: The DataFrame with an additional column for the present value of each cash flow and the actuals removed.
    """
    # Extract the year from the fiscalDateEnding
    df['Year'] = pd.to_datetime(df['fiscalDateEnding']).dt.year
    base_year = df['Year'].iloc[historical_years]  # Adjust based on the actual number of historical years

    # Calculate the number of years into the future for each cash flow
    df['Years in Future'] = df['Year'] - (base_year)

    # Calculate the present value of each future cash flow
    df['Present Value of FCF'] = df.apply(
        lambda row: row['Free Cash Flow'] / ((1 + discount_rate) ** row['Years in Future']), axis=1
    )


    # Remove the rows with historical data
    df = df.iloc[historical_years:]

    return df


def to_float(s):
    """
    Convert a string to a float, removing any currency symbols and commas.

    Args:
    s (str): The string to convert.

    Returns:
    float or None: The converted float, or None if conversion is not possible.
    """
    if s == "None":
        return 0
    try:
        return float(s.replace(',', '').replace('$', ''))
    except ValueError:
        return None