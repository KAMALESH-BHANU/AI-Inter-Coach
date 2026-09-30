import pytest
import json
import os
from fastapi.testclient import TestClient
from app.main import app
from app.services.sql_service import SqlService
from app.services.question_service import QuestionService
from app.services.scoring_service import ScoringService
from app.db.models import QuestionModel, QuestionType, CandidateAnswerModel

client = TestClient(app)

def test_sql_question_bank_schema_compliance():
    """Verify all questions in sql_questions.json have exactly 2 tables, each with >= 5 cols and >= 5 rows."""
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "questions", "sql_questions.json")
    assert os.path.exists(filepath), "sql_questions.json not found"
    
    with open(filepath, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    assert len(questions) >= 10, f"Expected at least 10 SQL questions, found {len(questions)}"
    
    for q in questions:
        tables = q.get("tables", [])
        assert len(tables) == 2, f"Question {q.get('id')} has {len(tables)} tables, expected exactly 2"
        
        for t in tables:
            cols = t.get("columns", [])
            rows = t.get("rows", [])
            assert len(cols) >= 5, f"Question {q.get('id')} table {t.get('name')} has {len(cols)} columns, expected >= 5"
            assert len(rows) >= 5, f"Question {q.get('id')} table {t.get('name')} has {len(rows)} rows, expected >= 5"

def test_sql_query_safety_validation():
    """Verify query safety checker blocks dangerous commands and allows safe queries."""
    # Safe queries
    safe_queries = [
        "SELECT * FROM Employees;",
        "SELECT dept_id, AVG(salary) FROM Employees GROUP BY dept_id HAVING AVG(salary) > 50000;",
        "WITH HighEarners AS (SELECT * FROM Employees WHERE salary > 80000) SELECT * FROM HighEarners;",
        "SELECT e.emp_name, d.dept_name FROM Employees e JOIN Departments d ON e.dept_id = d.dept_id;"
    ]
    for q in safe_queries:
        is_safe, err = SqlService.validate_query_safety(q)
        assert is_safe is True, f"Expected query to be safe: {q}, error: {err}"

    # Dangerous queries (mutations, DDL, multi-statement)
    dangerous_queries = [
        "DROP TABLE Employees;",
        "DELETE FROM Employees WHERE emp_id = 1;",
        "UPDATE Employees SET salary = 999999;",
        "INSERT INTO Employees VALUES (10, 'Hacker', 'IT', 99999, '2023-01-01');",
        "ALTER TABLE Employees DROP COLUMN salary;",
        "TRUNCATE TABLE Employees;",
        "CREATE TABLE Hackers (id INT);",
        "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%';",
        "SELECT * FROM Employees; DROP TABLE Employees;"
    ]
    for q in dangerous_queries:
        is_safe, err = SqlService.validate_query_safety(q)
        assert is_safe is False, f"Expected dangerous query to be blocked: {q}"

def test_in_memory_sql_execution_and_evaluation():
    """Verify in-memory execution produces accurate result sets and compares correctly with reference query."""
    tables_data = [
        {
            "name": "Employees",
            "columns": ["emp_id", "emp_name", "dept_id", "salary", "hire_date"],
            "rows": [
                {"emp_id": 101, "emp_name": "Alice Smith", "dept_id": 1, "salary": 85000.0, "hire_date": "2020-03-15"},
                {"emp_id": 102, "emp_name": "Bob Jones", "dept_id": 1, "salary": 62000.0, "hire_date": "2021-06-01"},
                {"emp_id": 103, "emp_name": "Charlie Brown", "dept_id": 2, "salary": 95000.0, "hire_date": "2019-01-10"},
                {"emp_id": 104, "emp_name": "Diana Prince", "dept_id": 2, "salary": 78000.0, "hire_date": "2022-04-20"},
                {"emp_id": 105, "emp_name": "Evan Wright", "dept_id": 3, "salary": 54000.0, "hire_date": "2023-08-11"}
            ]
        },
        {
            "name": "Departments",
            "columns": ["dept_id", "dept_name", "location", "budget", "head_count"],
            "rows": [
                {"dept_id": 1, "dept_name": "Engineering", "location": "Building A", "budget": 500000.0, "head_count": 25},
                {"dept_id": 2, "dept_name": "Marketing", "location": "Building B", "budget": 300000.0, "head_count": 15},
                {"dept_id": 3, "dept_name": "Sales", "location": "Building C", "budget": 250000.0, "head_count": 20},
                {"dept_id": 4, "dept_name": "HR", "location": "Building A", "budget": 150000.0, "head_count": 8},
                {"dept_id": 5, "dept_name": "Finance", "location": "Building B", "budget": 400000.0, "head_count": 12}
            ]
        }
    ]

    # Test candidate query matching reference
    expected_query = "SELECT emp_name, salary FROM Employees WHERE salary > 70000 ORDER BY salary DESC;"
    candidate_correct = "SELECT emp_name, salary FROM Employees WHERE salary > 70000 ORDER BY salary DESC;"
    candidate_incorrect = "SELECT emp_name, salary FROM Employees WHERE salary > 90000;"

    res_correct = SqlService.evaluate_sql_answer(tables_data, candidate_correct, expected_query)
    assert res_correct["is_correct"] is True
    assert len(res_correct["candidate_result"]) == 3

    res_bad = SqlService.evaluate_sql_answer(tables_data, candidate_incorrect, expected_query)
    assert res_bad["is_correct"] is False

def test_dynamic_sql_generation_and_distinctness():
    """Ensure QuestionService generates exactly 2 dynamic SQL questions with distinct IDs."""
    sql_qs = QuestionService.get_dynamic_sql_questions(count=2)
    assert len(sql_qs) == 2
    assert sql_qs[0].id != sql_qs[1].id
    assert sql_qs[0].type == QuestionType.SQL
    assert sql_qs[1].type == QuestionType.SQL
    assert len(sql_qs[0].tables) == 2
    assert len(sql_qs[1].tables) == 2

def test_sql_score_formula():
    """Verify SQL score formula: (correct / 2) * 100 -> 0%, 50%, 100%."""
    q_sql_1 = QuestionModel(id="SQL_1", skill="SQL", difficulty="medium", type=QuestionType.SQL, question="Q1", expected_query="SELECT 1;")
    q_sql_2 = QuestionModel(id="SQL_2", skill="SQL", difficulty="medium", type=QuestionType.SQL, question="Q2", expected_query="SELECT 2;")
    
    questions = [
        QuestionModel(id="INTRO_1", skill="General", difficulty="easy", type=QuestionType.INTRODUCTION, question="Tell me about yourself.")
    ] + [
        QuestionModel(id=f"P_{i}", skill="Project", difficulty="medium", type=QuestionType.PROJECT, question=f"P {i}")
        for i in range(3)
    ] + [
        QuestionModel(id=f"T_{i}", skill="Java", difficulty="medium", type=QuestionType.TECHNICAL, question=f"T {i}")
        for i in range(5)
    ] + [
        QuestionModel(id=f"PS_{i}", skill="Pseudocode", difficulty="medium", type=QuestionType.PSEUDOCODE, question=f"PS {i}")
        for i in range(2)
    ] + [q_sql_1, q_sql_2]

    # Case 1: 0 correct
    ans_0 = [CandidateAnswerModel(question_id=q.id, question_index=idx, is_correct=False) for idx, q in enumerate(questions)]
    score_0 = ScoringService.aggregate_session_scores(questions, ans_0)
    assert score_0.sql_score == 0.0

    # Case 2: 1 correct
    ans_1 = [CandidateAnswerModel(question_id=q.id, question_index=idx, is_correct=(idx == 11)) for idx, q in enumerate(questions)]
    score_1 = ScoringService.aggregate_session_scores(questions, ans_1)
    assert score_1.sql_score == 50.0

    # Case 3: 2 correct
    ans_2 = [CandidateAnswerModel(question_id=q.id, question_index=idx, is_correct=(idx in (11, 12))) for idx, q in enumerate(questions)]
    score_2 = ScoringService.aggregate_session_scores(questions, ans_2)
    assert score_2.sql_score == 100.0

def test_sql_run_api_endpoint():
    """Verify POST /api/interview/sql/run executes safe queries."""
    # Register candidate & create session
    reg_res = client.post("/api/auth/register", json={
        "email": "sqlrunner@example.com",
        "full_name": "SQL Runner Candidate",
        "password": "password123",
        "skills": ["Python", "SQL"]
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/api/interview/create", json={
        "skills": ["Python", "SQL"]
    }, headers=headers)
    assert create_res.status_code == 200
    session_data = create_res.json()
    session_id = session_data["session_id"]
    
    # Get session details to find SQL question ID
    session_res = client.get(f"/api/interview/{session_id}", headers=headers)
    questions = session_res.json()["questions"]
    sql_q = next(q for q in questions if q["type"] == "sql")
    
    # Run a valid query
    table_name = sql_q["tables"][0]["name"]
    run_res = client.post("/api/interview/sql/run", json={
        "session_id": session_id,
        "question_id": sql_q["id"],
        "query": f"SELECT * FROM {table_name} LIMIT 3;"
    }, headers=headers)
    assert run_res.status_code == 200
    res_data = run_res.json()
    assert res_data["success"] is True
    assert res_data["row_count"] == 3
    assert len(res_data["columns"]) >= 5

def test_decoupled_table_and_output_validation():
    """Verify input tables require >= 5 cols and >= 5 rows, while expected output can have fewer cols/rows."""
    # Valid 2 tables (>= 5 cols, >= 5 rows)
    valid_tables = [
        {
            "name": "T1",
            "columns": ["c1", "c2", "c3", "c4", "c5"],
            "rows": [{"c1": i, "c2": "a", "c3": "b", "c4": "c", "c5": "d"} for i in range(5)]
        },
        {
            "name": "T2",
            "columns": ["k1", "k2", "k3", "k4", "k5"],
            "rows": [{"k1": i, "k2": "x", "k3": "y", "k4": "z", "k5": "w"} for i in range(5)]
        }
    ]
    is_valid_t, err_t = SqlService.validate_sql_tables(valid_tables)
    assert is_valid_t is True, f"Valid tables failed validation: {err_t}"

    # Invalid table (only 4 cols)
    invalid_tables = [
        {
            "name": "T1",
            "columns": ["c1", "c2", "c3", "c4"],
            "rows": [{"c1": i, "c2": "a", "c3": "b", "c4": "c"} for i in range(5)]
        },
        valid_tables[1]
    ]
    is_valid_inv, _ = SqlService.validate_sql_tables(invalid_tables)
    assert is_valid_inv is False, "Expected table with 4 columns to be rejected"

    # Expected output with only 1 column and 1 row (e.g. second highest salary)
    single_out = {
        "columns": ["second_highest_salary"],
        "row_count": 1,
        "order_required": False
    }
    is_valid_out, err_o = SqlService.validate_expected_output(single_out, [{"second_highest_salary": 85000}])
    assert is_valid_out is True, f"Single output validation failed: {err_o}"

    # Expected output with 2 columns and 3 rows (e.g. top 3 customers)
    top3_out = {
        "columns": ["customer_name", "total_spent"],
        "row_count": 3,
        "order_required": True,
        "ordering": "total_spent DESC"
    }
    is_valid_top3, err_top3 = SqlService.validate_expected_output(top3_out, [
        {"customer_name": "A", "total_spent": 100},
        {"customer_name": "B", "total_spent": 90},
        {"customer_name": "C", "total_spent": 80}
    ])
    assert is_valid_top3 is True, f"Top3 output validation failed: {err_top3}"

def test_sql_evaluation_column_mismatch_rejection():
    """Verify evaluation rejects candidate queries that select unrequested columns."""
    tables_data = [
        {
            "name": "Employees",
            "columns": ["emp_id", "emp_name", "dept_id", "salary", "hire_date"],
            "rows": [
                {"emp_id": 1, "emp_name": "Alice", "dept_id": 1, "salary": 80000, "hire_date": "2020-01-01"},
                {"emp_id": 2, "emp_name": "Bob", "dept_id": 1, "salary": 90000, "hire_date": "2020-01-01"},
                {"emp_id": 3, "emp_name": "Charlie", "dept_id": 2, "salary": 70000, "hire_date": "2020-01-01"},
                {"emp_id": 4, "emp_name": "David", "dept_id": 2, "salary": 60000, "hire_date": "2020-01-01"},
                {"emp_id": 5, "emp_name": "Eve", "dept_id": 3, "salary": 85000, "hire_date": "2020-01-01"}
            ]
        },
        {
            "name": "Departments",
            "columns": ["dept_id", "dept_name", "loc", "budget", "manager"],
            "rows": [
                {"dept_id": 1, "dept_name": "Eng", "loc": "BLR", "budget": 100, "manager": "M1"},
                {"dept_id": 2, "dept_name": "HR", "loc": "CHE", "budget": 50, "manager": "M2"},
                {"dept_id": 3, "dept_name": "Fin", "loc": "MUM", "budget": 80, "manager": "M3"},
                {"dept_id": 4, "dept_name": "Ops", "loc": "DEL", "budget": 60, "manager": "M4"},
                {"dept_id": 5, "dept_name": "Sales", "loc": "HYD", "budget": 90, "manager": "M5"}
            ]
        }
    ]

    expected_query = "SELECT emp_name, salary FROM Employees WHERE salary > 75000;"
    expected_output = {
        "columns": ["emp_name", "salary"],
        "row_count": 3,
        "order_required": False
    }

    # Correct candidate query with exact 2 columns
    cand_correct = "SELECT emp_name, salary FROM Employees WHERE salary > 75000;"
    res_c = SqlService.evaluate_sql_answer(tables_data, cand_correct, expected_query, expected_output=expected_output)
    assert res_c["is_correct"] is True

    # Candidate query selecting extra columns (e.g. SELECT *)
    cand_extra_cols = "SELECT * FROM Employees WHERE salary > 75000;"
    res_extra = SqlService.evaluate_sql_answer(tables_data, cand_extra_cols, expected_query, expected_output=expected_output)
    assert res_extra["is_correct"] is False
    assert "Column count mismatch" in res_extra["execution_error"]

def test_sql_evaluation_order_sensitivity():
    """Verify evaluation respects order_required: true vs order_required: false."""
    tables_data = [
        {
            "name": "Items",
            "columns": ["id", "name", "price", "cat", "stock"],
            "rows": [
                {"id": 1, "name": "Item A", "price": 10, "cat": "C1", "stock": 100},
                {"id": 2, "name": "Item B", "price": 30, "cat": "C1", "stock": 50},
                {"id": 3, "name": "Item C", "price": 20, "cat": "C1", "stock": 70},
                {"id": 4, "name": "Item D", "price": 40, "cat": "C1", "stock": 20},
                {"id": 5, "name": "Item E", "price": 50, "cat": "C1", "stock": 10}
            ]
        },
        {
            "name": "Categories",
            "columns": ["cat_id", "cat_name", "desc", "floor", "mgr"],
            "rows": [{"cat_id": f"C{i}", "cat_name": f"Cat{i}", "desc": "d", "floor": 1, "mgr": "m"} for i in range(1, 6)]
        }
    ]

    expected_ordered_query = "SELECT name, price FROM Items ORDER BY price DESC LIMIT 3;"
    expected_output_ordered = {
        "columns": ["name", "price"],
        "row_count": 3,
        "order_required": True,
        "ordering": "price DESC"
    }

    # Query with correct sorting
    cand_ordered = "SELECT name, price FROM Items ORDER BY price DESC LIMIT 3;"
    res_ord = SqlService.evaluate_sql_answer(tables_data, cand_ordered, expected_ordered_query, expected_output=expected_output_ordered)
    assert res_ord["is_correct"] is True

    # Query with wrong sorting (ASC instead of DESC)
    cand_wrong_ord = "SELECT name, price FROM (SELECT name, price FROM Items ORDER BY price DESC LIMIT 3) ORDER BY price ASC;"
    res_wrong_ord = SqlService.evaluate_sql_answer(tables_data, cand_wrong_ord, expected_ordered_query, expected_output=expected_output_ordered)
    assert res_wrong_ord["is_correct"] is False

