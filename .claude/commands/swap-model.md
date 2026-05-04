# /swap-model $ARGUMENTS

Swap the LLM model for an agent. Arguments format: `<agent> <model>`

## Instructions

1. Parse $ARGUMENTS to extract agent name and new model string.
2. Read `config/models.yaml`.
3. Update `agents.<agent>.model` to the new model.
4. Write the updated config back.
5. Run `uv run pytest packages/eval/ -k "<agent>" -v` to compare eval scores.
6. Report the before/after model and any score changes.
