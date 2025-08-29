Cost Calculation Azure Function (CalculateUsageCosts)
1. Overview
This Azure Function is a core component of the "Provider Cost Logger" autonomous agent. Its primary responsibility is to calculate the monetary cost (cost_usd) for a given list of AI model and workflow usages.

It acts as a serverless microservice that takes raw usage data and a pricing list as input, and returns a fully processed report with calculated costs for each usage entry. This function is written in Python using the v2 programming model and is designed to be called from an Azure Logic App.

2. Core Functionality
The function performs the following steps:

Receives Inputs: It accepts a JSON object containing three key properties: workflow_usage, provider_costs, and environment.

Creates a Price Lookup Table: It transforms the provider_costs array into an efficient lookup dictionary (hash map) for quick access to pricing information.

Iterates Through Usage: It loops through each entry in the workflow_usage.usage array.

Calculates Cost: For each entry, it applies one of two logic paths:

Buildship Logic: If the provider is "buildship", it calculates the cost based on the number of credits used.

Token-Based Logic: For all other providers (e.g., OpenAI, Anthropic), it calculates the cost based on the number of input and output tokens, accounting for cached vs. non-cached tokens.

Handles Errors: If pricing information for a specific provider/model combination is not found, it flags that entry with an error instead of failing the entire process.

Returns a Final Report: It combines the original workflow information with the newly calculated costs and returns a single, structured JSON object.

3. API Contract
The function is triggered by an HTTP POST request.

Endpoint: .../api/CalculateUsageCosts (The exact URL is available in the Azure Portal)

Input Body
The function expects a JSON object in the request body with the following structure:

{
  "workflow_usage": {
    "location_id": "loc-prod-123",
    "workflow_name": "AI Content Generation",
    "workflow_url": "[http://example.com/flow1](http://example.com/flow1)",
    "usage": [
      {
        "provider": "openai",
        "model": "gpt-4o",
        "input_tokens": 5000,
        "input_tokens_cached": 1000,
        "output_tokens": 1500,
        "output_tokens_cached": 500
      },
      {
        "provider": "buildship",
        "model": "node-cost",
        "buildship_total_credits": 150
      }
    ]
  },
  "provider_costs": [
    {
      "provider": "openai",
      "model": "gpt-4o",
      "input_token_cpm": 0.0025,
      "input_token_cpm_cached": 0.00125,
      "output_token_cpm": 0.01,
      "output_token_cpm_cached": 0.01
    },
    {
        "provider": "buildship",
        "model": "node-cost",
        "cost_per_node": 0.0001
    }
  ],
  "environment": "MAISY365"
}

Output Body (Success - 200 OK)
On success, the function returns a detailed report with costs calculated for each usage entry.

{
    "environment": "MAISY356",
    "location_id": "loc-prod-123",
    "workflow_name": "AI Content Generation",
    "workflow_url": "[http://example.com/flow1](http://example.com/flow1)",
    "executed_at": "2025-08-29T08:40:00.123456+00:00",
    "usage_with_costs": [
      {
        "provider": "openai",
        "model": "gpt-4o",
        "input_tokens": 5000,
        "input_tokens_cached": 1000,
        "output_tokens": 1500,
        "output_tokens_cached": 500,
        "input_tokens_uncached": 4000,
        "output_tokens_uncached": 1000,
        "cost_usd": 0.02125
      },
      {
        "provider": "buildship",
        "model": "node-cost",
        "buildship_total_credits": 150,
        "cost_usd": 0.015,
        "buildship_credits_used": 150
      }
    ]
}

4. Local Development & Deployment
Prerequisites
Python 3.9+

Visual Studio Code

Azure Functions Extension for VS Code

Azure Functions Core Tools

Deployment
This function is developed locally using the Python v2 model. To deploy, use the "Deploy to Function App..." command from the Azure Functions extension in VS Code.

Important: The @app.route() decorator in function_app.py must not contain a custom route parameter, as this will cause validation to fail when called from a Logic App.

Correct: @app.route(auth_level=func.AuthLevel.FUNCTION)
Incorrect: @app.route(route="CalculateUsageCosts", ...)
