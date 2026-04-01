# Skill: Automated Testing & Mandatory Regression Coverage

## Objective
Maintain 100% architectural stability and functional integrity through a global regression suite.

## Protocol
1. **Mandatory Execution**: THE DEVELOPER MUST RUN THE ENTIRE TEST SUITE AFTER EVERY IMPLEMENTATION OR REFACTOR. No exceptions.
2. **Global Suite**: Maintain a `run_all_tests.py` or equivalent in the project root/tests folder that executes every single test module.
3. **Coverage Target**: Aim for ~100% coverage of core business logic.
4. **No Regressions**: If any test fails, the implementation is considered "FAILED". Revert or fix immediately before proceeding.
5. **Automated Guardian**: Use tools like `check_health.py` to ensure the environment is correctly set up for testing.

## Commands
- `python tests/run_all_tests.py` (Global Suite - MANDATORY)
- `pytest --cov=.` (Coverage Analysis)
