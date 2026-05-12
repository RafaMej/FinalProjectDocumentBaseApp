// DocumentBaseApp.swift
// App entry point and root tab container.

import SwiftUI

@main
struct DocumentBaseApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Home",    systemImage: "house.fill") }

            SearchView()
                .tabItem { Label("Search",  systemImage: "magnifyingglass") }

            CompareView()
                .tabItem { Label("Compare", systemImage: "arrow.left.arrow.right") }

            MetricsView()
                .tabItem { Label("Metrics", systemImage: "chart.bar.xaxis") }

            SetupView()
                .tabItem { Label("Setup",   systemImage: "gearshape.fill") }
        }
        .accentColor(.indigo)
    }
}

#Preview { ContentView() }
