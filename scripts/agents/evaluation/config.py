#!/usr/bin/env python3
"""
Configuration for CSP Agent Evaluation.

This module provides model configuration for the Azure AI Evaluation SDK.
"""

import os

from azure.ai.evaluation import AzureOpenAIModelConfiguration


def get_model_config() -> AzureOpenAIModelConfiguration:
    """
    Configure the judge model for AI-assisted evaluation.

    Returns:
        AzureOpenAIModelConfiguration for the evaluation judge model.

    Environment Variables:
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
        AZURE_OPENAI_API_KEY: API key (optional if using DefaultAzureCredential)
        AZURE_OPENAI_EVAL_DEPLOYMENT: Deployment name for evaluation (default: gpt-4o)
        AZURE_API_VERSION: API version (default: 2024-10-21)
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT environment variable is required. "
            "Set it to your Azure OpenAI endpoint URL."
        )

    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    deployment = os.environ.get("AZURE_OPENAI_EVAL_DEPLOYMENT", "gpt-4o")
    api_version = os.environ.get("AZURE_API_VERSION", "2024-10-21")

    return AzureOpenAIModelConfiguration(
        azure_endpoint=endpoint,
        api_key=api_key,
        azure_deployment=deployment,
        api_version=api_version,
    )
