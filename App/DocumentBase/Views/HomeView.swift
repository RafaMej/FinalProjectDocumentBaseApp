// HomeView.swift
// Static informational home screen — no ViewModel needed.

import SwiftUI

struct HomeView: View {

    private let stats: [(String, String, String)] = [
        ("10",  "Documents", "doc.text.fill"),
        ("LSI", "Indexing",  "brain"),
        ("6",   "Metrics",   "chart.pie.fill"),
        ("ES",  "Language",  "textformat"),
    ]

    private let features: [(String, Color, String, String)] = [
        ("waveform.path.ecg",        .blue,   "Cosine Similarity",        "Query → Docs  (higher = more relevant)"),
        ("ruler",                    .orange, "Euclidean Distance",        "Query → Docs  (lower = more relevant)"),
        ("map",                      .green,  "Manhattan Distance",        "L1 norm distance to query vector"),
        ("brain.head.profile",       .purple, "LSI Semantic Search",       "Latent concept space via Truncated SVD"),
        ("arrow.left.arrow.right",   .pink,   "Document Comparison",       "All six metrics: doc vs doc"),
        ("circle.grid.cross",        .teal,   "Jaccard / Dice / Inner ·",  "Set-based similarity measures"),
    ]

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    headerCard
                    statsGrid
                    featureList
                }
                .padding(.vertical)
            }
            .navigationTitle("LSI System")
            .background(Color(.systemGroupedBackground))
        }
    }

    // MARK: - Sub-views

    private var headerCard: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 20)
                .fill(
                    LinearGradient(
                        colors: [.indigo, .purple],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
            VStack(spacing: 8) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 48))
                    .foregroundColor(.white.opacity(0.9))
                Text("Document Base System")
                    .font(.title2.bold())
                    .foregroundColor(.white)
                Text("Mental Health · University Students")
                    .font(.subheadline)
                    .foregroundColor(.white.opacity(0.75))
            }
            .padding(32)
        }
        .padding(.horizontal)
    }

    private var statsGrid: some View {
        LazyVGrid(
            columns: [GridItem(.flexible()), GridItem(.flexible())],
            spacing: 12
        ) {
            ForEach(stats, id: \.0) { value, label, icon in
                StatCard(value: value, label: label, icon: icon)
            }
        }
        .padding(.horizontal)
    }

    private var featureList: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Capabilities")
                .font(.headline)
                .padding(.horizontal)

            ForEach(features, id: \.2) { icon, color, title, subtitle in
                FeatureRow(icon: icon, color: color, title: title, subtitle: subtitle)
            }
        }
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .padding(.horizontal)
        .shadow(color: .black.opacity(0.06), radius: 8, y: 2)
    }
}

#Preview { HomeView() }
