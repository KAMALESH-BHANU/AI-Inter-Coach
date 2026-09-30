import os
import json

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(DATA_DIR, "skills")
os.makedirs(SKILLS_DIR, exist_ok=True)

# Curated question banks for major technical skills
SKILL_QUESTIONS = {
    "Java": [
        {
            "id": "JAVA_001",
            "skill": "Java",
            "difficulty": "medium",
            "question": "What is the difference between final, finally, and finalize in Java?",
            "expected_concepts": ["final keyword", "finally block", "finalize method", "garbage collection"],
            "ideal_answer": "final is a keyword to declare constants, prevent method overriding or class inheritance. finally is a block used in exception handling that executes regardless of whether an exception occurs. finalize is a method on Object called by the Garbage Collector before an object is reclaimed.",
            "explanation": "Tests understanding of Java core keywords, exception handling flow, and GC lifecycle."
        },
        {
            "id": "JAVA_002",
            "skill": "Java",
            "difficulty": "medium",
            "question": "Explain how HashMap works internally in Java.",
            "expected_concepts": ["hashcode", "equals", "buckets", "collision handling", "red-black tree"],
            "ideal_answer": "HashMap uses key's hashCode() to compute the bucket index. Key-value pairs are stored as Node objects in linked lists. Since Java 8, if a bucket linked list exceeds 8 nodes, it transforms into a balanced Red-Black tree (O(log n) lookup).",
            "explanation": "Evaluates knowledge of data structures in Java collections framework."
        },
        {
            "id": "JAVA_003",
            "skill": "Java",
            "difficulty": "hard",
            "question": "What is the Java Memory Model, and how do volatile and synchronized keywords differ?",
            "expected_concepts": ["Java Memory Model", "Heap vs Thread Stack", "volatile visibility", "synchronized atomicity & locking"],
            "ideal_answer": "The JMM defines how threads interact with main memory and CPU caches. volatile ensures visibility of variable updates across threads by forcing reads/writes from main memory, but doesn't guarantee atomicity. synchronized guarantees both visibility and mutual exclusion (atomicity) by locking an object monitor.",
            "explanation": "Assesses multi-threading and concurrency fundamentals in Java."
        },
        {
            "id": "JAVA_004",
            "skill": "Java",
            "difficulty": "easy",
            "question": "Explain String immutability in Java and why String is immutable.",
            "expected_concepts": ["String pool", "Immutability", "Security", "Thread-safety", "Caching hashcode"],
            "ideal_answer": "String objects cannot be changed once created. Immutability improves security (network connections, file paths), allows string pooling to save memory, makes strings thread-safe without locks, and allows hashcodes to be cached.",
            "explanation": "Fundamental core Java memory management question."
        },
        {
            "id": "JAVA_005",
            "skill": "Java",
            "difficulty": "medium",
            "question": "What is the difference between Abstract Class and Interface in Java 8+?",
            "expected_concepts": ["Multiple inheritance", "default methods", "static methods", "state/instance variables"],
            "ideal_answer": "Abstract classes can hold state (instance variables) and constructors. Interfaces cannot hold state (only static final constants). Interfaces allow multiple inheritance of behavior, and since Java 8 support default and static methods, and Java 9 private methods.",
            "explanation": "Tests Object-Oriented design understanding in Java."
        }
    ],
    "Python": [
        {
            "id": "PY_001",
            "skill": "Python",
            "difficulty": "medium",
            "question": "What is the Global Interpreter Lock (GIL) in Python, and how does it affect multi-threading?",
            "expected_concepts": ["GIL", "CPython", "Thread safety", "CPU-bound vs I/O-bound", "Multiprocessing"],
            "ideal_answer": "The GIL is a mutex in CPython that allows only one thread to execute Python bytecode at a time. It prevents multi-threaded CPU-bound execution across multiple CPU cores. For CPU-intensive tasks, multiprocessing or C extensions are used instead of threading.",
            "explanation": "Critical Python runtime architecture question."
        },
        {
            "id": "PY_002",
            "skill": "Python",
            "difficulty": "medium",
            "question": "Explain Python Generators and the yield keyword. How do they save memory?",
            "expected_concepts": ["Generators", "yield statement", "Iterator protocol", "Lazy evaluation", "Memory efficiency"],
            "ideal_answer": "Generators yield values one at a time on demand rather than loading an entire dataset into memory at once. They implement the iterator protocol lazily, keeping track of execution state between calls.",
            "explanation": "Evaluates Python memory management and iterator concepts."
        },
        {
            "id": "PY_003",
            "skill": "Python",
            "difficulty": "easy",
            "question": "What is the difference between mutable and immutable types in Python? Give examples.",
            "expected_concepts": ["Mutability", "Memory references", "list/dict/set vs tuple/str/int"],
            "ideal_answer": "Mutable objects (lists, dicts, sets) can be modified in place without changing their memory address (id). Immutable objects (strings, tuples, ints, floats) create a new object when modified.",
            "explanation": "Core Python data type semantics."
        },
        {
            "id": "PY_004",
            "skill": "Python",
            "difficulty": "hard",
            "question": "How do decorators work in Python? Write the structure of a decorator accepting arguments.",
            "expected_concepts": ["First-class functions", "Closures", "functools.wraps", "Decorator arguments"],
            "ideal_answer": "Decorators take a function as an argument, extend or modify its behavior inside a wrapper function, and return the wrapper. For decorators accepting arguments, an extra outer function layer receives arguments and returns the decorator function.",
            "explanation": "Assesses functional programming and closure understanding in Python."
        },
        {
            "id": "PY_005",
            "skill": "Python",
            "difficulty": "medium",
            "question": "Explain Python's Memory Management, Reference Counting, and Garbage Collection.",
            "expected_concepts": ["Reference counting", "Cyclic garbage collection", "Generational GC", "gc module"],
            "ideal_answer": "Python uses reference counting as its primary memory management mechanism; when reference count reaches 0, memory is freed immediately. A cyclic garbage collector detects and cleans up circular references using generational collection.",
            "explanation": "Advanced Python runtime internals."
        }
    ],
    "React": [
        {
            "id": "REACT_001",
            "skill": "React",
            "difficulty": "medium",
            "question": "Explain how the Virtual DOM works and the Reconciliation process in React.",
            "expected_concepts": ["Virtual DOM", "Reconciliation", "Diffing algorithm", "Fiber architecture", "Keys"],
            "ideal_answer": "React creates an in-memory lightweight representation of the real DOM called Virtual DOM. When state changes, React creates a new Virtual DOM tree, diffs it against the previous tree using the heuristic Reconciliation algorithm (O(n)), and patches only necessary changes to the real DOM.",
            "explanation": "Core rendering architecture of React."
        },
        {
            "id": "REACT_002",
            "skill": "React",
            "difficulty": "medium",
            "question": "What are the rules of React Hooks, and why must useEffect dependencies be specified accurately?",
            "expected_concepts": ["Call order top-level", "Stale closures", "Dependency array", "Cleanup function"],
            "ideal_answer": "Hooks must only be called at the top level of React functions (not inside loops or conditions) to ensure call order preservation across renders. Missing dependencies in useEffect lead to stale closures where outdated state/props are captured.",
            "explanation": "Assesses hooks state management and lifecycle comprehension."
        },
        {
            "id": "REACT_003",
            "skill": "React",
            "difficulty": "hard",
            "question": "How do useMemo, useCallback, and React.memo optimize component rendering?",
            "expected_concepts": ["Re-rendering prevention", "Memoization", "Referential equality", "Expensive computations"],
            "ideal_answer": "React.memo skips re-rendering a component if props have not changed. useMemo memoizes the result of expensive calculations. useCallback memoizes callback function instances to preserve referential equality across renders.",
            "explanation": "Evaluates React performance optimization techniques."
        },
        {
            "id": "REACT_004",
            "skill": "React",
            "difficulty": "easy",
            "question": "What is State vs Props in React, and what does unidirectional data flow mean?",
            "expected_concepts": ["Component internal state", "Read-only props", "Top-down data flow", "Lifting state up"],
            "ideal_answer": "Props are read-only inputs passed down from parent to child components. State is local component data managed internally that triggers re-renders when updated. Unidirectional data flow means data flows down via props and events bubble up via callbacks.",
            "explanation": "Basic React component architecture."
        },
        {
            "id": "REACT_005",
            "skill": "React",
            "difficulty": "medium",
            "question": "Compare React Context API vs Redux Toolkit for state management.",
            "expected_concepts": ["Prop drilling", "Global state", "Middleware", "Re-render scope", "DevTools"],
            "ideal_answer": "Context API is built-in and ideal for low-frequency global state (theme, user auth). Redux Toolkit is designed for complex, high-frequency state updates with predictable action dispatching, middleware support, and fine-grained selector re-rendering controls.",
            "explanation": "Architectural state management comparison."
        }
    ],
    "Spring Boot": [
        {
            "id": "SB_001",
            "skill": "Spring Boot",
            "difficulty": "medium",
            "question": "Explain Dependency Injection and Inversion of Control (IoC) in Spring Framework.",
            "expected_concepts": ["IoC Container", "Dependency Injection", "@Autowired", "Bean lifecycle", "Loose coupling"],
            "ideal_answer": "Inversion of Control transfers object creation and dependency management responsibility to the Spring IoC container. Dependency Injection (DI) is the pattern where dependencies are injected into a class (via constructor, setter, or field) rather than instantiated directly, achieving loose coupling.",
            "explanation": "Core Spring philosophy and architecture."
        },
        {
            "id": "SB_002",
            "skill": "Spring Boot",
            "difficulty": "medium",
            "question": "What is the difference between @Component, @Service, @Repository, and @Controller annotations?",
            "expected_concepts": ["Stereotype annotations", "Spring Bean registration", "Persistence exception translation"],
            "ideal_answer": "@Component is the generic stereotype annotation. @Service annotates business logic layer classes. @Repository annotates data access layer classes and provides automatic exception translation. @Controller annotates web controller layers.",
            "explanation": "Spring bean stereotype classification."
        },
        {
            "id": "SB_003",
            "skill": "Spring Boot",
            "difficulty": "hard",
            "question": "How does Spring Boot Auto-Configuration work under the hood?",
            "expected_concepts": ["@EnableAutoConfiguration", "@ConditionalOnClass", "spring.factories / AutoConfiguration.imports", "Spring Boot starter"],
            "ideal_answer": "Spring Boot inspects classpath dependencies using @EnableAutoConfiguration and imports auto-configuration classes specified in spring.factories/AutoConfiguration.imports. Conditional annotations (@ConditionalOnClass, @ConditionalOnMissingBean) trigger bean creation only if requirements are satisfied.",
            "explanation": "Advanced Spring Boot framework mechanics."
        }
    ],
    "MySQL": [
        {
            "id": "MYSQL_001",
            "skill": "MySQL",
            "difficulty": "medium",
            "question": "Explain ACID properties in database transactions and how InnoDB implements them.",
            "expected_concepts": ["Atomicity", "Consistency", "Isolation", "Durability", "Undo log", "Redo log", "MVCC"],
            "ideal_answer": "ACID stands for Atomicity, Consistency, Isolation, and Durability. InnoDB achieves Atomicity via Undo logs, Durability via Redo logs/WAL, Isolation via Multi-Version Concurrency Control (MVCC) and locks, and Consistency by enforcing table constraints.",
            "explanation": "Essential database engine principles."
        },
        {
            "id": "MYSQL_002",
            "skill": "MySQL",
            "difficulty": "medium",
            "question": "What is the difference between Clustered Index and Non-Clustered Index in InnoDB?",
            "expected_concepts": ["B+ Tree", "Primary key index", "Secondary index", "Table row data storage"],
            "ideal_answer": "A Clustered Index stores actual table rows in the leaf nodes of the B+ Tree (InnoDB primary key). A Non-Clustered (secondary) Index leaf node stores the primary key value, requiring a secondary lookup to retrieve row data unless covered.",
            "explanation": "Evaluates database indexing internals."
        }
    ],
    "Node.js": [
        {
            "id": "NODE_001",
            "skill": "Node.js",
            "difficulty": "medium",
            "question": "Explain the Node.js Event Loop architecture and phases.",
            "expected_concepts": ["Single-threaded event loop", "Libuv", "Phases (Timers, I/O, Poll, Check)", "Microtasks queue (process.nextTick, Promise)"],
            "ideal_answer": "Node.js uses a single-threaded Event Loop backed by libuv thread pool for non-blocking I/O. The loop moves through phases: Timers, Pending I/O, Poll, Check (setImmediate), and Close callbacks, processing microtask queues between phase transitions.",
            "explanation": "Core Node.js asynchronous architecture."
        }
    ],
    "Data Structures": [
        {
            "id": "DS_001",
            "skill": "Data Structures",
            "difficulty": "medium",
            "question": "Compare Hash Table vs Binary Search Tree in terms of time and space complexity.",
            "expected_concepts": ["Hash table O(1) average", "BST O(log n)", "Worst case O(n)", "In-order traversal", "Range queries"],
            "ideal_answer": "Hash tables offer O(1) average lookup/insert/delete but O(n) worst case on collisions and do not maintain order. Balanced BSTs offer O(log n) guaranteed search/insert/delete and support ordered range queries.",
            "explanation": "Fundamental algorithm complexity evaluation."
        }
    ],
    "System Design": [
        {
            "id": "SYS_001",
            "skill": "System Design",
            "difficulty": "hard",
            "question": "How would you design a distributed caching layer using Redis? Address cache invalidation and cache stampede.",
            "expected_concepts": ["Cache-Aside pattern", "TTL", "Cache stampede / thundering herd", "Mutex locking / probabilistic early expiration", "Consistent hashing"],
            "ideal_answer": "Use Cache-Aside pattern where app reads cache first and populates from DB on miss. Mitigate cache stampede using distributed locks or probabilistic early expiration. Distribute cache keys across nodes using Consistent Hashing.",
            "explanation": "High-level distributed systems scalability design."
        }
    ]
}

# General fallback questions for other skills dynamically generated cleanly
DEFAULT_SKILLS = [
    "C", "C++", "JavaScript", "TypeScript", "Express.js", "Hibernate", "REST API", 
    "Microservices", "PostgreSQL", "MongoDB", "SQL", "Git", "GitHub", "Docker", 
    "AWS", "Azure", "GCP", "HTML", "CSS", "Tailwind CSS", "Algorithms", "OOP", 
    "Operating Systems", "Computer Networks", "DBMS", "Machine Learning", 
    "Deep Learning", "Artificial Intelligence", "Generative AI", "NLP", 
    "Computer Vision", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy"
]

def generate_questions_for_skill(skill_name):
    return [
        {
            "id": f"{skill_name.upper().replace('.', '_').replace(' ', '_')}_001",
            "skill": skill_name,
            "difficulty": "easy",
            "question": f"What are the core features and primary use cases of {skill_name} in modern software engineering?",
            "expected_concepts": [f"{skill_name} fundamentals", "Primary features", "Use cases", "Key advantages"],
            "ideal_answer": f"{skill_name} is used to build robust applications by providing specific tooling, syntax, or infrastructure optimized for efficiency and modularity.",
            "explanation": f"Basic conceptual understanding of {skill_name}."
        },
        {
            "id": f"{skill_name.upper().replace('.', '_').replace(' ', '_')}_002",
            "skill": skill_name,
            "difficulty": "medium",
            "question": f"Explain a major technical challenge or common pitfall when using {skill_name} in production and how to avoid it.",
            "expected_concepts": ["Best practices", "Performance optimization", "Error handling", "Resource management"],
            "ideal_answer": f"Common challenges with {skill_name} include improper resource management or unhandled edge cases. Best practices involve following recommended patterns, monitoring, and proper testing.",
            "explanation": f"Practical production understanding of {skill_name}."
        },
        {
            "id": f"{skill_name.upper().replace('.', '_').replace(' ', '_')}_003",
            "skill": skill_name,
            "difficulty": "hard",
            "question": f"How does {skill_name} handle scalability, concurrency, or internal performance optimization?",
            "expected_concepts": ["Internal architecture", "Scalability", "Concurrency", "Optimization"],
            "ideal_answer": f"{skill_name} handles performance through optimized execution, caching, modular component isolation, or asynchronous resource scheduling.",
            "explanation": f"Deep architectural analysis of {skill_name}."
        }
    ]

def seed():
    print("Seeding question banks...")
    # Seed technical skill questions
    for skill, q_list in SKILL_QUESTIONS.items():
        filename = f"{skill.lower().replace(' ', '').replace('.', '')}.json"
        filepath = os.path.join(SKILLS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(q_list, f, indent=2)
        print(f"  [+] Saved {len(q_list)} questions for {skill}")

    for skill in DEFAULT_SKILLS:
        if skill not in SKILL_QUESTIONS:
            q_list = generate_questions_for_skill(skill)
            filename = f"{skill.lower().replace(' ', '').replace('.', '').replace('/', '')}.json"
            filepath = os.path.join(SKILLS_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(q_list, f, indent=2)

    # Pseudocode questions are stored in backend/data/questions/pseudocode.json as language-independent logic questions
    pseudocode_path = os.path.join(DATA_DIR, "pseudocode.json")
    if os.path.exists(pseudocode_path):
        with open(pseudocode_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  [+] Verified {len(data)} language-independent pseudocode questions in {pseudocode_path}")
    else:
        print(f"  [-] Warning: {pseudocode_path} not found")

if __name__ == "__main__":
    seed()
