// Components.swift
// Shared, reusable SwiftUI components used across multiple views.
// No ViewModel dependencies — only plain data inputs.

import SwiftUI

// MARK: - Metric Bar

/// Horizontal progress bar for a single metric value.
struct MetricBar: View {
    let label: String
    let value: Double
    let maxValue: Double
    let color: Color
    var inverted: Bool = false   // distance metrics: lower = better → flip bar

    private var fraction: Double {
        let clamped = min(value / maxValue, 1.0)
        return inverted ? 1.0 - clamped : clamped
    }

    var body: some View {
        HStack(spacing: 10) {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 90, alignment: .leading)

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(color.opacity(0.15)).frame(height: 8)
                    Capsule()
                        .fill(color)
                        .frame(width: geo.size.width * fraction, height: 8)
                        .animation(.easeOut(duration: 0.5), value: fraction)
                }
            }
            .frame(height: 8)

            Text(String(format: "%.6f", value))
                .font(.system(.caption2, design: .monospaced))
                .frame(width: 76, alignment: .trailing)
                .foregroundColor(color)
        }
    }
}

// MARK: - Score Card

/// Large centred display of a single numeric result.
struct ScoreCard: View {
    let title: String
    let subtitle: String
    let score: Double
    let isBounded: Bool   // if true, shows a [0,1] progress bar

    var body: some View {
        VStack(spacing: 14) {
            Text(subtitle)
                .font(.caption)
                .foregroundColor(.secondary)

            Text(String(format: "%.6f", score))
                .font(.system(size: 46, weight: .bold, design: .monospaced))
                .foregroundColor(.indigo)

            Text(title)
                .font(.subheadline)
                .foregroundColor(.secondary)

            if isBounded {
                ProgressView(value: min(score, 1.0))
                    .progressViewStyle(.linear)
                    .tint(.indigo)
                    .padding(.horizontal, 24)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(24)
        .background(Color(.systemBackground))
        .cornerRadius(18)
        .shadow(color: .black.opacity(0.07), radius: 8, y: 2)
    }
}

// MARK: - Doc Picker Row

/// A label + menu picker for a document name.
struct DocPickerRow: View {
    let label: String
    @Binding var selection: String
    let options: [String]

    var body: some View {
        HStack {
            Text(label)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .frame(width: 110, alignment: .leading)

            Picker(label, selection: $selection) {
                ForEach(options, id: \.self) { Text($0) }
            }
            .pickerStyle(.menu)
            .frame(maxWidth: .infinity)
            .padding(10)
            .background(Color(.systemBackground))
            .cornerRadius(10)
        }
    }
}

// MARK: - Feature Row

/// One-line capability description used on the Home screen.
struct FeatureRow: View {
    let icon: String
    let color: Color
    let title: String
    let subtitle: String

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 14) {
                Image(systemName: icon)
                    .font(.system(size: 18))
                    .foregroundColor(color)
                    .frame(width: 32, height: 32)
                    .background(color.opacity(0.12))
                    .cornerRadius(8)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.subheadline.weight(.medium))
                    Text(subtitle).font(.caption).foregroundColor(.secondary)
                }
                Spacer()
            }
            .padding(.horizontal)
            .padding(.vertical, 10)
            Divider().padding(.leading, 60)
        }
    }
}

// MARK: - Stat Card

/// Small key-value card for the Home stats grid.
struct StatCard: View {
    let value: String
    let label: String
    let icon: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.indigo)
                .frame(width: 36)

            VStack(alignment: .leading, spacing: 2) {
                Text(value).font(.title3.bold())
                Text(label).font(.caption).foregroundColor(.secondary)
            }
            Spacer()
        }
        .padding(14)
        .background(Color(.systemBackground))
        .cornerRadius(14)
        .shadow(color: .black.opacity(0.06), radius: 6, y: 2)
    }
}

// MARK: - Info Row

/// Simple two-column label/value row.
struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 80, alignment: .leading)
            Text(value).font(.caption.weight(.medium))
            Spacer()
        }
    }
}

// MARK: - Status Row

/// Checkmark/circle status row for the Setup screen.
struct StatusRow: View {
    let label: String
    let done: Bool

    var body: some View {
        HStack {
            Image(systemName: done ? "checkmark.circle.fill" : "circle")
                .foregroundColor(done ? .green : .secondary)
            Text(label).font(.subheadline)
            Spacer()
            Text(done ? "Ready" : "Pending")
                .font(.caption)
                .foregroundColor(done ? .green : .secondary)
        }
    }
}

// MARK: - Error Banner

struct ErrorBanner: View {
    let message: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.orange)
            Text(message)
                .font(.caption)
                .foregroundColor(.primary)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.orange.opacity(0.1))
        .cornerRadius(10)
    }
}

// MARK: - Loading Overlay

struct LoadingOverlay: View {
    let message: String

    var body: some View {
        HStack(spacing: 12) {
            ProgressView()
            Text(message).font(.subheadline).foregroundColor(.secondary)
        }
        .padding(16)
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 8, y: 2)
    }
}
