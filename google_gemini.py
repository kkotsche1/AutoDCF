from dotenv import load_dotenv
from google.oauth2 import service_account
import vertexai
from vertexai.language_models import ChatModel
from vertexai.preview.generative_models import GenerativeModel
import os

load_dotenv()

def format_gemini_opcf_projection_historical(ticker, timespan, first_year, historical_json):
    return f"""
    You are a professional financial analyst known for your extremely accurate financial forecasts.
    Provide operating cash flow in dollars for {ticker} over the next {timespan} years starting in {first_year}.
    You will only respond with a JSON object containing the estimates. Do not provide explanations.

    Use the following historical data in your determination:
    {historical_json}
    """

def format_gemini_capex_projection_historical(ticker, timespan, first_year, historical_json):
    return f"""
    You are a professional financial analyst known for extremely accurate financial forecasts.
    Provide capital expenditures in dollars for {ticker} over the next {timespan} years starting in {first_year}.
    You will only respond with a JSON object containing the estimates. Do not provide explanations.

    Use the following historical data in your determination:
    {historical_json}
    """

def format_gemini_dcrate_prompt(ticker, timespan):
    return f"Determine the appropriate discount rate for a discounted cash flow model for {ticker}. You will only respond with a decimal."

def format_gemini_perpgrowthrate_prompt(ticker, timespan):
    return f"Determine the gordown growth formula terminal growth rate for {ticker} for a discounted cash flow model. Respond only with a decimal."


def get_gemini_response(user_input):

    credentials = service_account.Credentials.from_service_account_file(
                os.environ["VERTEX_AI_AUTHFILE"],
    scopes = ["https://www.googleapis.com/auth/cloud-platform"])

    vertexai.init(project=os.environ['VERTEX_AI_PROJECT'], location="us-central1", credentials=credentials)

    chat_model = GenerativeModel("gemini-pro")

    response = chat_model.generate_content(
                    user_input,
        generation_config={
            "max_output_tokens": 252,
            "temperature": 0,
        },
                )
    return response.candidates[0].text


def predict_capex(ticker, time_period, first_year, historical_json):
    return get_gemini_response(format_gemini_capex_projection_historical(ticker, time_period, first_year, historical_json))

def predict_opcf(ticker, time_period, first_year, historical_json):
    return get_gemini_response(format_gemini_opcf_projection_historical(ticker, time_period, first_year, historical_json))

def predict_dcrate(ticker, timespan):
    return get_gemini_response(format_gemini_dcrate_prompt(ticker, timespan))

def predict_perpgrowthrate(ticker, timespan):
    return get_gemini_response(format_gemini_perpgrowthrate_prompt(ticker, timespan))