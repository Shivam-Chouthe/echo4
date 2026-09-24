import logging
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.db.session import engine, init_db
from app.models.memory import MemoryRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOCK_MEMORIES = [
    {
        "client_id": "seed-place-001",
        "raw_content": "Visit German Bakery in Koregaon Park Pune for breakfast croissants and iced latte",
        "source_url": "https://maps.app.goo.gl/germanbakerypune",
        "source_type": "URL",
        "client_timestamp": 1727184000000,
        "category": "PLACE",
        "title": "German Bakery Koregaon Park",
        "summary": "Iconic cafe in Koregaon Park famous for baked goods, breakfast plates, and specialty coffee.",
        "intent": "Visit for breakfast or casual coffee meet",
        "keywords": ["German Bakery", "Pune", "Koregaon Park", "Bakery", "Breakfast", "Coffee"],
        "target_place": {
            "name": "German Bakery, Koregaon Park, Pune",
            "latitude": 18.5362,
            "longitude": 73.8938,
        },
        "status": "ENRICHED",
        "hours_ago": 1,
    },
    {
        "client_id": "seed-place-002",
        "raw_content": "Aga Khan Palace Pune historical landmark and garden walking trail",
        "source_url": "https://maps.app.goo.gl/agakhanpalace",
        "source_type": "URL",
        "client_timestamp": 1727170000000,
        "category": "PLACE",
        "title": "Aga Khan Palace Heritage Visit",
        "summary": "Historic Italian-arched palace built in 1892 with serene memorial grounds and museums.",
        "intent": "Explore historical architecture and gardens",
        "keywords": ["Aga Khan Palace", "Pune", "History", "Monuments", "Architecture"],
        "target_place": {
            "name": "Aga Khan Palace, Pune",
            "latitude": 18.5524,
            "longitude": 73.9015,
        },
        "status": "ENRICHED",
        "hours_ago": 4,
    },
    {
        "client_id": "seed-recipe-001",
        "raw_content": "Rich roasted tomato and basil soup recipe with garlic sourdough croutons",
        "source_url": "https://cooking.nytimes.com/recipes/tomato-soup",
        "source_type": "URL",
        "client_timestamp": 1727150000000,
        "category": "RECIPE",
        "title": "Roasted Tomato Basil Soup",
        "summary": "Classic comforting roasted tomato soup seasoned with fresh basil leaves and crispy homemade croutons.",
        "intent": "Cook weekend comfort dinner",
        "keywords": ["Soup", "Tomato", "Basil", "Dinner", "Vegetarian", "Cooking"],
        "target_place": None,
        "status": "ENRICHED",
        "hours_ago": 8,
    },
    {
        "client_id": "seed-tool-001",
        "raw_content": "Check out uv by Astral - extremely fast Python package manager written in Rust",
        "source_url": "https://github.com/astral-sh/uv",
        "source_type": "URL",
        "client_timestamp": 1727120000000,
        "category": "TOOL",
        "title": "uv: Ultra-Fast Python Package Manager",
        "summary": "A drop-in replacement for pip and pip-tools written in Rust, offering 10-100x speedups for virtualenv creation.",
        "intent": "Try for Python project dependency management",
        "keywords": ["Python", "uv", "Rust", "DevTools", "Pip"],
        "target_place": None,
        "status": "ENRICHED",
        "hours_ago": 16,
    },
    {
        "client_id": "seed-topic-001",
        "raw_content": "Attention mechanism visualizer and Transformer query-key-value breakdown",
        "source_url": "https://jalammar.github.io/illustrated-transformer/",
        "source_type": "URL",
        "client_timestamp": 1727080000000,
        "category": "TOPIC",
        "title": "The Illustrated Transformer",
        "summary": "Step-by-step visual guide dissecting multi-head self-attention and transformer network architectures.",
        "intent": "Study deep learning attention mechanics",
        "keywords": ["Transformers", "Attention", "Deep Learning", "Machine Learning", "NLP"],
        "target_place": None,
        "status": "ENRICHED",
        "hours_ago": 24,
    },
    {
        "client_id": "seed-pending-001",
        "raw_content": "Quick reminder to check this out: https://news.ycombinator.com",
        "source_url": "https://news.ycombinator.com",
        "source_type": "URL",
        "client_timestamp": 1727187000000,
        "category": None,
        "title": None,
        "summary": None,
        "intent": None,
        "keywords": [],
        "target_place": None,
        "status": "PENDING",
        "hours_ago": 0,
    },
]


def seed_database() -> None:
    init_db()
    now = datetime.now(timezone.utc)
    inserted_count = 0

    with Session(engine) as session:
        for item in MOCK_MEMORIES:
            # Check if record already exists
            statement = select(MemoryRecord).where(MemoryRecord.client_id == item["client_id"])
            existing = session.exec(statement).first()

            if not existing:
                record = MemoryRecord(
                    client_id=item["client_id"],
                    raw_content=item["raw_content"],
                    source_url=item["source_url"],
                    source_type=item["source_type"],
                    client_timestamp=item["client_timestamp"],
                    category=item["category"],
                    title=item["title"],
                    summary=item["summary"],
                    intent=item["intent"],
                    keywords=item["keywords"],
                    target_place=item["target_place"],
                    status=item["status"],
                    created_at=now - timedelta(hours=item["hours_ago"]),
                )
                session.add(record)
                inserted_count += 1

        session.commit()

    logger.info("Successfully seeded %d sample memories.", inserted_count)


if __name__ == "__main__":
    seed_database()