import json
import pandas as pd
from alpha_vantage.fundamentaldata import FundamentalData
import requests
import os

from dotenv import load_dotenv

from support_functions import calculate_free_cash_flow, discount_cash_flows, calculate_terminal_value, to_float, extract_historicals
from calculation_functions import adjust_for_net_debt, calculate_equity_and_per_share_value
from google_gemini import predict_opcf, predict_dcrate, predict_capex, predict_perpgrowthrate


def process_df(df, exclude_columns, year):
    """
    Process a DataFrame by converting appropriate columns to float.

    Args:
    df (DataFrame): The DataFrame to process.
    exclude_columns (list): Columns to exclude from conversion.
    year (int): The index of the year to process.

    Returns:
    dict: A dictionary of processed data.
    """
    return {col: to_float(val) if col not in exclude_columns else val
            for col, val in df.iloc[year].items()}

def extract_detailed_financials(income_statement_df, balance_sheet_df, cash_flow_df):
    """
        Extract and combine detailed financials from income statement, balance sheet, and cash flow data.

        Args:
        income_statement_df (DataFrame): DataFrame of income statement data.
        balance_sheet_df (DataFrame): DataFrame of balance sheet data.
        cash_flow_df (DataFrame): DataFrame of cash flow data.

        Returns:
        dict: A dictionary containing detailed financials combined from all data sources.
        """

    extracted_financials = {}
    previous_year_working_capital = None

    exclude_columns = ['fiscalDateEnding', 'reportedCurrency']

    def process_df(df):
        return {col: to_float(val) if col not in exclude_columns else val
                for col, val in df.iloc[year].items()}


    # Find the minimum length among the three dataframes
    min_length = min(len(income_statement_df), len(balance_sheet_df), len(cash_flow_df))


    for year in range(min_length):
        year_data = {}

        # Process each DataFrame
        is_data = process_df(income_statement_df)
        bs_data = process_df(balance_sheet_df)
        cf_data = process_df(cash_flow_df)

        # Update year_data with processed data
        year_data.update(is_data)
        year_data.update(bs_data)
        year_data.update(cf_data)

        # Additional Data Calculations
        current_year_working_capital = bs_data['totalCurrentAssets'] - bs_data['totalCurrentLiabilities']
        year_data['Working Capital'] = current_year_working_capital
        if previous_year_working_capital is not None:
            year_data['Change in Working Capital'] = current_year_working_capital - previous_year_working_capital
        else:
            year_data['Change in Working Capital'] = None
        previous_year_working_capital = current_year_working_capital

        # Assuming Dividends Paid is available in the cash flow statement
        year_data['Dividends Paid'] = cf_data.get('dividendPayout', 0)

        extracted_financials[is_data['fiscalDateEnding'][:4]] = year_data

    return extracted_financials, min_length


def fetch_financial_data(ticker, api_key):
    fd = FundamentalData(api_key)
    financial_data_filename = f"{ticker}_financial_data.json"

    try:
        # Check if financial data is already available as a JSON file
        if os.path.exists(financial_data_filename):
            with open(financial_data_filename, 'r') as file:
                financial_data = json.load(file)
                # Convert the loaded data back to DataFrame
                financial_data['income_statement'] = pd.DataFrame(financial_data['income_statement'])
                financial_data['balance_sheet'] = pd.DataFrame(financial_data['balance_sheet'])
                financial_data['cash_flow'] = pd.DataFrame(financial_data['cash_flow'])
                return financial_data
        else:
            # Fetch company overview data
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
            overview_response = requests.get(overview_url)
            overview_data = overview_response.json()

            # Fetch and process other financial data
            income_statement, _ = fd.get_income_statement_annual(symbol=ticker)
            balance_sheet, _ = fd.get_balance_sheet_annual(symbol=ticker)
            cash_flow, _ = fd.get_cash_flow_annual(symbol=ticker)

            financial_data = {
                "income_statement": pd.DataFrame(income_statement),
                "balance_sheet": pd.DataFrame(balance_sheet),
                "cash_flow": pd.DataFrame(cash_flow),
                "shares_outstanding": int(overview_data.get("SharesOutstanding", 0))
            }

            # Save the fetched data to a JSON file
            with open(financial_data_filename, 'w') as file:
                json_data = {key: (value.to_dict(orient='list') if isinstance(value, pd.DataFrame) else value)
                             for key, value in financial_data.items()}
                json.dump(json_data, file)

            return financial_data

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


from datetime import datetime, timedelta

def setup_and_forecast_dataframe_llm(historical_df, operating_cashflow_json, capital_expenditures_json):
    # Convert JSON strings to Python dictionaries
    operating_cashflow = json.loads(operating_cashflow_json.replace("`", ""))
    capital_expenditures = json.loads(capital_expenditures_json.replace("`", ""))

    # Determine the last fiscal date and reported currency
    last_fiscal_date = historical_df['fiscalDateEnding'].dropna().iloc[-1]
    reported_currency = historical_df['reportedCurrency'].dropna().iloc[-1]

    # Convert last fiscal date to a datetime object
    last_fiscal_date = datetime.strptime(last_fiscal_date, "%Y-%m-%d")

    # Initialize the forecast DataFrame
    forecast_df = pd.DataFrame()

    # Since we no longer calculate future values, we iterate over the years provided in the JSON dictionaries
    # Assuming both JSONs cover the same fiscal years
    for year in operating_cashflow.keys():
        future_year_data = {
            'operatingCashflow': operating_cashflow[year],
            'capitalExpenditures': capital_expenditures[year]
        }

        # Calculate the fiscal date for the future year
        future_fiscal_date = (last_fiscal_date + timedelta(
            days=365 * (int(year) - int(last_fiscal_date.strftime("%Y"))))).strftime("%Y-%m-%d")

        # Add fiscal date and reported currency to the data
        future_year_data['fiscalDateEnding'] = future_fiscal_date
        future_year_data['reportedCurrency'] = reported_currency

        # Convert future_year_data to a DataFrame and concatenate it with forecast_df
        future_year_df = pd.DataFrame(
            [future_year_data])  # Enclose future_year_data in a list to ensure it's treated as a single row
        forecast_df = pd.concat([forecast_df, future_year_df], ignore_index=True)

    # When setting the forecast_df index, ensure you're working with integers.
    # Assuming historical_df.index[-1] is an integer or can be safely converted to one:
    last_index = int(historical_df.index[-1]) if isinstance(historical_df.index[-1], str) else historical_df.index[-1]
    forecast_df.index = range(last_index + 1, last_index + 1 + len(forecast_df))

    # Combine historical and forecasted data
    combined_df = pd.concat([historical_df, forecast_df])

    return combined_df


def perform_dcf_analysis(df, balance_sheet_df, financial_data, discount_rate, perpetual_growth_rate, num_years_historicals):
    """
    Perform a Discounted Cash Flow (DCF) analysis on the provided financial data.

    Args:
    df (DataFrame): The financial data.
    discount_rate (float): The weighted average cost of capital (WACC).
    perpetual_growth_rate (float): The perpetual growth rate for terminal value calculation.

    Returns:
    float: The per-share value of the company.
    """
    # Ensure dataframe is sorted by fiscalDateEnding in ascending order
    df = df.sort_values(by='fiscalDateEnding')

    # Initialize variables
    total_present_value_of_fcfs = 0
    terminal_value = 0

    # Calculate Free Cash Flows (FCF)
    df_with_fcf = calculate_free_cash_flow(df)

    # Discount Future FCFs and Calculate Present Value
    df_with_pv_fcf = discount_cash_flows(df_with_fcf, discount_rate, num_years_historicals)

    for index, row in df_with_pv_fcf.iterrows():
        total_present_value_of_fcfs = total_present_value_of_fcfs + row["Present Value of FCF"]

    # Calculate Terminal Value at the end of the projection period
    last_fcf = df_with_pv_fcf['Free Cash Flow'].iloc[-1]
    terminal_value = calculate_terminal_value(last_fcf, perpetual_growth_rate, discount_rate)

    # Discount the Terminal Value back to its present value
    years_in_future = df_with_pv_fcf['Years in Future'].iloc[-1]
    present_value_of_terminal_value = terminal_value / ((1 + discount_rate) ** years_in_future)

    # Calculate Total Enterprise Value
    total_enterprise_value = total_present_value_of_fcfs + present_value_of_terminal_value

    # Retrieving latest cash and net debt data for enterprise value adjustment
    latest_balance_sheet = balance_sheet_df.iloc[0]  # Accessing the first row for latest data
    total_debt = float(latest_balance_sheet['totalLiabilities'])
    cash_and_equivalents = float(latest_balance_sheet[
        'cashAndCashEquivalentsAtCarryingValue'])

    # Adjusting enterprise value under consideration of net debt and cash
    adjusted_enterprise_value = adjust_for_net_debt(total_enterprise_value, total_debt, cash_and_equivalents)

    # Calculate Equity Value and Per-Share Value
    shares_outstanding = financial_data["shares_outstanding"]
    equity_value, per_share_value = calculate_equity_and_per_share_value(adjusted_enterprise_value, total_debt,
                                                                         shares_outstanding)

    ### SANITY CHEKC PRINTING ###

    print("last fcf ", last_fcf)
    print("terminal value ", terminal_value)
    print("present value of terminal value ", present_value_of_terminal_value)
    print("total pvalue of fcfs ", total_present_value_of_fcfs)
    print("pv of terminal value ", present_value_of_terminal_value)
    print("total debt ", total_debt)
    print("cash and cash equivalents ", cash_and_equivalents)
    print("adjusted enterprise value ", adjusted_enterprise_value)
    print()

    # Return the per-share value
    return per_share_value




def main():
    load_dotenv()
    api_key = os.getenv("ALPHAVANTAGE_API_KEY") # Your API key
    ticker = 'AAPL'  # Replace with your target company's ticker
    time_period = 10
    first_year = 2024

    financial_data = fetch_financial_data(ticker, api_key)
    detailed_financials, num_years_historicals = extract_detailed_financials(financial_data["income_statement"], financial_data["balance_sheet"], financial_data["cash_flow"])

    # Extract historical data
    historical_df = pd.DataFrame(detailed_financials)

    # Transpose and reverse the order of rows in the DataFrame
    historical_df = historical_df.T.iloc[::-1]

    # Extracting historical values to pass them to Gemini Ultra for more accurate future predictions
    operating_cashflow_historicals, capex_historicals = extract_historicals(historical_df)

    # Gemini CapEx estimation
    capital_expenditures_json_string = predict_capex(ticker, time_period, first_year, capex_historicals)

    # Gemini Operating cash flow estimation
    operating_cashflow_json_string = predict_opcf(ticker, time_period, first_year, operating_cashflow_historicals)

    # Estimating our discount rate with Gemini
    discount_rate = float(predict_dcrate(ticker, time_period))
    perp_growth_rate = float(predict_perpgrowthrate(ticker, time_period))

    print("Discount Rate: ", discount_rate)
    print("Perpetual Growth Rate: ", perp_growth_rate)

    forecasted_df = setup_and_forecast_dataframe_llm(historical_df, operating_cashflow_json_string, capital_expenditures_json_string)

    # Extract the balance sheet DataFrame for the Net Debt calculation
    balance_sheet_df = pd.DataFrame(financial_data["balance_sheet"])

    per_share_value = perform_dcf_analysis(forecasted_df, balance_sheet_df, financial_data,
                                           discount_rate=discount_rate, perpetual_growth_rate=perp_growth_rate,
                                           num_years_historicals = num_years_historicals)

    print(f"---------- PER SHARE VALUE: {per_share_value} -----------------")


if __name__ == "__main__":
    main()
