import os
import re
import json
import time
import sqlite3
from typing import List, Dict, Any, Tuple, Optional
from app.utils.logger import logger

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "questions")
SQL_QUESTIONS_FILE = os.path.join(DATA_DIR, "sql_questions.json")

# Forbidden SQL statements and mutation keywords
FORBIDDEN_KEYWORDS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b",
    r"\bTRUNCATE\b", r"\bCREATE\b", r"\bGRANT\b", r"\bREVOKE\b", r"\bREPLACE\b",
    r"\bCALL\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bLOAD\b", r"\bOUTFILE\b",
    r"\bINFILE\b", r"\bSHUTDOWN\b", r"\bSLEEP\b", r"\bBENCHMARK\b",
    r"\bINFORMATION_SCHEMA\b", r"\bPERFORMANCE_SCHEMA\b", r"\bMYSQL\b", r"\bPG_\b"
]

class SqlService:
    @staticmethod
    def load_sql_questions() -> List[Dict[str, Any]]:
        """
        Loads and validates all SQL questions from the predefined question bank.
        Ensures strict contract: exactly 2 tables, each with >= 5 columns and >= 5 rows.
        """
        if not os.path.exists(SQL_QUESTIONS_FILE):
            logger.error(f"SQL question file not found at: {SQL_QUESTIONS_FILE}")
            return []

        try:
            with open(SQL_QUESTIONS_FILE, "r", encoding="utf-8") as f:
                raw_questions = json.load(f)

            valid_questions = []
            for q in raw_questions:
                is_valid, reason = SqlService.validate_sql_question_schema(q)
                if is_valid:
                    valid_questions.append(q)
                else:
                    logger.warning(f"Rejected SQL question '{q.get('id')}': {reason}")

            return valid_questions
        except Exception as e:
            logger.error(f"Failed to load SQL questions: {e}")
            return []

    @staticmethod
    def validate_sql_tables(tables: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validates the input database tables contract:
        - Exactly 2 tables
        - Each table has at least 5 columns and at least 5 rows
        - Column names must be unique within each table
        - Every row must contain values for all defined columns
        """
        if not isinstance(tables, list) or len(tables) != 2:
            return False, f"Expected exactly 2 tables, got {len(tables) if isinstance(tables, list) else type(tables)}"

        for idx, table in enumerate(tables):
            tname = table.get("name", f"Table_{idx+1}")
            cols = table.get("columns", [])
            rows = table.get("rows", [])

            if len(cols) < 5:
                return False, f"Table '{tname}' has {len(cols)} columns (minimum 5 required)"

            if len(rows) < 5:
                return False, f"Table '{tname}' has {len(rows)} rows (minimum 5 required)"

            if len(cols) != len(set(cols)):
                return False, f"Table '{tname}' has duplicate column names"

            for r_idx, row in enumerate(rows):
                for c in cols:
                    if c not in row:
                        return False, f"Table '{tname}' row {r_idx+1} missing column '{c}'"

        return True, "Valid"

    @staticmethod
    def validate_expected_output(
        expected_output: Dict[str, Any], 
        expected_result: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, str]:
        """
        Validates the expected output specification of a SQL question:
        - Must define non-empty columns list
        - Must define row_count >= 0
        - Must define order_required boolean
        - If expected_result is present, verify row count and column key matches
        """
        if not isinstance(expected_output, dict):
            return False, "expected_output must be a dictionary"

        cols = expected_output.get("columns", [])
        if not isinstance(cols, list) or len(cols) == 0:
            return False, "expected_output.columns must be a non-empty list of column names"

        if "row_count" not in expected_output:
            return False, "expected_output.row_count is required"

        row_count = expected_output.get("row_count")
        if not isinstance(row_count, int) or row_count < 0:
            return False, f"Invalid expected_output.row_count: {row_count}"

        if expected_result is not None:
            if not isinstance(expected_result, list):
                return False, "expected_result must be a list of row dicts"
            if len(expected_result) != row_count:
                return False, f"expected_result row count ({len(expected_result)}) does not match expected_output.row_count ({row_count})"

        return True, "Valid"

    @staticmethod
    def validate_sql_question_schema(question: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates the schema of a single SQL question:
        - Must have id, title, description, expected_query, tables
        - Input tables must satisfy validate_sql_tables (2 tables, >= 5 cols, >= 5 rows)
        - Expected output must satisfy validate_expected_output if provided
        """
        if not question.get("id") or not question.get("expected_query"):
            return False, "Missing id or expected_query"

        tables = question.get("tables", [])
        valid_tables, table_err = SqlService.validate_sql_tables(tables)
        if not valid_tables:
            return False, table_err

        if "expected_output" in question:
            valid_out, out_err = SqlService.validate_expected_output(
                question["expected_output"], 
                question.get("expected_result")
            )
            if not valid_out:
                return False, out_err

        return True, "Valid"

    @staticmethod
    def validate_query_safety(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validates safety of user SQL query:
        - Must be non-empty
        - Must start with SELECT, WITH, or EXPLAIN
        - Must not contain dangerous mutation commands
        - Must not contain multiple statements separated by semicolons
        - Must not contain comment tricks intended to bypass keyword checking
        """
        if not query or not query.strip():
            return False, "Query cannot be empty."

        clean = query.strip()

        # Reject comment blocks and line comments that could mask statements
        clean_no_comments = re.sub(r"/\*.*?\*/", " ", clean, flags=re.DOTALL)
        clean_no_comments = re.sub(r"--.*?(\r\n|\r|\n|$)", " ", clean_no_comments)
        clean_no_comments = re.sub(r"#.*?(\r\n|\r|\n|$)", " ", clean_no_comments).strip()

        if not clean_no_comments:
            return False, "Query contains only comments or whitespace."

        # Verify allowed read-only starting token
        allowed_starts = (r"^(SELECT|WITH|EXPLAIN)\b",)
        if not any(re.match(pattern, clean_no_comments, re.IGNORECASE) for pattern in allowed_starts):
            return False, "Only read-only queries (SELECT, WITH, EXPLAIN) are permitted."

        # Check for multiple statements separated by semicolons
        statements = [s.strip() for s in clean_no_comments.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements separated by semicolons are not permitted."

        # Check forbidden keywords
        for kw_regex in FORBIDDEN_KEYWORDS:
            if re.search(kw_regex, clean_no_comments, re.IGNORECASE):
                kw_name = kw_regex.replace(r"\b", "")
                return False, f"Forbidden SQL operation detected: {kw_name}. Only read-only operations are allowed."

        return True, None

    @classmethod
    def execute_query(
        cls, 
        tables: List[Dict[str, Any]], 
        query: str,
        timeout_sec: float = 2.0
    ) -> Dict[str, Any]:
        """
        Executes a SQL query in an isolated, ephemeral in-memory database pre-loaded
        strictly with the question's 2 tables.
        """
        is_safe, error_msg = cls.validate_query_safety(query)
        if not is_safe:
            return {
                "success": False,
                "error": error_msg,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0
            }

        start_time = time.perf_counter()

        # Create fresh, ephemeral in-memory SQLite database
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        try:
            # 1. Create and populate tables
            for table in tables:
                tname = table["name"]
                cols = table["columns"]
                rows = table["rows"]

                # Infer simple types or use flexible columns
                col_defs = ", ".join([f'"{col}" TEXT' for col in cols])
                cursor.execute(f'CREATE TABLE "{tname}" ({col_defs});')

                placeholders = ", ".join(["?"] * len(cols))
                insert_sql = f'INSERT INTO "{tname}" ({", ".join([f"`{c}`" for c in cols])}) VALUES ({placeholders})'

                row_tuples = []
                for r in rows:
                    row_tuples.append([r.get(c) for c in cols])

                cursor.executemany(insert_sql, row_tuples)

            conn.commit()

            # 2. Execute candidate query with strict LIMIT
            clean_query = query.strip().rstrip(";")
            cursor.execute(clean_query)

            desc = cursor.description
            if not desc:
                # Query executed but returned no result set (e.g. explain)
                exec_time = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": True,
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "execution_time_ms": exec_time
                }

            columns = [col[0] for col in desc]
            raw_rows = cursor.fetchmany(100)  # Max 100 rows for display

            formatted_rows = []
            for r in raw_rows:
                row_dict = {}
                for idx, col_name in enumerate(columns):
                    val = r[idx]
                    # Convert to appropriate JSON types if numeric
                    if isinstance(val, float) and val.is_integer():
                        val = int(val)
                    row_dict[col_name] = val
                formatted_rows.append(row_dict)

            exec_time = round((time.perf_counter() - start_time) * 1000, 2)

            return {
                "success": True,
                "columns": columns,
                "rows": formatted_rows,
                "row_count": len(formatted_rows),
                "execution_time_ms": exec_time
            }

        except sqlite3.OperationalError as op_err:
            exec_time = round((time.perf_counter() - start_time) * 1000, 2)
            clean_err = str(op_err).replace('near "', 'near "')
            return {
                "success": False,
                "error": f"SQL Execution Error: {clean_err}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": exec_time
            }
        except Exception as e:
            exec_time = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "error": f"Execution Error: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": exec_time
            }
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def evaluate_sql_answer(
        cls,
        tables: List[Dict[str, Any]],
        candidate_query: str,
        expected_query: str,
        expected_output: Optional[Dict[str, Any]] = None,
        expected_result: Optional[List[Dict[str, Any]]] = None,
        check_order: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates candidate SQL query against expected query and expected output specification.
        - Checks column count matching (rejects extra/missing columns)
        - Checks row count matching
        - Normalizes values across types (numeric, whitespace, lowercase)
        - Enforces ordering strictly if order_required is true
        """
        # Execute Candidate Query first
        candidate_res = cls.execute_query(tables, candidate_query)
        if not candidate_res["success"]:
            return {
                "is_correct": False,
                "candidate_result": candidate_res.get("rows", []),
                "expected_result": expected_result or [],
                "candidate_columns": candidate_res.get("columns", []),
                "expected_columns": expected_output.get("columns", []) if expected_output else [],
                "execution_error": candidate_res.get("error"),
                "execution_time_ms": candidate_res.get("execution_time_ms", 0.0)
            }

        # Execute Expected Query to obtain canonical expected result set
        expected_res = cls.execute_query(tables, expected_query)
        if not expected_res["success"] and expected_result is None:
            logger.error(f"Expected query execution failed: {expected_res.get('error')}")

        expected_rows = expected_res.get("rows", []) if expected_res["success"] else (expected_result or [])
        expected_cols = expected_res.get("columns", []) if expected_res["success"] else (expected_output.get("columns", []) if expected_output else [])
        
        # If expected_output specifies canonical columns, prefer them for metadata
        if expected_output and expected_output.get("columns"):
            target_cols = expected_output["columns"]
        else:
            target_cols = expected_cols

        candidate_cols = candidate_res.get("columns", [])
        candidate_rows = candidate_res.get("rows", [])

        # 1. Check Column Count
        if len(candidate_cols) != len(target_cols):
            return {
                "is_correct": False,
                "candidate_result": candidate_rows,
                "expected_result": expected_rows,
                "candidate_columns": candidate_cols,
                "expected_columns": target_cols,
                "execution_error": f"Column count mismatch: expected {len(target_cols)} column(s) ({', '.join(target_cols)}), but query returned {len(candidate_cols)} column(s) ({', '.join(candidate_cols)}).",
                "execution_time_ms": candidate_res.get("execution_time_ms", 0.0)
            }

        # 2. Check Row Count
        if len(candidate_rows) != len(expected_rows):
            return {
                "is_correct": False,
                "candidate_result": candidate_rows,
                "expected_result": expected_rows,
                "candidate_columns": candidate_cols,
                "expected_columns": target_cols,
                "execution_error": f"Row count mismatch: expected {len(expected_rows)} row(s), but query returned {len(candidate_rows)} row(s).",
                "execution_time_ms": candidate_res.get("execution_time_ms", 0.0)
            }

        # 3. Value normalization helper
        def normalize_val(val: Any) -> Any:
            if val is None:
                return "NULL"
            if isinstance(val, (int, float)):
                return round(float(val), 2)
            # Check if string is numeric float/int
            str_val = str(val).strip()
            try:
                num = float(str_val)
                return round(num, 2)
            except ValueError:
                return str_val.lower()

        def normalize_row_tuple(row_dict: Dict[str, Any]) -> Tuple[Any, ...]:
            return tuple(normalize_val(v) for v in row_dict.values())

        # Determine if strict ordering is required
        order_required = False
        if expected_output and "order_required" in expected_output:
            order_required = bool(expected_output["order_required"])
        elif check_order or ("order by" in expected_query.lower()):
            order_required = True

        cand_tuples = [normalize_row_tuple(r) for r in candidate_rows]
        exp_tuples = [normalize_row_tuple(r) for r in expected_rows]

        is_correct = False
        if order_required:
            is_correct = (cand_tuples == exp_tuples)
            error_reason = None if is_correct else "Result data or row order does not match the expected sorted solution."
        else:
            is_correct = (sorted([str(t) for t in cand_tuples]) == sorted([str(t) for t in exp_tuples]))
            error_reason = None if is_correct else "Result set data does not match the expected solution values."

        return {
            "is_correct": is_correct,
            "candidate_result": candidate_rows,
            "expected_result": expected_rows,
            "candidate_columns": candidate_cols,
            "expected_columns": target_cols,
            "execution_error": error_reason,
            "execution_time_ms": candidate_res.get("execution_time_ms", 0.0)
        }
