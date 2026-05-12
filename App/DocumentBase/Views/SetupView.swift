// SetupView.swift
// Bound to SetupViewModel — pure presentation.

import SwiftUI

struct SetupView: View {
    @StateObject private var vm = SetupViewModel()
    @State private var showLog = false

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    pipelineSection
                    lsiComponentsCard
                    statusCard
                    dbInfoCard
                }
                .padding(.vertical)
            }
            .navigationTitle("Setup")
            .background(Color(.systemGroupedBackground))
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button { showLog.toggle() } label: {
                        Image(systemName: "terminal")
                    }
                }
            }
            .sheet(isPresented: $showLog) { LogSheet(lines: vm.logLines, onClear: vm.clearLog) }
        }
    }

    // MARK: - Pipeline Steps

    private var pipelineSection: some View {
        VStack(alignment: .leading, spacing: 4) {
            VStack(alignment: .leading, spacing: 2) {
                Text("Setup Pipeline").font(.headline).padding(.horizontal)
                Text("Run these steps in order before searching.")
                    .font(.caption).foregroundColor(.secondary).padding(.horizontal)
            }
            ForEach(SetupStep.allCases) { step in
                SetupStepRow(
                    step: step,
                    state: vm.state(for: step),
                    isLocked: vm.isLocked(step),
                    onRun: { vm.run(step) },
                    onReset: { vm.resetStep(step) }
                )
            }
        }
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .padding(.horizontal)
        .shadow(color: .black.opacity(0.06), radius: 8, y: 2)
    }

    // MARK: - LSI Components Slider

    private var lsiComponentsCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("LSI Components (k)", systemImage: "slider.horizontal.3")
                .font(.subheadline.bold())
            Text("Number of singular values to retain. More components = richer semantics, slower queries.")
                .font(.caption).foregroundColor(.secondary)
            HStack {
                Slider(value: $vm.lsiComponents, in: 2...9, step: 1).accentColor(.indigo)
                Text("\(Int(vm.lsiComponents))")
                    .font(.subheadline.bold()).frame(width: 24)
            }
        }
        .padding(16)
        .background(Color(.systemBackground))
        .cornerRadius(14)
        .padding(.horizontal)
        .shadow(color: .black.opacity(0.06), radius: 6, y: 2)
    }

    // MARK: - Status Card

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("System Status").font(.headline)
            StatusRow(label: "Database",      done: vm.isDBDone)
            StatusRow(label: "Preprocessing", done: vm.isPrepDone)
            StatusRow(label: "LSI Index",     done: vm.isLSIDone)

            if vm.allDone {
                HStack {
                    Image(systemName: "checkmark.seal.fill").foregroundColor(.green)
                    Text("System ready — all search modes available")
                        .font(.subheadline).foregroundColor(.green)
                }
                .padding(12).background(Color.green.opacity(0.1)).cornerRadius(10)
            }
        }
        .padding(16)
        .background(Color(.systemBackground))
        .cornerRadius(14)
        .padding(.horizontal)
        .shadow(color: .black.opacity(0.06), radius: 6, y: 2)
    }

    // MARK: - DB Info Card

    private var dbInfoCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Database Info", systemImage: "externaldrive").font(.subheadline.bold())
            InfoRow(label: "Path",     value: "data/document_base.db")
            InfoRow(label: "Language", value: "Spanish (ES)")
            InfoRow(label: "Stemmer",  value: "Snowball (spanish)")
            InfoRow(label: "Topic",    value: "Mental Health · University Students")
            InfoRow(label: "Docs",     value: "10 documents")
        }
        .padding(16)
        .background(Color(.systemBackground))
        .cornerRadius(14)
        .padding(.horizontal)
        .shadow(color: .black.opacity(0.06), radius: 6, y: 2)
    }
}

// MARK: - Setup Step Row

private struct SetupStepRow: View {
    let step: SetupStep
    let state: SetupStepState
    let isLocked: Bool
    let onRun: () -> Void
    let onReset: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 14) {
                stepCircle
                VStack(alignment: .leading, spacing: 2) {
                    Text(step.title).font(.subheadline.weight(.medium))
                    Text(step.subtitle).font(.caption).foregroundColor(.secondary)
                }
                Spacer()
                actionButton
            }
            .padding(.horizontal)
            .padding(.vertical, 14)
            Divider().padding(.leading, 64)
        }
    }

    private var stepCircle: some View {
        ZStack {
            Circle()
                .fill(circleColor)
                .frame(width: 36, height: 36)

            if state.isDone {
                Image(systemName: "checkmark").font(.caption.bold()).foregroundColor(.white)
            } else if case .failed = state {
                Image(systemName: "xmark").font(.caption.bold()).foregroundColor(.white)
            } else {
                Text("\(step.rawValue)").font(.caption.bold()).foregroundColor(.white)
            }
        }
    }

    private var circleColor: Color {
        if state.isDone { return .green }
        if case .failed = state { return .red }
        if isLocked { return .gray.opacity(0.4) }
        return .indigo
    }

    @ViewBuilder
    private var actionButton: some View {
        if state.isRunning {
            ProgressView().frame(width: 28, height: 28)
        } else if state.isDone {
            Button(action: onReset) {
                Image(systemName: "arrow.clockwise")
                    .font(.caption).foregroundColor(.secondary)
            }
        } else if case .failed = state {
            Button(action: onRun) {
                Image(systemName: "arrow.clockwise")
                    .font(.caption).foregroundColor(.red)
            }
        } else if isLocked {
            Image(systemName: "lock.fill")
                .font(.caption).foregroundColor(.secondary)
        } else {
            Button(action: onRun) {
                Image(systemName: "play.fill")
                    .font(.caption).foregroundColor(.white)
                    .frame(width: 28, height: 28)
                    .background(Color.indigo)
                    .cornerRadius(8)
            }
        }
    }
}

// MARK: - Log Sheet

private struct LogSheet: View {
    let lines: [String]
    let onClear: () -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationView {
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 4) {
                        if lines.isEmpty {
                            Text("No log output yet.")
                                .font(.system(.caption, design: .monospaced))
                                .foregroundColor(.secondary)
                                .padding()
                        } else {
                            ForEach(lines.indices, id: \.self) { i in
                                Text(lines[i])
                                    .font(.system(.caption, design: .monospaced))
                                    .id(i)
                            }
                            .padding()
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .onChange(of: lines.count) { _ in
                    if let last = lines.indices.last {
                        withAnimation { proxy.scrollTo(last, anchor: .bottom) }
                    }
                }
            }
            .navigationTitle("Log Output")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Clear", action: onClear)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

#Preview { SetupView() }
