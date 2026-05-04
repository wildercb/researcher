# /seed $ARGUMENTS

Add a seed and trigger calibration. Arguments format: `<type> <identifier>`

Types: paper, author, venue, keyword

## Instructions

1. Parse $ARGUMENTS to extract seed type and identifier.
2. For papers: accept DOI (10.xxx), arXiv ID (arxiv:xxx or just the ID), or title string (fuzzy match, confirm).
3. For authors: accept name, optionally with --orcid flag.
4. For venues: accept name or --rss URL.
5. For keywords: accept term, optionally with --weight float.
6. Add the seed to `config/seeds.yaml` under the appropriate section.
7. Run `uv run atlas seed <type> <identifier>` to register in the database.
8. Report what was added.
