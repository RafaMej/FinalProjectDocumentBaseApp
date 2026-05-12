// CompareViewModel.swift
// Owns all state for the Document Comparison tab.

import Foundation
import Combine

@MainActor
final class CompareViewModel: ObservableObject {

    // MARK: - Published State

    @Published var doc1: String = "doc1.txt"
    @Published var doc2: String = "doc2.txt"

    @Published private(set) var comparison: DocumentComparison? = nil
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

    var canCompare: Bool { doc1 != doc2 }

    // MARK: - Intent

    func compare() {
        guard canCompare else { return }
        isLoading    = true
        comparison   = nil
        errorMessage = nil

        Task {
            do {
                comparison = try await service.compareDocuments(doc1: doc1, doc2: doc2)
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }

    func reset() {
        comparison   = nil
        errorMessage = nil
    }
}
