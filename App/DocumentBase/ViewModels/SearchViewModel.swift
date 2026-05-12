// SearchViewModel.swift
// Owns all state and business logic for the Search tab.

import Foundation
import Combine

@MainActor
final class SearchViewModel: ObservableObject {

    // MARK: - Published State

    @Published var queryText: String = ""
    @Published var selectedMode: QueryMode = .cosine
    @Published var topN: Double = 5

    @Published private(set) var results: [SearchResult] = []
    @Published private(set) var isLoading: Bool = false
    @Published private(set) var hasSearched: Bool = false
    @Published private(set) var errorMessage: String? = nil

    // MARK: - Constants

    let suggestedQueries: [String] = [
        "ansiedad exámenes universitarios",
        "depresión apoyo social",
        "estrés académico rendimiento",
        "estrategias afrontamiento bienestar",
        "burnout estudiantes universitarios",
        "salud mental pandemia",
    ]

    // MARK: - Private

    private let service: DocumentBaseServiceProtocol

    // MARK: - Init

    init(service: DocumentBaseServiceProtocol = RealDocumentBaseService()) {
        self.service = service
    }

    // MARK: - Derived

    var canSearch: Bool { !queryText.trimmingCharacters(in: .whitespaces).isEmpty }

    // MARK: - Intent

    func runQuery() {
        guard canSearch else { return }
        isLoading   = true
        hasSearched = false
        errorMessage = nil
        results     = []

        Task {
            do {
                let res = try await service.runQuery(
                    text:  queryText,
                    mode:  selectedMode,
                    topN:  Int(topN)
                )
                results     = res
                hasSearched = true
            } catch {
                errorMessage = error.localizedDescription
                hasSearched  = true
            }
            isLoading = false
        }
    }

    func selectSuggestion(_ text: String) {
        queryText = text
    }

    func clearResults() {
        results      = []
        hasSearched  = false
        errorMessage = nil
    }
}
