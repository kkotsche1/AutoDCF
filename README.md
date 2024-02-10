# Automated Discounted Cash Flow (DCF) Analysis Project

## README CURRENTLY OUTDATED

## Project Overview
This project automates the Discounted Cash Flow (DCF) analysis, a valuation method used to estimate the value of an investment based on its expected future cash flows. The analysis is performed using Python, leveraging the pandas library for data manipulation.

## Key Components
The project is comprised of several key functions, each responsible for a part of the DCF analysis process:

### `fetch_financial_data`
- **Purpose**: Fetches and caches financial data for a given company from an API, designed to minimize API requests by caching data locally. This function is the initial step in gathering necessary financial information for the analysis.
- **Inputs**: The stock ticker symbol and API key.
- **Output**: A dictionary containing structures for the income statement, balance sheet, cash flow statement, and shares outstanding; or `None` in case of an error.

### `extract_detailed_financials`
- **Purpose**: Combines detailed financials from income statement, balance sheet, and cash flow data into a single dictionary, providing a comprehensive view of the company's financial status.
- **Inputs**: DataFrames of income statement, balance sheet, and cash flow data.
- **Output**: A dictionary containing combined and processed financial data.

### `setup_and_forecast_dataframe`
- **Purpose**: Prepares historical financial data and forecasts future financial metrics based on calculated growth rates, crucial for projecting the company's financial performance over the forecast period.
- **Input**: A dictionary containing historical financial data.
- **Output**: A combined DataFrame of historical data and forecasted data for specified future periods.

### `perform_dcf_analysis`
- **Purpose**: Orchestrates the core of the DCF analysis process, integrating calculations of Free Cash Flow (FCF), discounting future cash flows, calculating the terminal value, adjusting for net debt, and computing the equity value per share. This function produces the final estimate of a company's per-share value.
- **Inputs**: Financial data DataFrame, balance sheet DataFrame, a dictionary of financial data, discount rate, and perpetual growth rate.
- **Output**: A float value representing the per-share value of the company.

### Helper Functions
- **`calculate_free_cash_flow`**: Calculates the Free Cash Flow (FCF) for each period.
- **`discount_cash_flows`**: Applies the discount rate to future cash flows to calculate their present value, reflecting the time value of money.
- **`calculate_terminal_value`**: Estimates the company's value at the end of the explicit forecast period using the Gordon Growth Model.
- **`calculate_equity_and_per_share_value`**: Determines the equity value by adjusting the enterprise value for net debt and then calculates the value per share.
- **`extract_historicals`**: Extracts the historical operating cash flow and capital expenditure values and formats them as a JSON to pass to the LLM.
- **`predict_opcf`**: Function to obtain operating cash flow estimates for a given ticker using the Google Gemini Pro model.
- **`predict_capex`**: Function to obtain capital expenditure estimates as a JSON for a given ticket using the Google Gemini Pro model.
- **`predict_dcrate`**: Function to obtain the discount rate for the DCF model for a given ticker using the Google Gemini Pro model.
- **`predict_perpgrowthrate`**: Function to obtain the expected perpetual growth rate for a given ticker using the Google Gemini Pro model. 

### `main`
- **Purpose**: Serves as the entry point of the program, orchestrating the workflow from data fetching to performing the DCF analysis. It sets up necessary parameters, fetches financial data, forecasts financials, and executes the DCF analysis to calculate the equity value per share.
- **Workflow**: Includes fetching financial data, extracting and processing detailed financials, forecasting future financials, and performing the DCF analysis.


## How to Use the Project
Ensure Python and pandas are installed, along with obtaining an API key from Alpha Vantage for fetching financial data. Follow these steps:

### Setup Environment
Install the required packages via pip:
```bash
pip install pandas requests requests-cache alpha_vantage google-auth google-cloud-aiplatform
```

### API Key
Obtain an API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key) or another financial data provider as needed.

### Running the Analysis
1. Update the `api_key` variable in the `main` function with your Alpha Vantage API key.
2. Set the `ticker` variable to the ticker symbol of the company you wish to analyze.
3. Run the script. The system will fetch the financial data, perform the DCF analysis, and print the per-share value of the company.

## Understanding the Code
- **Data Fetching and Preparation**: The `fetch_financial_data` function is crucial for fetching historical financial data and setting the stage for forecasting and analysis.
- **Forecasting**: The `setup_and_forecast_dataframe` function uses historical data to forecast future financial metrics, a key step in DCF analysis.
- **DCF Analysis**: The `perform_dcf_analysis` function is at the heart of the project, tying together cash flow forecasting, terminal value calculation, and net debt adjustment to estimate equity value per share.

## Possible Adjustments
- **Modifying the Forecast Period**: Adjust the forecasting horizon in the `setup_and_forecast_dataframe` function as needed.
- **Expanding Financial Metrics**: Extend the project to include more detailed financial metrics for a more granular analysis.

## Next Steps
- **Allowing more usage customization**: Currently the forecasting period, discount rate and perpetual growth rate are hard-coded. It would be useful to either automatically adjust these based on the company being analyzed, or at least enabling the user to customize these depending on their needs. In addition, it might be useful to enable a user to choose between automated forecasting of financials based on calcualted growth rates, or enabling the manual entry of growth rates for individual financials (possibly via a GUI?)
- **Export to XLSX**: It would be useful to enable the export of the analysis with the required financials into an excel sheet for further editing/customization.


## Conclusion
This project automates a complex yet critical financial analysis, providing a valuable tool for investment evaluation. This is a strongly simplified and one-size-fits-all solution to an extremely complex analysis type, therefore the results should be interpreted with a lot of apprehension. Further improvements are needed to enable a DCF analysis that mirrors potential future financials development in closer alignment with reality, for example, by incorporating consensus analyst estimates rather than simply doing linear modeling. 

