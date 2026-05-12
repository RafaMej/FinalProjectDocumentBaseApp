// RealDocumentBaseService.swift
// Implementación real que llama al backend Flask.

import Foundation

final class RealDocumentBaseService: DocumentBaseServiceProtocol {

    // ⚠️ En simulador: usa 127.0.0.1
    // ⚠️ En dispositivo físico: usa la IP de tu Mac en la red Wi-Fi (ej. 192.168.1.x)
    private let baseURL = "http://127.0.0.1:5000/api"

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        return URLSession(configuration: config)
    }()

    // MARK: - Helpers

    private func post<T: Decodable>(_ path: String, body: [String: Any]? = nil) async throws -> T {
        guard let url = URL(string: baseURL + path) else {
            throw ServiceError.networkError("Invalid URL: \(path)")
        }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body = body {
            req.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        let (data, resp) = try await session.data(for: req)
        try checkStatus(resp, data: data)
        return try JSONDecoder().decode(T.self, from: data)
    }

    private func get<T: Decodable>(_ path: String) async throws -> T {
        guard let url = URL(string: baseURL + path) else {
            throw ServiceError.networkError("Invalid URL: \(path)")
        }
        let (data, resp) = try await session.data(from: url)
        try checkStatus(resp, data: data)
        return try JSONDecoder().decode(T.self, from: data)
    }

    private func checkStatus(_ resp: URLResponse, data: Data) throws {
        guard let http = resp as? HTTPURLResponse else { return }
        if http.statusCode >= 400 {
            if let errObj = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw ServiceError.networkError(errObj.error)
            }
            throw ServiceError.networkError("HTTP \(http.statusCode)")
        }
    }

    // MARK: - Documentos

    func fetchDocuments() async throws -> [DocumentItem] {
        struct Resp: Decodable { let documents: [String] }
        let resp: Resp = try await get("/docs")
        return resp.documents.map { DocumentItem(name: $0) }
    }

    // MARK: - Búsqueda

    func runQuery(text: String, mode: QueryMode, topN: Int) async throws -> [SearchResult] {
        struct RawResult: Decodable { let rank: Int; let document: String; let score: Double }
        struct Resp: Decodable { let results: [RawResult]; let mode: String }

        let modeStr: String
        switch mode {
        case .cosine:    modeStr = "cosine"
        case .euclidean: modeStr = "euclidean"
        case .manhattan: modeStr = "manhattan"
        case .semantic:  modeStr = "semantic"
        }

        let resp: Resp = try await post("/query/search", body: [
            "query": text,
            "mode": modeStr,
            "top_n": topN
        ])

        return resp.results.map {
            SearchResult(rank: $0.rank, document: $0.document, score: $0.score, mode: mode)
        }
    }

    // MARK: - Comparación

    func compareDocuments(doc1: String, doc2: String) async throws -> DocumentComparison {
        struct Resp: Decodable {
            let doc1: String, doc2: String
            let cosineSimilarity: Double, jaccardCoefficient: Double
            let diceCoefficient: Double, innerProduct: Double
            let euclideanDistance: Double, manhattanDistance: Double
        }
        let resp: Resp = try await post("/query/compare", body: ["doc1": doc1, "doc2": doc2])
        return DocumentComparison(
            doc1: resp.doc1, doc2: resp.doc2,
            cosineSimilarity:   resp.cosineSimilarity,
            jaccardCoefficient: resp.jaccardCoefficient,
            diceCoefficient:    resp.diceCoefficient,
            innerProduct:       resp.innerProduct,
            euclideanDistance:  resp.euclideanDistance,
            manhattanDistance:  resp.manhattanDistance
        )
    }

    // MARK: - Métrica individual

    func computeMetric(_ metric: DocMetric, doc1: String, doc2: String) async throws -> MetricResult {
        struct Resp: Decodable { let metric: String; let doc1: String; let doc2: String; let score: Double }
        let metricStr: String
        switch metric {
        case .jaccard: metricStr = "jaccard"
        case .dice:    metricStr = "dice"
        case .inner:   metricStr = "inner"
        }
        let resp: Resp = try await post("/query/metric", body: [
            "metric": metricStr, "doc1": doc1, "doc2": doc2
        ])
        return MetricResult(metric: metric, doc1: resp.doc1, doc2: resp.doc2, score: resp.score)
    }

    // MARK: - Setup

    func initializeDatabase() async throws {
        struct Resp: Decodable { let ok: Bool }
        let _: Resp = try await post("/setup/init-db")
    }

    func runPreprocessing() async throws {
        struct Resp: Decodable { let ok: Bool }
        let _: Resp = try await post("/setup/preprocess")
    }

    func generateLSI(components: Int) async throws {
        struct Resp: Decodable { let ok: Bool }
        let _: Resp = try await post("/setup/lsi", body: ["k": components])
    }

    func fetchQueryCount() async throws -> Int {
        struct Resp: Decodable { let count: Int }
        let resp: Resp = try await get("/query-count")
        return resp.count
    }
}

private struct ErrorResponse: Decodable { let error: String }
