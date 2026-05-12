// Models.swift
// Pure data structures — no business logic, no UI dependencies.

import Foundation

// MARK: - Document

struct DocumentItem: Identifiable, Hashable {
    let id = UUID()
    let name: String   // e.g. "doc1.txt"

    /// Numeric index extracted from filename for display/sorting.
    var index: Int {
        Int(name.filter(\.isNumber)) ?? 0
    }
}

// MARK: - Search

enum QueryMode: String, CaseIterable, Identifiable {
    case cosine    = "Cosine Similarity"
    case euclidean = "Euclidean Distance"
    case manhattan = "Manhattan Distance"
    case semantic  = "LSI Semantic Search"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .cosine:    return "waveform.path.ecg"
        case .euclidean: return "ruler"
        case .manhattan: return "map"
        case .semantic:  return "brain.head.profile"
        }
    }

    /// Whether lower score means more similar (distance metrics).
    var isDistance: Bool { self == .euclidean || self == .manhattan }

    var accentColorName: String {
        switch self {
        case .cosine:    return "blue"
        case .euclidean: return "orange"
        case .manhattan: return "green"
        case .semantic:  return "purple"
        }
    }

    var resultLabel: String {
        isDistance ? "Distance (lower = more similar)" : "Score (higher = more similar)"
    }
}

struct SearchResult: Identifiable {
    let id = UUID()
    let rank: Int
    let document: String
    let score: Double
    let mode: QueryMode
}

// MARK: - Pairwise Metrics

enum DocMetric: String, CaseIterable, Identifiable {
    case jaccard = "Jaccard"
    case dice    = "Dice"
    case inner   = "Inner Product"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .jaccard: return "circle.grid.cross"
        case .dice:    return "die.face.4"
        case .inner:   return "dot.radiowaves.left.and.right"
        }
    }

    var description: String {
        switch self {
        case .jaccard:
            return "Jaccard = |A ∩ B| / |A ∪ B|\n\nOverlap of term sets. 1.0 = identical vocabulary, 0.0 = no shared terms."
        case .dice:
            return "Dice = 2 × |A ∩ B| / (|A| + |B|)\n\nWeights shared terms more heavily than Jaccard. Always ≥ Jaccard for the same pair."
        case .inner:
            return "Inner Product = Σ(freq_A × freq_B)\n\nRaw dot product of frequency vectors — not normalised. Larger values mean more shared high-frequency terms."
        }
    }

    /// Whether the score is bounded [0, 1] (useful for rendering a progress bar).
    var isBounded: Bool { self != .inner }
}

struct MetricResult: Identifiable {
    let id = UUID()
    let metric: DocMetric
    let doc1: String
    let doc2: String
    let score: Double
}

// MARK: - Full Document Comparison

struct DocumentComparison {
    let doc1: String
    let doc2: String

    // Similarity (higher = more similar)
    let cosineSimilarity:   Double
    let jaccardCoefficient: Double
    let diceCoefficient:    Double
    let innerProduct:       Double

    // Dissimilarity (lower = more similar)
    let euclideanDistance:  Double
    let manhattanDistance:  Double
}

// MARK: - Setup / Pipeline

enum SetupStep: Int, CaseIterable, Identifiable {
    case initDB        = 1
    case preprocessing = 2
    case lsiIndex      = 3

    var id: Int { rawValue }

    var title: String {
        switch self {
        case .initDB:        return "Initialize Database"
        case .preprocessing: return "Run Preprocessing"
        case .lsiIndex:      return "Generate LSI Index"
        }
    }

    var subtitle: String {
        switch self {
        case .initDB:
            return "Creates SQLite schema: DOCUMENTS, TERMS, FREQUENCIES, SYNONYMS, LSI tables"
        case .preprocessing:
            return "NLP pipeline: lowercase → remove accents → tokenise → stopwords → stem (Snowball ES)"
        case .lsiIndex:
            return "Truncated SVD on TF matrix → stores U, Σ, Vᵀ for semantic folding-in"
        }
    }

    var icon: String {
        switch self {
        case .initDB:        return "cylinder.split.1x2"
        case .preprocessing: return "cpu"
        case .lsiIndex:      return "brain"
        }
    }
}

enum SetupStepState {
    case pending, running, done, failed(String)

    var isDone: Bool {
        if case .done = self { return true }
        return false
    }
    var isRunning: Bool {
        if case .running = self { return true }
        return false
    }
}

// MARK: - System Info

struct SystemInfo {
    let dbPath     = "data/document_base.db"
    let language   = "Spanish (ES)"
    let stemmer    = "Snowball (spanish)"
    let topic      = "Mental Health · University Students"
    let totalDocs  = 10
    let totalTerms: Int?       // populated after DB init
    let queryCount: Int?       // populated from QUERIES table
}
