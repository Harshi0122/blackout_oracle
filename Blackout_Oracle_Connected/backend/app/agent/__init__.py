"""
Blackout Oracle - AI Agent Package.

This package contains the AI reasoning and orchestration layer responsible for:

- Investigating detected grid anomalies
- Gathering evidence from analytical services
- Generating candidate scenarios
- Requesting power-system simulations
- Verifying simulation results
- Ranking verified scenarios
- Generating incident reports

The AI agent is strictly a decision-support component.
It must never directly control real electrical infrastructure,
SCADA systems, breakers, substations, or other critical systems.
"""

from .agent import BlackoutOracleAgent

__all__ = ["BlackoutOracleAgent"]