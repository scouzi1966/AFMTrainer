#!/usr/bin/env python3
"""
Theme Demo Script - Shows the visual improvements with sv-ttk theme
"""

import tkinter as tk
from tkinter import ttk
import sys

try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    SV_TTK_AVAILABLE = False

def create_demo_window():
    """Create a demo window showing theme improvements."""
    root = tk.Tk()
    root.title("AFM Trainer - Theme Demo")
    root.geometry("600x400")
    
    # Apply theme
    if SV_TTK_AVAILABLE:
        sv_ttk.set_theme("dark")
        theme_name = "Sun Valley Dark Theme"
    else:
        style = ttk.Style()
        style.theme_use('clam')
        theme_name = "Enhanced Default Theme"
    
    # Create demo interface
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill="both", expand=True)
    
    # Header
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 20))
    
    title_frame = ttk.Frame(header_frame)
    title_frame.pack(anchor="w")
    
    icon_label = ttk.Label(title_frame, text="🧠", font=("Arial", 20))
    icon_label.pack(side="left", padx=(0, 10))
    
    title_label = ttk.Label(title_frame, text="AFM Trainer", font=("Arial", 18, "bold"))
    title_label.pack(side="left")
    
    subtitle_label = ttk.Label(header_frame, text=f"Using: {theme_name}", font=("Arial", 10))
    subtitle_label.pack(anchor="w", pady=(5, 0))
    
    # Notebook demo
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, pady=(0, 20))
    
    # Tab 1
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="🔧 Setup")
    
    group1 = ttk.LabelFrame(tab1, text="🔧 Configuration", padding="10")
    group1.pack(fill="x", padx=10, pady=10)
    
    ttk.Label(group1, text="Sample Entry:", font=("Arial", 9, "bold")).pack(anchor="w")
    ttk.Entry(group1, value="Modern styled entry field").pack(fill="x", pady=5)
    
    # Tab 2
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="⚙️ Training")
    
    group2 = ttk.LabelFrame(tab2, text="⚙️ Parameters", padding="10")
    group2.pack(fill="x", padx=10, pady=10)
    
    param_frame = ttk.Frame(group2)
    param_frame.pack(fill="x", pady=5)
    ttk.Label(param_frame, text="Learning Rate:", width=15).pack(side="left")
    ttk.Entry(param_frame, value="1e-4", width=10).pack(side="left")
    
    ttk.Checkbutton(group2, text="Enable Modern Styling").pack(anchor="w", pady=5)
    
    # Progress demo
    ttk.Label(group2, text="Progress Demo:").pack(anchor="w", pady=(10, 5))
    progress = ttk.Progressbar(group2, mode='determinate', value=70)
    progress.pack(fill="x", pady=5)
    
    # Button demo
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x")
    
    ttk.Button(button_frame, text="✓ Normal Button").pack(side="left", padx=(0, 5))
    ttk.Button(button_frame, text="🚀 Accent Button", style="Accent.TButton").pack(side="left", padx=(0, 5))
    
    if SV_TTK_AVAILABLE:
        theme_var = tk.StringVar(value="dark")
        ttk.Label(button_frame, text="Theme:").pack(side="right", padx=(10, 5))
        theme_combo = ttk.Combobox(button_frame, textvariable=theme_var,
                                 values=["dark", "light"], width=8, state="readonly")
        theme_combo.pack(side="right")
        
        def change_theme(event):
            sv_ttk.set_theme(theme_var.get())
            subtitle_label.config(text=f"Using: Sun Valley {theme_var.get().capitalize()} Theme")
        
        theme_combo.bind("<<ComboboxSelected>>", change_theme)
    
    # Instructions
    info_text = f"""
Theme Features Demonstrated:
• Modern {theme_name.lower()} styling
• Enhanced visual hierarchy with icons
• Improved button and entry styling
• Professional color scheme
• Better typography and spacing
{"• Real-time theme switching (dark/light)" if SV_TTK_AVAILABLE else "• Fallback styling for compatibility"}

This is how AFM Trainer now looks with the enhanced theme!
    """
    
    info_label = ttk.Label(main_frame, text=info_text.strip(), 
                          font=("Arial", 9), justify="left")
    info_label.pack(pady=(10, 0))
    
    return root

if __name__ == "__main__":
    try:
        root = create_demo_window()
        print("🎨 AFM Trainer Theme Demo")
        print("=" * 40)
        print(f"sv-ttk available: {'✅ Yes' if SV_TTK_AVAILABLE else '❌ No (using fallback)'}")
        print("Close the window to exit the demo")
        print("=" * 40)
        
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n👋 Demo ended")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        sys.exit(1)