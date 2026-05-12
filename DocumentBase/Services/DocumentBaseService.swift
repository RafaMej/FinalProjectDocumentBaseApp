// DocumentBaseService.swift
// Abstracts all backend communication.
// Swap the mock implementations for real URLSession / Python API calls.

import Foundation

// MARK: - Protocol

protocol DocumentBaseServiceProtocol {
    /// Fetch all document names stored in the database.
    func fetchDocuments() async throws -> [DocumentItem]

    /// Run a query against the document collection.
    func runQuery(text: String, mode: QueryMode, topN: Int) async throws -> [SearchResult]

    /// Compare two documents with all six metrics.
    func compareDocuments(doc1: String, doc2: String) async throws -> DocumentComparison

    /// Compute a single pairwise metric for two documents.
    func computeMetric(_ metric: DocMetric, doc1: String, doc2: String) async throws -> MetricResult

    // Setup pipeline steps
    func initializeDatabase() async throws
    func runPreprocessing() async throws
    func generateLSI(components: Int) async throws

    /// Fetch total query count from history.
    func fetchQueryCount() async throws -> Int
}

// MARK: - Mock Implementation
// Replace with a real network/local service when the Python backend
// is exposed via Flask/FastAPI or called via PythonKit.

final class MockDocumentBaseService: DocumentBaseServiceProtocol {

    private let documents: [DocumentItem] = (1...10).map {
        DocumentItem(name: "doc\($0).txt")
    }

    // MARK: Documents

    func fetchDocuments() async throws -> [DocumentItem] {
        try await Task.sleep(nanoseconds: 300_000_000)
        return documents
    }

    // MARK: Query

    func runQuery(text: String, mode: QueryMode, topN: Int) async throws -> [SearchResult] {
        // Simulate network delay
        try await Task.sleep(nanoseconds: UInt64.random(in: 800_000_000...1_400_000_000))

        let shuffled = documents.shuffled().prefix(topN)
        let raw: [(String, Double)] = shuffled.map { doc in
            let score = mode.isDistance
                ? Double.random(in: 0.4...8.0)
                : Double.random(in: 0.25...0.99)
            return (doc.name, score)
        }

        let sorted = raw.sorted {
            mode.isDistance ? $0.1 < $1.1 : $0.1 > $1.1
        }

        return sorted.enumerated().map { idx, pair in
            SearchResult(rank: idx + 1, document: pair.0, score: pair.1, mode: mode)
        }
    }

    // MARK: Compare

    func compareDocuments(doc1: String, doc2: String) async throws -> DocumentComparison {
        try await Task.sleep(nanoseconds: 1_000_000_000)

        guard doc1 != doc2 else {
            throw ServiceError.sameDocument
        }

        return DocumentComparison(
            doc1:               doc1,
            doc2:               doc2,
            cosineSimilarity:   Double.random(in: 0.30...0.95),
            jaccardCoefficient: Double.random(in: 0.20...0.80),
            diceCoefficient:    Double.random(in: 0.25...0.85),
            innerProduct:       Double.random(in: 50...550),
            euclideanDistance:  Double.random(in: 0.5...10.0),
            manhattanDistance:  Double.random(in: 5...90)
        )
    }

    // MARK: Single Metric

    func computeMetric(_ metric: DocMetric, doc1: String, doc2: String) async throws -> MetricResult {
        try await Task.sleep(nanoseconds: 700_000_000)

        guard doc1 != doc2 else {
            throw ServiceError.sameDocument
        }

        let score: Double
        switch metric {
        case .jaccard: score = Double.random(in: 0.20...0.80)
        case .dice:    score = Double.random(in: 0.25...0.85)
        case .inner:   score = Double.random(in: 50...600)
        }

        return MetricResult(metric: metric, doc1: doc1, doc2: doc2, score: score)
    }

    // MARK: Setup Pipeline

    func initializeDatabase() async throws {
        try await Task.sleep(nanoseconds: 1_500_000_000)
        // Real call: POST /api/setup/init-db
    }

    func runPreprocessing() async throws {
        try await Task.sleep(nanoseconds: 2_000_000_000)
        // Real call: POST /api/setup/preprocess
    }

    func generateLSI(components: Int) async throws {
        try await Task.sleep(nanoseconds: 2_500_000_000)
        // Real call: POST /api/setup/generate-lsi  body: { "k": components }
    }

    func fetchQueryCount() async throws -> Int {
        try await Task.sleep(nanoseconds: 200_000_000)
        return Int.random(in: 0...42)
    }
}

// MARK: - Errors

enum ServiceError: LocalizedError {
    case sameDocument
    case lsiNotReady
    case dbNotInitialized
    case networkError(String)
    case decodingError

    var errorDescription: String? {
        switch self {
        case .sameDocument:
            return "Please select two different documents."
        case .lsiNotReady:
            return "LSI index not found. Run Setup → Generate LSI first."
        case .dbNotInitialized:
            return "Database not initialised. Run Setup → Initialize Database first."
        case .networkError(let msg):
            return "Network error: \(msg)"
        case .decodingError:
            return "Failed to decode server response."
        }
    }
}
