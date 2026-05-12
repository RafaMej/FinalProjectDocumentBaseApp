import os
import re
import sqlite3
import unicodedata
from collections import Counter
from nltk.stem.snowball import SnowballStemmer


# Conexión
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "document_base.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Utilidades NLP compartidas
stemmer = SnowballStemmer("spanish")

STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "y", "en", "a",
    "un", "una", "con", "por", "para", "es", "se", "al",
    "lo", "como", "o", "u", "que", "su", "sus", "no", "si",
    "mas", "pero", "son", "han", "hay", "ser", "fue", "era",
    "este", "esta", "esto", "ese", "esa", "entre", "sobre",
    "le", "les", "me", "te", "nos", "ya", "porque", "cuando",
    "también", "tambien", "muy", "más", "mas", "sin", "hasta",
    "desde", "hacia", "ante", "bajo", "durante", "mediante"
}

def preprocess_query(query_text):
    """
    Normalise, tokenise, filter stopwords/short tokens, and stem a raw query.
    Returns a Counter of {stem: frequency}.
    """
    # Minúsculas
    text = query_text.lower()
    # Quitar acentos
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    # Concervar letras y espacios
    text = re.sub(r'[^a-z\s]', ' ', text)
    # Tokenisar y derivar
    tokens = [
        stemmer.stem(t)
        for t in text.split()
        if t not in STOPWORDS and len(t) > 2
    ]
    return Counter(tokens)

def expand_query_with_synonyms(query_counter, cursor):
    """
    For each stem in the query, check the SYNONYMS table.
    If a synonym's canonical form is in the index, add it to the query.
    This implements basic semantic expansion.
    """
    expanded = Counter(query_counter)

    for stem in list(query_counter.keys()):
        # Comprobar si la raíz coincide con alguna entra de sinónimos
        cursor.execute(
            "SELECT canonical FROM SYNONYMS WHERE term = ?",
            (stem,)
        )
        row = cursor.fetchone()
        if row:
            canonical_stem = stemmer.stem(row[0])
            if canonical_stem not in expanded:
                expanded[canonical_stem] = query_counter[stem]

    return expanded

def save_query(cursor, conn, query_text):
    """Persist query to history table."""
    cursor.execute(
        "INSERT INTO QUERIES (query_text) VALUES (?)",
        (query_text,)
    )
    conn.commit()

def validate_document(cursor, doc_name):
    """
    Check that a document exists. Raises ValueError with a clear message if not.
    """
    cursor.execute("SELECT id FROM DOCUMENTS WHERE name = ?", (doc_name,))
    row = cursor.fetchone()
    if row is None:
        available = [r[0] for r in cursor.execute("SELECT name FROM DOCUMENTS ORDER BY name")]
        raise ValueError(
            f"Document '{doc_name}' not found.\n"
            f"Available documents: {', '.join(available)}"
        )
    return row[0]

#  Funcionde de Similitud

# 1. COSINE SIMILARITY — cosulta vs. documentos
def cosine_similarity_query(query_text, top_n=5):
    """
    Retrieve the top_n most relevant documents for a query using cosine similarity.

    Correctness fix: the denominator uses the FULL document vector norm
    and the FULL query vector norm, not just the terms in common.
    This is achieved by computing norms separately from the dot-product join.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    save_query(cursor, conn, query_text)

    query_freqs = preprocess_query(query_text)
    query_freqs = expand_query_with_synonyms(query_freqs, cursor)

    if not query_freqs:
        print("No meaningful terms found in query after preprocessing.")
        conn.close()
        return

    # Insertado de los términos de consulta en una tabla temporal
    cursor.execute("DROP TABLE IF EXISTS TEMP_QUERY")
    cursor.execute("""
        CREATE TEMP TABLE TEMP_QUERY (
            term      TEXT,
            frequency REAL
        )
    """)
    cursor.executemany(
        "INSERT INTO TEMP_QUERY VALUES (?, ?)",
        list(query_freqs.items())
    )

    # Norma de consulta
    query_norm = sum(v ** 2 for v in query_freqs.values()) ** 0.5

    # Producto punto por documento
    sql_dot = """
    SELECT
        d.name,
        SUM(f.frequency * tq.frequency) AS dot_product,
        SQRT(SUM(f.frequency * f.frequency)) AS doc_norm
    FROM FREQUENCIES f
    JOIN DOCUMENTS d  ON f.document_id = d.id
    JOIN TERMS t      ON f.term_id = t.id
    JOIN TEMP_QUERY tq ON t.term = tq.term
    GROUP BY d.name
    """

    rows = cursor.execute(sql_dot).fetchall()

    results = []
    for doc_name, dot, doc_norm_partial in rows:
        # Implementación de norma doc completa
        cursor.execute(
            """
            SELECT SQRT(SUM(f.frequency * f.frequency))
            FROM FREQUENCIES f
            JOIN DOCUMENTS d ON f.document_id = d.id
            WHERE d.name = ?
            """,
            (doc_name,)
        )
        full_doc_norm = cursor.fetchone()[0] or 0.0

        if full_doc_norm > 0 and query_norm > 0:
            cosine = dot / (full_doc_norm * query_norm)
        else:
            cosine = 0.0

        results.append((doc_name, round(cosine, 6)))

    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\nCosine Similarity — top {top_n} results for: '{query_text}'")
    print(f"{'Rank':<5} {'Document':<15} {'Cosine Score':>14}")
    print("-" * 38)
    for rank, (doc, score) in enumerate(results[:top_n], 1):
        print(f"{rank:<5} {doc:<15} {score:>14.6f}")

    conn.close()
    return results[:top_n]



# 2. JACCARD SIMILARITY — entre dos docuemntos
def jaccard_similarity(doc1, doc2):
    """
    Jaccard coefficient = |A ∩ B| / |A ∪ B|
    where A and B are the sets of terms (with frequency > 0) for each document.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    validate_document(cursor, doc1)
    validate_document(cursor, doc2)

    sql = """
    SELECT
        CAST(
            (SELECT COUNT(DISTINCT f1.term_id)
             FROM FREQUENCIES f1
             JOIN FREQUENCIES f2 ON f1.term_id = f2.term_id
             WHERE f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
               AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?))
        AS REAL)
        /
        (SELECT COUNT(DISTINCT term_id)
         FROM (
             SELECT term_id FROM FREQUENCIES
             WHERE document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
             UNION
             SELECT term_id FROM FREQUENCIES
             WHERE document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
         ))
        AS jaccard_score
    """

    cursor.execute(sql, (doc1, doc2, doc1, doc2))
    result = cursor.fetchone()[0] or 0.0

    conn.close()
    return round(result, 6)


# 3. INNER PRODUCT (producto punto) — entre dos documentos
def inner_product(doc1, doc2):
    """
    Raw dot product of frequency vectors.
    Measures absolute co-occurrence weight (not normalized).
    """
    conn   = get_connection()
    cursor = conn.cursor()

    validate_document(cursor, doc1)
    validate_document(cursor, doc2)

    cursor.execute("""
        SELECT SUM(f1.frequency * f2.frequency)
        FROM FREQUENCIES f1
        JOIN FREQUENCIES f2 ON f1.term_id = f2.term_id
        WHERE f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
          AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
    """, (doc1, doc2))

    result = cursor.fetchone()[0] or 0.0
    conn.close()
    return round(result, 6)


# 4. DICE COEFFICIENT — entre dos documentos
def dice_coefficient(doc1, doc2):
    """
    Dice = 2 * |A ∩ B| / (|A| + |B|)
    where |A| is the number of distinct terms in document A.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    validate_document(cursor, doc1)
    validate_document(cursor, doc2)

    cursor.execute("""
        SELECT COUNT(DISTINCT f1.term_id)
        FROM FREQUENCIES f1
        JOIN FREQUENCIES f2 ON f1.term_id = f2.term_id
        WHERE f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
          AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
    """, (doc1, doc2))
    intersection = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT COUNT(DISTINCT term_id) FROM FREQUENCIES WHERE document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)",
        (doc1,)
    )
    size_a = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT COUNT(DISTINCT term_id) FROM FREQUENCIES WHERE document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)",
        (doc2,)
    )
    size_b = cursor.fetchone()[0] or 0

    dice = (2 * intersection / (size_a + size_b)) if (size_a + size_b) > 0 else 0.0
    conn.close()
    return round(dice, 6)


# Funciones de desimilitud

# 5. EUCLIDEAN DISTANCE — consulta vs. documentos
def euclidean_distance_query(query_text, top_n=5):
    """
    Rank documents by Euclidean distance to the query vector (lower = more relevant).

    Fix: avoids the COMPLETE CROSS JOIN. Uses TERMS as the universe
    and LEFT JOINs independently for document and query vectors.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    save_query(cursor, conn, query_text)

    query_freqs = preprocess_query(query_text)
    query_freqs = expand_query_with_synonyms(query_freqs, cursor)

    if not query_freqs:
        print("No meaningful terms found in query after preprocessing.")
        conn.close()
        return

    cursor.execute("DROP TABLE IF EXISTS TEMP_QUERY_EUCL")
    cursor.execute("""
        CREATE TEMP TABLE TEMP_QUERY_EUCL (
            term      TEXT,
            frequency REAL
        )
    """)
    cursor.executemany(
        "INSERT INTO TEMP_QUERY_EUCL VALUES (?, ?)",
        list(query_freqs.items())
    )

    # Juso de LEFT JOIN
    sql = """
    SELECT
        d.name,
        SQRT(SUM(
            (COALESCE(f.frequency, 0) - COALESCE(tq.frequency, 0)) *
            (COALESCE(f.frequency, 0) - COALESCE(tq.frequency, 0))
        )) AS euclidean_distance
    FROM DOCUMENTS d
    CROSS JOIN TERMS t
    LEFT JOIN FREQUENCIES f
        ON f.document_id = d.id AND f.term_id = t.id
    LEFT JOIN TEMP_QUERY_EUCL tq
        ON tq.term = t.term
    GROUP BY d.name
    ORDER BY euclidean_distance ASC
    """

    rows = cursor.execute(sql).fetchall()
    results = [(doc, round(dist, 6)) for doc, dist in rows]

    print(f"\nEuclidean Distance — top {top_n} results for: '{query_text}'")
    print(f"{'Rank':<5} {'Document':<15} {'Distance':>12}")
    print("-" * 36)
    for rank, (doc, dist) in enumerate(results[:top_n], 1):
        print(f"{rank:<5} {doc:<15} {dist:>12.6f}")

    conn.close()
    return results[:top_n]


# 6. MANHATTAN DISTANCE — consulta vs. docuemntos
def manhattan_distance_query(query_text, top_n=5):
    """
    L1 distance: SUM(|doc_freq - query_freq|) for all terms.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    save_query(cursor, conn, query_text)

    query_freqs = preprocess_query(query_text)
    query_freqs = expand_query_with_synonyms(query_freqs, cursor)

    if not query_freqs:
        print("No meaningful terms found in query after preprocessing.")
        conn.close()
        return

    cursor.execute("DROP TABLE IF EXISTS TEMP_QUERY_MANH")
    cursor.execute("""
        CREATE TEMP TABLE TEMP_QUERY_MANH (
            term      TEXT,
            frequency REAL
        )
    """)
    cursor.executemany(
        "INSERT INTO TEMP_QUERY_MANH VALUES (?, ?)",
        list(query_freqs.items())
    )

    sql = """
    SELECT
        d.name,
        SUM(
            ABS(COALESCE(f.frequency, 0) - COALESCE(tq.frequency, 0))
        ) AS manhattan_distance
    FROM DOCUMENTS d
    CROSS JOIN TERMS t
    LEFT JOIN FREQUENCIES f
        ON f.document_id = d.id AND f.term_id = t.id
    LEFT JOIN TEMP_QUERY_MANH tq
        ON tq.term = t.term
    GROUP BY d.name
    ORDER BY manhattan_distance ASC
    """

    rows = cursor.execute(sql).fetchall()
    results = [(doc, round(dist, 6)) for doc, dist in rows]

    print(f"\nManhattan Distance — top {top_n} results for: '{query_text}'")
    print(f"{'Rank':<5} {'Document':<15} {'Distance':>12}")
    print("-" * 36)
    for rank, (doc, dist) in enumerate(results[:top_n], 1):
        print(f"{rank:<5} {doc:<15} {dist:>12.6f}")

    conn.close()
    return results[:top_n]



# Búsqueda semántica
def semantic_search(query_text, top_n=5):
    """
    True LSI semantic search:
      1. Preprocess + expand the query into a raw frequency vector q
      2. Project q into LSI space: q_lsi = q_vec @ V^T^T / Sigma
         (equivalent to: q_lsi[k] = dot(q_vec, Vt[k, :]) / sigma[k])
      3. Compute cosine similarity between q_lsi and each document's LSI vector
      4. Rank by descending similarity

    This is the standard Folding-In method for LSI retrieval.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    save_query(cursor, conn, query_text)

    # Comprobación de que LSI se calculó
    cursor.execute("SELECT COUNT(*) FROM LSI_VECTORS")
    if cursor.fetchone()[0] == 0:
        print("LSI vectors not found. Please run lsi.py first (option 1).")
        conn.close()
        return

    cursor.execute("SELECT COUNT(*) FROM LSI_SIGMA")
    if cursor.fetchone()[0] == 0:
        print("Singular values not found. Please re-run lsi.py.")
        conn.close()
        return

    # Carga de Sigma y V^T desde la BD
    cursor.execute("SELECT component, singular_value FROM LSI_SIGMA ORDER BY component")
    sigma_rows = cursor.fetchall()
    sigma = {row[0]: row[1] for row in sigma_rows}
    k = len(sigma)

    cursor.execute("""
        SELECT t.term, lv.component, lv.value
        FROM LSI_VT lv
        JOIN TERMS t ON lv.term_id = t.id
        ORDER BY lv.component
    """)
    vt_rows = cursor.fetchall()

    # Construcción de mapeo 
    vt_map = {}
    for term, component, value in vt_rows:
        if term not in vt_map:
            vt_map[term] = {}
        vt_map[term][component] = value

    # Preoporcesamiento y expansión de la consulta
    query_freqs = preprocess_query(query_text)
    query_freqs = expand_query_with_synonyms(query_freqs, cursor)

    if not query_freqs:
        print("No meaningful terms found after preprocessing.")
        conn.close()
        return

    # Consulta del proyecto en el espacio LSI 
    # q_lsi[component] = sum_over_terms(q_freq[term] * Vt[component][term]) / sigma[component]
    q_lsi = {}
    for component in range(k):
        dot = sum(
            query_freqs.get(term, 0) * vt_map.get(term, {}).get(component, 0.0)
            for term in vt_map
        )
        sv = sigma[component]
        q_lsi[component] = dot / sv if sv != 0 else 0.0

    q_norm = sum(v ** 2 for v in q_lsi.values()) ** 0.5

    if q_norm == 0:
        print("Query projects to zero vector in LSI space. Try different terms.")
        conn.close()
        return

    # Carga de documentos de vectores LSI
    cursor.execute("""
        SELECT d.name, l.component, l.value
        FROM LSI_VECTORS l
        JOIN DOCUMENTS d ON l.document_id = d.id
        ORDER BY d.name, l.component
    """)
    doc_rows = cursor.fetchall()

    doc_vectors = {}
    for doc_name, component, value in doc_rows:
        if doc_name not in doc_vectors:
            doc_vectors[doc_name] = {}
        doc_vectors[doc_name][component] = value

    # Similitud del coseno entre q_lsi y cada vector del documento
    results = []
    for doc_name, doc_vec in doc_vectors.items():
        dot = sum(q_lsi.get(c, 0.0) * doc_vec.get(c, 0.0) for c in range(k))
        doc_norm = sum(v ** 2 for v in doc_vec.values()) ** 0.5
        cosine = dot / (q_norm * doc_norm) if doc_norm > 0 else 0.0
        results.append((doc_name, round(cosine, 6)))

    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\nLSI Semantic Search — top {top_n} results for: '{query_text}'")
    print(f"(Query projected into {k}-dimensional LSI space)")
    print(f"{'Rank':<5} {'Document':<15} {'Semantic Score':>16}")
    print("-" * 40)
    for rank, (doc, score) in enumerate(results[:top_n], 1):
        print(f"{rank:<5} {doc:<15} {score:>16.6f}")

    conn.close()
    return results[:top_n]


#  Comparación entre documentos (D1 vs D2) — uso de todas las métricas
def compare_documents(doc1, doc2):
    """
    Compare two documents using all implemented similarity and distance metrics.
    Validates document existence before any computation.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Validar existencia de ambos documentos
    try:
        validate_document(cursor, doc1)
        validate_document(cursor, doc2)
    except ValueError as e:
        print(f"\nError: {e}")
        conn.close()
        return
    finally:
        conn.close()

    print(f"\n{'=' * 50}")
    print(f"DOCUMENT COMPARISON: {doc1}  vs  {doc2}")
    print(f"{'=' * 50}")

    # Metricas de similitud
    print("\nSimilarity functions (higher = more similar):")

    # Cosine Similarity (doc vs doc)
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            SUM(f1.frequency * f2.frequency) * 1.0
            / (
                SQRT(SUM(f1.frequency * f1.frequency)) *
                SQRT(SUM(f2.frequency * f2.frequency))
              )
            AS cosine_similarity
        FROM FREQUENCIES f1
        JOIN FREQUENCIES f2 ON f1.term_id = f2.term_id
        WHERE f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
          AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
    """, (doc1, doc2))
    cosine_val = round(cursor.fetchone()[0] or 0.0, 6)
    conn.close()

    jaccard_val = jaccard_similarity(doc1, doc2)
    inner_val   = inner_product(doc1, doc2)
    dice_val    = dice_coefficient(doc1, doc2)

    print(f"  Cosine similarity : {cosine_val:.6f}")
    print(f"  Jaccard coefficient: {jaccard_val:.6f}")
    print(f"  Dice coefficient  : {dice_val:.6f}")
    print(f"  Inner product     : {inner_val:.6f}")

    # Métricas de Desimilitud
    print("\nDissimilarity functions (lower = more similar):")

    conn   = get_connection()
    cursor = conn.cursor()

    # Euclidean Distance (doc vs doc)
    cursor.execute("""
        SELECT SQRT(SUM(
            (COALESCE(f1.frequency, 0) - COALESCE(f2.frequency, 0)) *
            (COALESCE(f1.frequency, 0) - COALESCE(f2.frequency, 0))
        ))
        FROM TERMS t
        LEFT JOIN FREQUENCIES f1
            ON t.id = f1.term_id
           AND f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
        LEFT JOIN FREQUENCIES f2
            ON t.id = f2.term_id
           AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
    """, (doc1, doc2))
    eucl_val = round(cursor.fetchone()[0] or 0.0, 6)

    # Manhattan Distance (doc vs doc)
    cursor.execute("""
        SELECT SUM(ABS(COALESCE(f1.frequency, 0) - COALESCE(f2.frequency, 0)))
        FROM TERMS t
        LEFT JOIN FREQUENCIES f1
            ON t.id = f1.term_id
           AND f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
        LEFT JOIN FREQUENCIES f2
            ON t.id = f2.term_id
           AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
    """, (doc1, doc2))
    manh_val = round(cursor.fetchone()[0] or 0.0, 6)

    conn.close()

    print(f"  Euclidean distance : {eucl_val:.6f}")
    print(f"  Manhattan distance : {manh_val:.6f}")

    print(f"\n{'=' * 50}")


# Pruebas
if __name__ == "__main__":

    print("\n--- Test: cosine similarity query ---")
    cosine_similarity_query("ansiedad exámenes universitarios", top_n=5)

    print("\n--- Test: euclidean distance query ---")
    euclidean_distance_query("depresión apoyo social", top_n=5)

    print("\n--- Test: manhattan distance query ---")
    manhattan_distance_query("estrés académico rendimiento", top_n=5)

    print("\n--- Test: semantic search ---")
    semantic_search("estrategias afrontamiento bienestar", top_n=5)

    print("\n--- Test: compare documents ---")
    compare_documents("doc1.txt", "doc2.txt")