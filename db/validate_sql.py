import sqlglot
from sqlglot import expressions as exp

from config import get_config
from allowlist import ALLOWED_TABLES
from utils import get_logger

logger = get_logger(__name__)

FORBIDDEN_KEYWORDS = frozenset(  # new code
    {"insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"}  # new code
)

class SqlValidationError(ValueError):
    """Raised when SQL validation failed"""

def normalize__sql(sql: str) -> str:
    return sql.strip().rstrip(';')

def validate_sql(sql: str, max_limit: int | None = None) -> str:
    if max_limit is None:
        max_limit = get_config().sql_max_limit

    cleaned = normalize__sql(sql)

    lowered = cleaned.lower()

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in lowered:
            raise SqlValidationError(f"Forbidden keyword {keyword} was used")
        
    try:
        expression = sqlglot.parse_one(cleaned, dialect="postgress")
    except sqlglot.errors.ParseError as ex:
        raise SqlValidationError(ex)
    
    if not isinstance(expression, exp.Select):
        raise SqlValidationError("Only selects madafaka!!!")
    
    limit_node = expression.args.get("limit")

    if limit_node is not None:
        try:
            value = int(limit_node.expression.this)
        except ex:
            raise SqlValidationError("You've provided invalid limit, you fucking morron!")
        
    if value < 0 or value > max_limit:
        raise SqlValidationError(f"Limit must be gt 0 and lt {max_limit}")
    

    tables = { t.name.lower() for t in expression.find_all(exp.Table) }
    unknown = tables - ALLOWED_TABLES

    if unknown:
        raise SqlValidationError(f"Unknown tables {unknown}")
    
    logger.info("SQL Query validated")

    return cleaned