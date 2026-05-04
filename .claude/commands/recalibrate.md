# /recalibrate

Run the seed expansion crawl from scratch.

## Instructions

1. Run `uv run atlas calibrate --depth 2 --max-items 5000`
2. Monitor progress with `uv run atlas calibrate --status`
3. Report: items added, items skipped, cost, duration.
4. Check `config/interest.yaml` was updated with the new interest profile.
