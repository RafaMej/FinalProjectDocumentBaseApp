// MetricsView.swift
// Bound to MetricsViewModel — pure presentation.

import SwiftUI

struct MetricsView: View {
    @StateObject private var vm = MetricsViewModel()

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    metricPicker
                    docSelectors
                    computeButton
                    if let err = vm.errorMessage { ErrorBanner(message: err).padding(.horizontal) }
                    if let result = vm.result { resultCard(result) }
                    infoCard
                }
                .padding(.vertical)
            }
            .navigationTitle("Doc Metrics")
            .background(Color(.systemGroupedBackground))
        }
    }

    // MARK: - Metric Picker

    private var metricPicker: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Select Metric").font(.headline).padding(.horizontal)
            HStack(spacing: 12) {
                ForEach(DocMetric.allCases) { metric in
                    Button { vm.changeMetric(to: metric) } label: {
                        VStack(spacing: 6) {
                            Image(systemName: metric.icon).font(.title3)
                            Text(metric.rawValue).font(.caption2)
                        }
                        .frame(maxWidth: .infinity).padding(12)
                        .background(vm.selectedMetric == metric ? Color.indigo : Color(.systemBackground))
                        .foregroundColor(vm.selectedMetric == metric ? .white : .primary)
                        .cornerRadius(12)
                        .shadow(color: .black.opacity(0.06), radius: 4, y: 1)
                    }
                }
            }
            .padding(.horizontal)
        }
    }

    // MARK: - Doc Selectors

    private var docSelectors: some View {
        VStack(spacing: 12) {
            DocPickerRow(label: "Document 1", selection: $vm.doc1, options: vm.availableDocs)
            DocPickerRow(label: "Document 2", selection: $vm.doc2, options: vm.availableDocs)
        }
        .padding(.horizontal)
    }

    // MARK: - Compute Button

    private var computeButton: some View {
        VStack(spacing: 6) {
            Button(action: vm.compute) {
                HStack {
                    if vm.isLoading { ProgressView().tint(.white) }
                    else { Image(systemName: vm.selectedMetric.icon) }
                    Text(vm.isLoading ? "Computing…" : "Compute \(vm.selectedMetric.rawValue)")
                        .fontWeight(.semibold)
                }
                .frame(maxWidth: .infinity).padding(14)
                .background(!vm.canCompute || vm.isLoading ? Color.gray : Color.indigo)
                .foregroundColor(.white)
                .cornerRadius(14)
            }
            .disabled(!vm.canCompute || vm.isLoading)

            if !vm.canCompute {
                Text("Select two different documents")
                    .font(.caption).foregroundColor(.orange)
            }
        }
        .padding(.horizontal)
    }

    // MARK: - Result Card

    private func resultCard(_ result: MetricResult) -> some View {
        ScoreCard(
            title: result.metric.rawValue,
            subtitle: "\(result.doc1)  ↔  \(result.doc2)",
            score: result.score,
            isBounded: result.metric.isBounded
        )
        .padding(.horizontal)
    }

    // MARK: - Info Card

    private var infoCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("About this metric", systemImage: "info.circle")
                .font(.subheadline.bold())
            Text(vm.selectedMetric.description)
                .font(.caption).foregroundColor(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemBackground))
        .cornerRadius(14)
        .padding(.horizontal)
        .shadow(color: .black.opacity(0.05), radius: 4, y: 1)
    }
}

#Preview { MetricsView() }
