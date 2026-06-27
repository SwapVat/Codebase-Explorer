import re

with open("src/App.jsx", "r") as f:
    content = f.read()

# Define mapping for Tailwind classes to semantic theme classes
replacements = {
    r'\bbg-gray-950\b': 'bg-primary',
    r'\bbg-gray-900/50\b': 'bg-secondary/50',
    r'\bbg-gray-900/80\b': 'bg-secondary/80',
    r'\bbg-gray-900\b': 'bg-secondary',
    r'\bbg-gray-800/50\b': 'bg-tertiary/50',
    r'\bbg-gray-800\b': 'bg-tertiary',
    r'\bbg-gray-700/30\b': 'bg-quaternary/30',
    r'\bbg-gray-700\b': 'bg-quaternary',
    r'\bborder-gray-800\b': 'border-primary',
    r'\bborder-gray-700\b': 'border-secondary',
    r'\bborder-gray-600\b': 'border-tertiary',
    r'\btext-gray-100\b': 'text-primary',
    r'\btext-gray-200\b': 'text-primary',
    r'\btext-gray-300\b': 'text-secondary',
    r'\btext-gray-400\b': 'text-muted',
    r'\btext-gray-500\b': 'text-muted',
    r'\btext-white\b': 'text-inverted',
    
    # Buttons/Accents (replacing specific color buttons with accent)
    r'\bbg-(?:blue|purple|emerald|amber|rose|red|cyan)-600\b': 'bg-accent',
    r'\bbg-(?:blue|purple|emerald|amber|rose|red|cyan)-500\b': 'bg-accent-hover',
    r'\bshadow-(?:blue|purple|emerald|amber|rose|red|cyan)-500/20\b': 'shadow-accent/20',
    r'\bshadow-(?:blue|purple|emerald|amber|rose|red|cyan)-500/25\b': 'shadow-accent/25',
    r'\bshadow-(?:blue|purple|emerald|amber|rose|red|cyan)-500/30\b': 'shadow-accent/30',
    r'\btext-(?:blue|purple|emerald|amber|rose|red|cyan)-400\b': 'text-accent',
    r'\bborder-(?:blue|purple|emerald|amber|rose|red|cyan)-500/20\b': 'border-accent/20',
    r'\bborder-(?:blue|purple|emerald|amber|rose|red|cyan)-500/30\b': 'border-accent/30',
    r'\bfocus:border-(?:blue|purple|emerald|amber|rose|red|cyan)-500\b': 'focus:border-accent',
}

# We also need to add the theme state and toggle button
# Find function App()
new_app_def = """
function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [theme, setTheme] = useState("dark");

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");
"""
content = re.sub(r'function App\(\) \{\n  const \[activeTab, setActiveTab\] = useState\("dashboard"\);', new_app_def, content)

# Inject the className={theme} into the root div
content = re.sub(r'<div className="min-h-screen bg-primary text-primary font-sans flex">', r'<div className={`${theme} min-h-screen bg-primary text-primary font-sans flex`}>', content)

# Add the toggle button to the sidebar
toggle_btn = """
        <div className="p-6 border-t border-primary flex justify-between items-center">
          <div className="flex items-center gap-3 text-muted text-xs">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            System Online
          </div>
          <button onClick={toggleTheme} className="text-muted hover:text-primary transition p-2 rounded-lg hover:bg-tertiary">
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
        </div>
"""
content = re.sub(r'        <div className="p-6 border-t border-gray-800">.*?</div>', toggle_btn, content, flags=re.DOTALL)

# Now apply all regex replacements
for pattern, replacement in replacements.items():
    content = re.sub(pattern, replacement, content)

with open("src/App.jsx", "w") as f:
    f.write(content)

