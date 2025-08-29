import azure.functions as func
import logging
import json
import math
from datetime import datetime, timezone

app = func.FunctionApp()

@app.function_name(name="CalculateUsageCosts")
@app.route(route="", auth_level=func.AuthLevel.FUNCTION)  # set route to "" (root)
def calculate_usage_costs(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
             "Please pass a valid JSON in the request body.",
             status_code=400
        )

    workflow_usage = req_body.get('workflow_usage')
    provider_costs = req_body.get('provider_costs')
    environment = req_body.get('environment')

    if not all([workflow_usage, provider_costs, environment]):
        return func.HttpResponse(
            "Please provide 'workflow_usage', 'provider_costs', and 'environment' in the request body.",
            status_code=400
        )

    cost_lookup = {f"{row.get('provider')}:{row.get('model')}": row for row in provider_costs}

    def calculate_cost(entry):
        key = f"{entry.get('provider')}:{entry.get('model')}"
        pricing = cost_lookup.get(key)

        if not pricing:
            entry['cost_usd'] = None
            entry['error'] = f"Pricing not found for {key}"
            return entry

        if entry.get('provider') == "buildship":
            credits = entry.get('buildship_total_credits', 0)
            cost_per_node = pricing.get('cost_per_node', 0)
            cost = credits * cost_per_node
            entry['cost_usd'] = round(cost * 1000000) / 1000000
            entry['buildship_credits_used'] = credits
            return entry

        def per_token(cpm):
            return (cpm or 0) / 1000

        input_tokens = entry.get('input_tokens', 0)
        input_cached = entry.get('input_tokens_cached', 0)
        input_uncached = input_tokens - input_cached

        output_tokens = entry.get('output_tokens', 0)
        output_cached = entry.get('output_tokens_cached', 0)
        output_uncached = output_tokens - output_cached

        cost = (
            input_uncached * per_token(pricing.get('input_token_cpm')) +
            input_cached * per_token(pricing.get('input_token_cpm_cached')) +
            output_uncached * per_token(pricing.get('output_token_cpm')) +
            output_cached * per_token(pricing.get('output_token_cpm_cached'))
        )

        entry['input_tokens_uncached'] = input_uncached
        entry['output_tokens_uncached'] = output_uncached
        entry['cost_usd'] = round(cost * 1000000) / 1000000
        return entry

    usage_with_costs = [calculate_cost(entry) for entry in workflow_usage.get('usage', [])]

    final_result = {
        "environment": environment,
        "location_id": workflow_usage.get('location_id'),
        "workflow_name": workflow_usage.get('workflow_name'),
        "workflow_url": workflow_usage.get('workflow_url'),
        "executed_at": workflow_usage.get('executed_at') or datetime.now(timezone.utc).isoformat(),
        "usage_with_costs": usage_with_costs
    }

    return func.HttpResponse(
        json.dumps(final_result),
        status_code=200,
        mimetype="application/json"
    )
