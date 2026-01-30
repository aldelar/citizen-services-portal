"""
CSP Agent Evaluation Package.

This package provides evaluation capabilities for the CSP Agent using
the Microsoft Azure AI Foundry Evaluation SDK.

Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk
"""

from .config import get_model_config

__all__ = ["get_model_config"]
