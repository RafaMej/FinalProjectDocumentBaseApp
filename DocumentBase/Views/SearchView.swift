// SearchView.swift
// Bound to SearchViewModel — pure presentation.

import SwiftUI

struct SearchView: View {
    @StateObject private var vm = SearchViewModel()

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    modePicker
                    searchControls
                    if let err = vm.errorMessage { ErrorBanner(message: err).padding(.horizontal) }
                    if vm.hasSearched { resultsSection }
                    if !vm.hasSearched && !vm.isLoading { suggestedSection }
                }
                .padding(.vertical)
            }
            .navigationTitle("Search")
            .background(Color(.systemGroupedBackground))
        }
    }

    // MARK: - Mode Picker

    private var modePicker: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Search Mode").font(.headline).padding(.horizontal)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(QueryMode.allCases) { mode in
                        ModeChip(mode: mode, isSelected: vm.selectedMode == mode) {
                            vm.selectedMode = mode
                            vm.clearResults()
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
    }

    // MARK: - Search Controls

    private var searchControls: some View {
        VStack(spacing: 12) {
            // Text field
            HStack {
                Image(systemName: "magnifyingglass").foregroundColor(.secondary)
                TextField("e.g. ansiedad exámenes universitarios", text: $vm.queryText)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .submitLabel(.search)
                    .onSubmit { vm.runQuery() }
                if !vm.queryText.isEmpty {
                    Button { vm.queryText = "" } label: {
                        Image(systemName: "xmark.circle.fill").foregroundColor(.secondary)
                    }
                }
            }
            .padding(14)
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.06), radius: 6, y: 2)

            // Top-N slider
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("Top results").font(.subheadline).foregroundColor(.secondary)
                    Spacer()
                    Text("\(Int(vm.topN))").font(.subheadline.bold())
                }
                Slider(value: $vm.topN, in: 1...10, step: 1).accentColor(.indigo)
            }
            .padding(14)
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.06), radius: 6, y: 2)

            // Run button
            Button(action: vm.runQuery) {
                HStack {
                    if vm.isLoading { ProgressView().tint(.white) }
                    else { Image(systemName: vm.selectedMode.icon) }
                    Text(vm.isLoading ? "Searching…" : "Run Query").fontWeight(.semibold)
                }
                .frame(maxWidth: .infinity)
                .padding(14)
                .background(vm.canSearch && !vm.isLoading ? Color.indigo : Color.gray)
                .foregroundColor(.white)
                .cornerRadius(14)
            }
            .disabled(!vm.canSearch || vm.isLoading)
        }
        .padding(.horizontal)
    }

    // MARK: - Results

    private var resultsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Results for \(vm.queryText) ").font(.headline)
                Spacer()
                Text("\(vm.results.count) docs").font(.caption).foregroundColor(.secondary)
            }

            if vm.results.isEmpty && !vm.isLoading {
                emptyResults
            } else {
                let maxScore = vm.results.map(\.score).max() ?? 1.0
                ForEach(vm.results) { result in
                    ResultRow(result: result, maxScore: maxScore)
                }
            }
        }
        .padding(.horizontal)
    }

    private var emptyResults: some View {
        HStack {
            Spacer()
            VStack(spacing: 8) {
                Image(systemName: "exclamationmark.magnifyingglass")
                    .font(.largeTitle).foregroundColor(.secondary)
                Text("No results found").foregroundColor(.secondary)
            }
            .padding(24)
            Spacer()
        }
    }

    // MARK: - Suggested Queries

    private var suggestedSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Suggested Queries").font(.headline)
            ForEach(vm.suggestedQueries, id: \.self) { suggestion in
                Button { vm.selectSuggestion(suggestion) } label: {
                    HStack {
                        Image(systemName: "sparkle").font(.caption).foregroundColor(.indigo)
                        Text(suggestion).font(.subheadline).foregroundColor(.primary)
                        Spacer()
                        Image(systemName: "chevron.right").font(.caption2).foregroundColor(.secondary)
                    }
                    .padding(12)
                    .background(Color(.systemBackground))
                    .cornerRadius(10)
                }
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - Mode Chip

private struct ModeChip: View {
    let mode: QueryMode
    let isSelected: Bool
    let action: () -> Void

    private var chipColor: Color {
        switch mode {
        case .cosine:    return .blue
        case .euclidean: return .orange
        case .manhattan: return .green
        case .semantic:  return .purple
        }
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: mode.icon).font(.caption)
                Text(mode.rawValue).font(.caption.weight(.medium))
            }
            .padding(.horizontal, 14).padding(.vertical, 8)
            .background(isSelected ? chipColor : Color(.systemBackground))
            .foregroundColor(isSelected ? .white : .primary)
            .cornerRadius(20)
            .shadow(color: .black.opacity(0.08), radius: 4, y: 1)
        }
    }
}

// MARK: - Result Row

private struct ResultRow: View {
    let result: SearchResult
    let maxScore: Double

    private var barColor: Color {
        switch result.mode {
        case .cosine:    return .blue
        case .euclidean: return .orange
        case .manhattan: return .green
        case .semantic:  return .purple
        }
    }

    private var normalizedBar: Double {
        result.mode.isDistance
            ? 1.0 - min(result.score / maxScore, 1.0)
            : min(result.score / maxScore, 1.0)
    }

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Text("#\(result.rank)")
                    .font(.caption.bold()).foregroundColor(.secondary).frame(width: 28)
                Text(result.document).font(.subheadline.weight(.medium))
                Spacer()
                Text(String(format: "%.6f", result.score))
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(barColor)
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(barColor.opacity(0.12)).frame(height: 6)
                    Capsule()
                        .fill(barColor)
                        .frame(width: geo.size.width * normalizedBar, height: 6)
                        .animation(.easeOut(duration: 0.5), value: normalizedBar)
                }
            }
            .frame(height: 6)
        }
        .padding(14)
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 4, y: 1)
    }
}

#Preview { SearchView() }
