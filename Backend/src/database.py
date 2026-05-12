import os
import sqlite3
from collections import Counter

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH       = os.path.join(BASE_DIR, "data", "document_base.db")
PROCESSED_PATH = os.path.join(BASE_DIR, "processed")

# Conexión
conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Habilitar la aplicación de llves foráneas 
cursor.execute("PRAGMA foreign_keys = ON")

# Eliminar Tablas Existentes
cursor.executescript("""
DROP VIEW  IF EXISTS COMPLETE;
DROP TABLE IF EXISTS LSI_VT;
DROP TABLE IF EXISTS LSI_SIGMA;
DROP TABLE IF EXISTS LSI_VECTORS;
DROP TABLE IF EXISTS FREQUENCIES;
DROP TABLE IF EXISTS SYNONYMS;
DROP TABLE IF EXISTS STEMS;
DROP TABLE IF EXISTS QUERIES;
DROP TABLE IF EXISTS TERMS;
DROP TABLE IF EXISTS DOCUMENTS;
""")
conn.commit()

# Crear Tablas
cursor.executescript("""
CREATE TABLE DOCUMENTS (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    UNIQUE NOT NULL
);

CREATE TABLE TERMS (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT    UNIQUE NOT NULL
);

-- Explicit stem -> canonical form mapping (suffix list concept)
CREATE TABLE STEMS (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    stem      TEXT    UNIQUE NOT NULL,
    canonical TEXT    NOT NULL
);

-- Synonym groups: each row maps a term to its canonical synonym group
CREATE TABLE SYNONYMS (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    term      TEXT    UNIQUE NOT NULL,
    canonical TEXT    NOT NULL
);

-- Raw term frequency matrix (sparse representation)
CREATE TABLE FREQUENCIES (
    document_id INTEGER NOT NULL,
    term_id     INTEGER NOT NULL,
    frequency   INTEGER NOT NULL,
    PRIMARY KEY (document_id, term_id),
    FOREIGN KEY (document_id) REFERENCES DOCUMENTS(id),
    FOREIGN KEY (term_id)     REFERENCES TERMS(id)
);

-- Query history
CREATE TABLE QUERIES (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT    NOT NULL,
    timestamp  TEXT    DEFAULT (datetime('now'))
);

-- LSI document vectors: U * Sigma matrix (one row per doc per component)
CREATE TABLE LSI_VECTORS (
    document_id INTEGER NOT NULL,
    component   INTEGER NOT NULL,
    value       REAL    NOT NULL,
    PRIMARY KEY (document_id, component),
    FOREIGN KEY (document_id) REFERENCES DOCUMENTS(id)
);

-- LSI singular values (Sigma diagonal)
CREATE TABLE LSI_SIGMA (
    component      INTEGER PRIMARY KEY,
    singular_value REAL    NOT NULL
);

-- LSI V^T matrix (term-to-concept mapping, needed to project queries)
CREATE TABLE LSI_VT (
    term_id   INTEGER NOT NULL,
    component INTEGER NOT NULL,
    value     REAL    NOT NULL,
    PRIMARY KEY (term_id, component),
    FOREIGN KEY (term_id) REFERENCES TERMS(id)
);
""")
conn.commit()

# Indices de rendimiento
cursor.executescript("""
CREATE INDEX IF NOT EXISTS idx_freq_doc  ON FREQUENCIES(document_id);
CREATE INDEX IF NOT EXISTS idx_freq_term ON FREQUENCIES(term_id);
CREATE INDEX IF NOT EXISTS idx_lsi_doc   ON LSI_VECTORS(document_id);
CREATE INDEX IF NOT EXISTS idx_vt_term   ON LSI_VT(term_id);
""")
conn.commit()

# -----------------------------
# Tabla de Sinónimos
#  Dominio: salud mental universitaria
#  Se agrupan palabras que transmiten mismo concepto semantico
# -----------------------------
SYNONYM_GROUPS = {
    "ansiedad":    ["angustia", "inquietud", "tension", "nerviosismo"],
    "depresion":   ["tristeza", "melancolía", "abatimiento", "desesperanza"],
    "estres":      ["agotamiento", "sobrecarga", "presion", "burnout"],
    "bienestar":   ["salud", "equilibrio", "satisfaccion"],
    "afrontamiento": ["coping", "gestion", "manejo", "regulacion"],
    "apoyo":       ["soporte", "ayuda", "respaldo", "acompanamiento"],
    "rendimiento": ["desempeno", "productividad", "resultado"],
    "tratamiento": ["terapia", "intervencion", "programa"],
}

synonym_rows = []
for canonical, synonyms in SYNONYM_GROUPS.items():
    synonym_rows.append((canonical, canonical))          # canonical maps to itself
    for syn in synonyms:
        synonym_rows.append((syn, canonical))

cursor.executemany(
    "INSERT OR IGNORE INTO SYNONYMS (term, canonical) VALUES (?, ?)",
    synonym_rows
)
conn.commit()
print(f"Synonym table populated: {len(synonym_rows)} entries across {len(SYNONYM_GROUPS)} groups")


# Carga de Documentos Porcesados
all_tokens_per_doc = {}

for filename in sorted(os.listdir(PROCESSED_PATH)):

    if not filename.endswith('.txt'):
        continue

    filepath = os.path.join(PROCESSED_PATH, filename)

    with open(filepath, 'r', encoding='utf-8') as f:
        tokens = f.read().split()

    all_tokens_per_doc[filename] = Counter(tokens)

# Recopilar todos los términos únicos en todos los documento
all_terms = set()
for counter in all_tokens_per_doc.values():
    all_terms.update(counter.keys())

# Insersión de todos los términos al mismo tiempo
cursor.executemany(
    "INSERT OR IGNORE INTO TERMS (term) VALUES (?)",
    [(t,) for t in sorted(all_terms)]
)
conn.commit()

# Construcción de búsqueda de término
cursor.execute("SELECT term, id FROM TERMS")
term_to_id = {row[0]: row[1] for row in cursor.fetchall()}

# Insertado de docuemntos y frecuencias
for filename, counter in all_tokens_per_doc.items():

    cursor.execute("INSERT INTO DOCUMENTS (name) VALUES (?)", (filename,))
    conn.commit()

    cursor.execute("SELECT id FROM DOCUMENTS WHERE name = ?", (filename,))
    document_id = cursor.fetchone()[0]

    freq_rows = [
        (document_id, term_to_id[term], freq)
        for term, freq in counter.items()
        if term in term_to_id
    ]

    cursor.executemany(
        "INSERT INTO FREQUENCIES (document_id, term_id, frequency) VALUES (?, ?, ?)",
        freq_rows
    )

conn.commit()

# Vista Completa
cursor.executescript("""
DROP VIEW IF EXISTS COMPLETE;

CREATE VIEW COMPLETE AS
SELECT
    d.id   AS document_id,
    d.name AS document_name,
    t.id   AS term_id,
    t.term AS term,
    COALESCE(f.frequency, 0) AS frequency
FROM DOCUMENTS d
CROSS JOIN TERMS t
LEFT JOIN FREQUENCIES f
    ON d.id = f.document_id
   AND t.id = f.term_id;
""")
conn.commit()

# Resumen
cursor.execute("SELECT COUNT(*) FROM DOCUMENTS")
n_docs = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM TERMS")
n_terms = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM FREQUENCIES")
n_freqs = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM SYNONYMS")
n_syns = cursor.fetchone()[0]

print(f"\nDatabase initialized successfully")
print(f"  Documents : {n_docs}")
print(f"  Terms     : {n_terms}")
print(f"  Frequencies: {n_freqs} (non-zero entries)")
print(f"  Synonyms  : {n_syns} entries")
print(f"\nRun lsi.py next to build LSI vectors.")

conn.close()