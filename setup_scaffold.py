import os

base = r"C:\Users\sagni\.gemini\antigravity\scratch\tennis-intelligence-platform"

dirs = [
    r"backend\app\api\v1",
    r"backend\app\core",
    r"backend\app\models",
    r"backend\app\schemas",
    r"backend\app\services",
    r"backend\app\repositories",
    r"backend\app\database",
    r"frontend\src\components\ui",
    r"frontend\src\components\charts",
    r"frontend\src\components\players",
    r"frontend\src\pages",
    r"frontend\src\layouts",
    r"frontend\src\services",
    r"frontend\src\hooks",
    r"frontend\src\assets",
    r"frontend\src\styles",
    r"data-engineering\extraction",
    r"data-engineering\transformation",
    r"data-engineering\validation",
    r"data-engineering\pipelines",
    r"data-engineering\sample_data",
    r"machine-learning\notebooks",
    r"machine-learning\preprocessing",
    r"machine-learning\models",
    r"machine-learning\evaluation",
    r"sql\migrations",
    r"tests\unit",
    r"tests\integration",
    r"docs\architecture",
    r"docs\diagrams",
    r"docs\screenshots",
    r".github\workflows",
    r"module1-foundation"
]

for d in dirs:
    full_path = os.path.join(base, d)
    os.makedirs(full_path, exist_ok=True)

print("Scaffold initialized successfully.")
