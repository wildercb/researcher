from enum import StrEnum


class AtlasMode(StrEnum):
    LAPTOP = "laptop"
    VPS = "vps"


class ItemKind(StrEnum):
    PAPER = "paper"
    PREPRINT = "preprint"
    POST = "post"
    TALK = "talk"
    BLOG = "blog"
    ISSUE = "issue"
    REVIEW = "review"


class SeedType(StrEnum):
    PAPER = "paper"
    AUTHOR = "author"
    VENUE = "venue"
    KEYWORD = "keyword"
    NEGATIVE = "negative"


class FeedbackSignal(StrEnum):
    LIKED = "liked"
    HIDDEN = "hidden"
    READ = "read"
    DEEP_READ = "deep_read"
    MORE_LIKE_THIS = "more_like_this"


class EnrichmentStatus(StrEnum):
    PENDING = "pending"
    ENRICHED = "enriched"
    FAILED = "failed"
    SKIPPED = "skipped"
