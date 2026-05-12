// CompareView.swift
// Bound to CompareViewModel — pure presentation.

import SwiftUI

struct CompareView: View {
    @StateObject private var vm = CompareViewModel()

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    docSelectors
                    compareButton
                    if let err = vm.errorMessage { ErrorBanner(message: err).padding(.horizontal) }
                    if let comparison = vm.comparison { ComparisonResultsSection(c: comparison) }
                }
                .padding(.vertical)
            }
            .navigationTitle("Compare Docs")
            .background(Color(.systemGroupedBackground))
        }
    }

    // MARK: - Doc Selectors

    private var docSelectors: some View {
        VStack(spacing: 12) {
            DocPickerRow(label: "Document A", selection: $vm.doc1, options: vm.availableDocs)
            HStack { Spacer(); Image(systemName: "arrow.left.arrow.right").foregroundColor(.indigo); Spacer() }
            DocPickerRow(label: "Document B", selection: $vm.doc2, options: vm.availableDocs)
        }
        .padding(.horizontal)
    }

    // MARK: - Compare Button

    private var compareButton: some View {
        VStack(spacing: 6) {
            Button(action: vm.compare) {
                HStack {
                    if vm.isLoading { ProgressView().tint(.white) }
                    else { Image(systemName: "arrow.left.arrow.right") }
                    Text(vm.isLoading ? "Computing…" : "Compare Documents").fontWeight(.semibold)
                }
                .frame(maxWidth: .infinity).padding(14)
                .background(!vm.canCompare || vm.isLoading ? Color.gray : Color.indigo)
                .foregroundColor(.white)
                .cornerRadius(14)
            }
            .disabled(!vm.canCompare || vm.isLoading)

            if !vm.canCompare {
                Text("Select two different documents")
                    .font(.caption).foregroundColor(.orange)
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - Comparison Results Section

private struct ComparisonResultsSection: View {
    let c: DocumentComparison

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("\(c.doc1)  ↔  \(c.doc2)")
                .font(.headline)
                .padding(.horizontal)

            similaritySection
            dissimilaritySection
        }
    }

    private var similaritySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Similarity  (higher = more similar)", systemImage: "arrow.up.circle.fill")
                .font(.subheadline.bold()).foregroundColor(.blue)

            MetricBar(label: "Cosine",  value: c.cosineSimilarity,   maxValue: 1.0, color: .blue)
            MetricBar(label: "Jaccard", value: c.jaccardCoefficient, maxValue: 1.0, color: .teal)
            MetricBar(label: "Dice",    value: c.diceCoefficient,    maxValue: 1.0, color: .cyan)

            // Inner Product is unbounded — show raw value only
            HStack {
                Text("Inner Product")
                    .font(.caption).foregroundColor(.secondary).frame(width: 90, alignment: .leading)
                Spacer()
                Text(String(format: "%.4f", c.innerProduct))
                    .font(.system(.caption, design: .monospaced)).foregroundColor(.indigo)
            }
            .padding(10)
            .background(Color(.systemBackground))
            .cornerRadius(10)
        }
        .padding(14)
        .background(Color.blue.opacity(0.05))
        .cornerRadius(14)
        .padding(.horizontal)
    }

    private var dissimilaritySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Dissimilarity  (lower = more similar)", systemImage: "arrow.down.circle.fill")
                .font(.subheadline.bold()).foregroundColor(.orange)

            MetricBar(label: "Euclidean", value: c.euclideanDistance, maxValue: 15.0, color: .orange, inverted: true)
            MetricBar(label: "Manhattan", value: c.manhattanDistance, maxValue: 120.0, color: .red,   inverted: true)
        }
        .padding(14)
        .background(Color.orange.opacity(0.05))
        .cornerRadius(14)
        .padding(.horizontal)
    }
}

#Preview { CompareView() }
