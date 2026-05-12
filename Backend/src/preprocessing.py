import os
import re
import math
import unicodedata
from collections import Counter
from nltk.stem.snowball import SnowballStemmer

# ================================================================
# STOP LIST
# Lista de palabras basada en salud mental
# ================================================================
STOPWORDS = {
    # Artículos
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    # Preprosiciones
    "de", "del", "en", "a", "al", "con", "por", "para", "ante",
    "bajo", "cabe", "contra", "desde", "durante", "entre", "hacia",
    "hasta", "mediante", "sin", "sobre", "tras",
    # Conjunciones
    "y", "e", "o", "u", "ni", "pero", "sino", "aunque", "porque",
    "pues", "ya", "que", "si", "como", "cuando", "donde", "mientras",
    # Pronombres
    "se", "lo", "la", "le", "les", "me", "te", "nos", "os",
    "su", "sus", "su", "sus", "mi", "mis", "tu", "tus",
    "este", "esta", "esto", "estos", "estas",
    "ese", "esa", "eso", "esos", "esas",
    "aquel", "aquella", "aquello",
    # Verbos comunes (auxiliares)
    "es", "son", "ser", "fue", "era", "eran", "han", "hay",
    "ser", "estar", "siendo", "sido",
    # Adervios
    "no", "si", "mas", "más", "muy", "también", "tambien",
    "así", "asi", "ya", "aún", "aun", "solo", "sólo", "tan",
}

# SUFFIX LIST
SUFFIX_LIST = [
    # Sufijos que forman sustantivos
    "ción", "cion", "sión", "sion",     # acción, depresión
    "idad", "dad",                       # ansiedad, salud
    "ismo",                              # mecanismo
    "ista",                              # especialista
    "miento", "amiento",                 # afrontamiento
    "tura", "ura",                       # estructura
    # Sufijos que forman adjetivos
    "ivo", "iva",                        # cognitivo, efectiva
    "oso", "osa",                        # ansioso
    "al", "ial",                         # social, emocional
    "ico", "ica",                        # psicológico, académica
    # Sufijos que forman verbos
    "ar", "er", "ir",                    # infinitives
    "ando", "endo",                      # gerunds
    "ado", "ido",                        # participles
]

# STEMMER
stemmer = SnowballStemmer("spanish")


# Normalización de los textos
def normalize_text(text):
    """
    Lowercase, remove accents, strip non-alphabetic characters.
    """
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z\s]', ' ', text)
    return text


def preprocess_text(text):
    """
    Full NLP pipeline:
      1. Normalise (lowercase, remove accents, strip punctuation)
      2. Tokenise by whitespace
      3. Remove stopwords and short tokens (len <= 2)
      4. Apply Snowball stemmer

    Returns a list of stems (with repetitions preserved for frequency counting).
    """
    text   = normalize_text(text)
    tokens = text.split()
    stems  = [
        stemmer.stem(token)
        for token in tokens
        if token not in STOPWORDS and len(token) > 2
    ]
    return stems


# Ponderación TF-DF
def compute_tfidf(doc_term_counts, all_doc_counts):
    """
    Compute TF-IDF weights for each (document, term) pair.

    TF  = frequency of term in document / total terms in document
    IDF = log(N / df_t)   where N = number of documents,
                                df_t = number of docs containing term t

    Returns: dict { doc_name: { term: tfidf_weight } }
    """
    N = len(doc_term_counts)
    if N == 0:
        return {}

    # Frecuencia de documentos por período
    df = Counter()
    for counts in doc_term_counts.values():
        for term in counts:
            df[term] += 1

    tfidf = {}
    for doc_name, counts in doc_term_counts.items():
        total_terms = sum(counts.values())
        tfidf[doc_name] = {}
        for term, count in counts.items():
            tf  = count / total_terms if total_terms > 0 else 0
            idf = math.log(N / df[term]) if df[term] > 0 else 0
            tfidf[doc_name][term] = round(tf * idf, 6)

    return tfidf



# Procesamiento de documentos
def process_documents(input_folder, output_folder):
    """
    Process all .txt documents in input_folder:
      - Apply NLP pipeline (normalise, tokenise, remove stopwords, stem)
      - Write processed token list to output_folder
      - Print basic statistics
    """
    os.makedirs(output_folder, exist_ok=True)

    doc_term_counts = {}

    for filename in sorted(os.listdir(input_folder)):

        if not filename.endswith('.txt'):
            continue

        filepath = os.path.join(input_folder, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        stems = preprocess_text(raw_text)
        doc_term_counts[filename] = Counter(stems)

        output_path = os.path.join(output_folder, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(' '.join(stems))

    # Print de estadísticas del corpus
    all_terms = set()
    for counts in doc_term_counts.values():
        all_terms.update(counts.keys())

    print(f"\nPreprocessing completed")
    print(f"  Documents processed : {len(doc_term_counts)}")
    print(f"  Unique stems        : {len(all_terms)}")
    print(f"  Stop words removed  : {len(STOPWORDS)}")
    print(f"  Suffix rules defined: {len(SUFFIX_LIST)}")

    # Calculo del resumen TF-DF
    tfidf = compute_tfidf(doc_term_counts, doc_term_counts)
    print(f"\nTop-5 TF-IDF terms per document (sample: first 3 docs):")
    for doc_name in sorted(doc_term_counts.keys())[:3]:
        top_terms = sorted(
            tfidf[doc_name].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        print(f"  {doc_name}: {[t for t, _ in top_terms]}")

    return doc_term_counts


# Punto de entrada independiente
if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    docs_path      = os.path.join(BASE_DIR, "docs")
    processed_path = os.path.join(BASE_DIR, "processed")

    process_documents(docs_path, processed_path)