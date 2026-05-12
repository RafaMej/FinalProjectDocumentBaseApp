import subprocess
import sys
import os

from queries import (
    cosine_similarity_query,
    euclidean_distance_query,
    manhattan_distance_query,
    semantic_search,
    compare_documents,
    jaccard_similarity,
    dice_coefficient,
    inner_product,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MENU = """
╔══════════════════════════════════════════════╗
║         DOCUMENT BASE SYSTEM — LSI           ║
║   Topic: Mental Health in University Students║
╠══════════════════════════════════════════════╣
║  SETUP                                       ║
║  1. Initialize database                      ║
║  2. Run preprocessing (NLP pipeline)         ║
║  3. Generate LSI (SVD indexing)              ║
╠══════════════════════════════════════════════╣
║  SIMILARITY QUERIES (higher = more similar)  ║
║  4. Cosine similarity  (query → documents)   ║
║  5. Jaccard coefficient (doc vs doc)         ║
║  6. Dice coefficient    (doc vs doc)         ║
║  7. Inner product       (doc vs doc)         ║
╠══════════════════════════════════════════════╣
║  DISSIMILARITY QUERIES (lower = more similar)║
║  8. Euclidean distance  (query → documents)  ║
║  9. Manhattan distance  (query → documents)  ║
╠══════════════════════════════════════════════╣
║  COMBINED & SEMANTIC                         ║
║  10. Compare two documents (all metrics)     ║
║  11. LSI semantic search  (query → concepts) ║
╠══════════════════════════════════════════════╣
║  0. Exit                                     ║
╚══════════════════════════════════════════════╝
"""

SRC_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(script_name):
    """Run a sibling script in the same src/ directory."""
    script_path = os.path.join(SRC_DIR, script_name)
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"\nScript '{script_name}' finished with errors (code {result.returncode}).")


def get_two_docs():
    """Prompt for two document names and return them."""
    doc1 = input("Enter first document name  (e.g. doc1.txt): ").strip()
    doc2 = input("Enter second document name (e.g. doc2.txt): ").strip()
    return doc1, doc2


def get_query():
    return input("Enter query text: ").strip()


def get_top_n():
    try:
        n = int(input("How many top results? [default 5]: ").strip() or "5")
        return max(1, n)
    except ValueError:
        return 5


while True:

    print(MENU)
    option = input("Select option: ").strip()

    if option == "1":
        run_script("database.py")

    elif option == "2":
        run_script("preprocessing.py")

    elif option == "3":
        run_script("lsi.py")

    elif option == "4":
        q = get_query()
        n = get_top_n()
        cosine_similarity_query(q, top_n=n)

    elif option == "5":
        doc1, doc2 = get_two_docs()
        try:
            score = jaccard_similarity(doc1, doc2)
            print(f"\nJaccard coefficient: {doc1} vs {doc2} = {score:.6f}")
        except ValueError as e:
            print(f"\nError: {e}")

    elif option == "6":
        doc1, doc2 = get_two_docs()
        try:
            score = dice_coefficient(doc1, doc2)
            print(f"\nDice coefficient: {doc1} vs {doc2} = {score:.6f}")
        except ValueError as e:
            print(f"\nError: {e}")

    elif option == "7":
        doc1, doc2 = get_two_docs()
        try:
            score = inner_product(doc1, doc2)
            print(f"\nInner product: {doc1} vs {doc2} = {score:.6f}")
        except ValueError as e:
            print(f"\nError: {e}")

    elif option == "8":
        q = get_query()
        n = get_top_n()
        euclidean_distance_query(q, top_n=n)

    elif option == "9":
        q = get_query()
        n = get_top_n()
        manhattan_distance_query(q, top_n=n)

    elif option == "10":
        doc1, doc2 = get_two_docs()
        compare_documents(doc1, doc2)

    elif option == "11":
        q = get_query()
        n = get_top_n()
        semantic_search(q, top_n=n)

    elif option == "0":
        print("Exiting system. Goodbye.")
        break

    else:
        print("Invalid option. Please choose a number from the menu.")