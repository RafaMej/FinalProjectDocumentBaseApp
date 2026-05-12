// SetupViewModel.swift
// Owns all state for the Setup pipeline tab.

import Foundation
import Combine

@MainActor
final class SetupViewModel: ObservableObject {

    // MARK: - Published State

    @Published private(set) var stepStates: [SetupStep: SetupStepState] = [
        .initDB:        .pending,
        .preprocessing: .pending,
        .lsiIndex:      .pending,
    ]

    @Published var lsiComponents: Double = 5   // user-chosen k for SVD
    @Published private(set) var queryCount: Int? = nil
    @Published private(set) var logLines: [String] = []

    // MARK: - Private

    private let service: DocumentBaseServiceProtocol

    // MARK: - Init

    init(service: DocumentBaseServiceProtocol = RealDocumentBaseService()) {
        self.service = service
    }

    // MARK: - Derived

    var isDBDone:   Bool { stepStates[.initDB]?.isDone == true }
    var isPrepDone: Bool { stepStates[.preprocessing]?.isDone == true }
    var isLSIDone:  Bool { stepStates[.lsiIndex]?.isDone == true }
    var allDone:    Bool { isDBDone && isPrepDone && isLSIDone }

    func isLocked(_ step: SetupStep) -> Bool {
        switch step {
        case .initDB:        return false
        case .preprocessing: return !isDBDone
        case .lsiIndex:      return !isPrepDone
        }
    }

    func state(for step: SetupStep) -> SetupStepState {
        stepStates[step] ?? .pending
    }

    // MARK: - Intent

    func run(_ step: SetupStep) {
        guard !isLocked(step) else { return }
        guard stepStates[step]?.isRunning != true else { return }

        stepStates[step] = .running
        appendLog("▶ Starting: \(step.title)…")

        Task {
            do {
                switch step {
                case .initDB:
                    try await service.initializeDatabase()
                    appendLog("✓ Database initialised — schema created, synonyms loaded.")
                case .preprocessing:
                    try await service.runPreprocessing()
                    appendLog("✓ Preprocessing done — 10 docs stemmed and stored.")
                case .lsiIndex:
                    try await service.generateLSI(components: Int(lsiComponents))
                    appendLog("✓ LSI index generated — k=\(Int(lsiComponents)) components, U·Σ·Vᵀ stored.")
                }
                stepStates[step] = .done
                queryCount = try? await service.fetchQueryCount()
            } catch {
                stepStates[step] = .failed(error.localizedDescription)
                appendLog("✗ Error: \(error.localizedDescription)")
            }
        }
    }

    func resetStep(_ step: SetupStep) {
        // Allow re-running a step
        stepStates[step] = .pending
    }

    // MARK: - Helpers

    private func appendLog(_ line: String) {
        let timestamp = DateFormatter.localizedString(
            from: Date(), dateStyle: .none, timeStyle: .medium
        )
        logLines.append("[\(timestamp)] \(line)")
    }

    func clearLog() { logLines.removeAll() }
}
