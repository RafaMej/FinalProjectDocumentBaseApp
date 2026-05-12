// MetricsViewModel.swift
// Owns all state for the individual Doc Metrics tab (Jaccard / Dice / Inner Product).

import Foundation
import Combine

@MainActor
final class MetricsViewModel: ObservableObject {

    // MARK: - Published State

    @Published var doc1: String = "doc1.txt"
    @Published var doc2: String = "doc2.txt"
    @Published var selectedMetric: DocMetric = .jaccard

    @Published private(set) var result: MetricResult? = nil
    @Published private(set) var isLoading: Bool = false
    @Published private(set) var errorMessage: String? = nil

    // MARK: - Constants

    let availableDocs: [String] = (1...10).map { "doc\($0).txt" }

    // MARK: - Private

    private let service: DocumentBaseServiceProtocol

    // MARK: - Init

    init(service: DocumentBaseServiceProtocol = MockDocumentBaseService()) {
        self.service = service
    }

    // MARK: - Derived

    var canCompute: Bool { doc1 != doc2 }

    // MARK: - Intent

    func compute() {
        guard canCompute else { return }
        isLoading    = true
        result       = nil
        errorMessage = nil

        Task {
            do {
                result = try await service.computeMetric(selectedMetric, doc1: doc1, doc2: doc2)
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }

    func changeMetric(to metric: DocMetric) {
        selectedMetric = metric
        result         = nil
        errorMessage   = nil
    }

    func reset() {
        result       = nil
        errorMessage = nil
    }
}
