import os
import sqlite3
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "data", "document_base.db")

# Conexión a la BD
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Carga de toda la Matriz de Frecuencia
query = """
SELECT document_name, term, frequency
FROM COMPLETE
"""

rows = pd.read_sql_query(query, conn)

matrix = rows.pivot_table(
    index='document_name',
    columns='term',
    values='frequency',
    fill_value=0
)

n_docs, n_terms = matrix.shape
print(f"\nFrequency matrix shape: {n_docs} documents x {n_terms} terms")


max_k = min(n_docs - 1, n_terms - 1)

# Ejecución de una vista previa de SVD
# muestra la varianza explicada por componente
preview_svd = TruncatedSVD(n_components=max_k, random_state=42)
preview_svd.fit(matrix.values)

cumulative_variance = np.cumsum(preview_svd.explained_variance_ratio_)

print("\nExplained variance by number of components:")
print(f"{'k':>4}  {'Cumulative variance':>20}")
for i, cv in enumerate(cumulative_variance, start=1):
    marker = " <-- recommended" if abs(cv - 0.80) < 0.07 and i <= 6 else ""
    print(f"{i:>4}  {cv:>19.1%}{marker}")

print(f"\nMax allowed k: {max_k}")
k = int(input(f"\nHow many LSI components do you want? (1-{max_k}): "))
k = max(1, min(k, max_k))

# Aplicar LSI (SVD)
svd = TruncatedSVD(n_components=k, random_state=42)
U_sigma = svd.fit_transform(matrix.values)      # shape: (n_docs, k)
sigma   = svd.singular_values_                  # shape: (k,)
Vt      = svd.components_                       # shape: (k, n_terms)

explained = svd.explained_variance_ratio_.sum()

print(f"\nLSI PROCESS COMPLETED")
print(f"Original dimensions:  {matrix.shape}")
print(f"Reduced dimensions:   {U_sigma.shape}")
print(f"Variance explained:   {explained:.1%}")

documents = list(matrix.index)
terms     = list(matrix.columns)

print("\nSample LSI vectors (first 3 documents):")
for i, doc in enumerate(documents[:3]):
    print(f"  {doc} -> {np.round(U_sigma[i], 4)}")

# Vectores de documentos LSI persistentes (U*Sigma)
cursor.execute("DELETE FROM LSI_VECTORS")
conn.commit()

for doc_idx, doc_name in enumerate(documents):

    cursor.execute("SELECT id FROM DOCUMENTS WHERE name = ?", (doc_name,))
    row = cursor.fetchone()

    if row is None:
        print(f"  Warning: '{doc_name}' not found in DOCUMENTS, skipping.")
        continue

    document_id = row[0]

    for component in range(k):
        cursor.execute(
            "INSERT INTO LSI_VECTORS (document_id, component, value) VALUES (?, ?, ?)",
            (document_id, component, float(U_sigma[doc_idx][component]))
        )

conn.commit()
print(f"\nDocument vectors stored: {len(documents)} docs x {k} components")

# Valores singulares persistentes (Sigma)
cursor.execute("DELETE FROM LSI_SIGMA")
conn.commit()

for idx, sv in enumerate(sigma):
    cursor.execute(
        "INSERT INTO LSI_SIGMA (component, singular_value) VALUES (?, ?)",
        (idx, float(sv))
    )

conn.commit()
print(f"Singular values stored: {k} values")

# Matriz PERSIST V^T (componente de término)
cursor.execute("DELETE FROM LSI_VT")
conn.commit()

for term_idx, term_name in enumerate(terms):

    cursor.execute("SELECT id FROM TERMS WHERE term = ?", (term_name,))
    row = cursor.fetchone()

    if row is None:
        continue

    term_id = row[0]

    for component in range(k):
        cursor.execute(
            "INSERT INTO LSI_VT (term_id, component, value) VALUES (?, ?, ?)",
            (term_id, component, float(Vt[component][term_idx]))
        )

conn.commit()
print(f"V^T matrix stored: {len(terms)} terms x {k} components")

# Cerrar conexión
conn.close()
print("\nLSI indexing complete. Semantic queries are now available.")