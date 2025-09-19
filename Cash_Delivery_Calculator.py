try:
    import tkinter as tk
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tk"])
    import tkinter as tk

from tkinter import ttk, messagebox
from itertools import product
from math import ceil

# Container capacities in volume - organized by size categories
containers = {
    "Small Containers": {
        "Piggybank": 50,
        "Case": 150,
        "Gift Box": 180,
        "Small Box": 200,
        "Backpack": 300,
        "Flat Box": 340,
        "Small Travelbag": 350
    },
    "Medium Containers": {
        "Medium Box": 400,
        "Sportsbag": 500,
        "Large Box": 600,
        "Large Travelbag": 600,
        "Bank Bag": 650,
        "Suitcase": 700
    },
    "Large Containers": {
        "Shopping Cart": 1600,
        "Mattress": 2200,
        "Pallet": 2900,
        "XXL Box": 3650
    }
}

# Flatten containers for backward compatibility
flat_containers = {}
for category, items in containers.items():
    flat_containers.update(items)

# Denomination labels using proper Unicode characters - FIXED CURRENCY SYMBOLS
label_map = {
    "10000": "$100",
    "5000": "$50",
    "2000": "$20",
    "1000": "$10",
    "1000000": "¥10,000",  # Fixed: Using proper Yen symbol
    "500000": "¥5,000",   # Fixed: Using proper Yen symbol
    "100000": "¥1,000",   # Fixed: Using proper Yen symbol
    "10000e": "€100",     # Fixed: Using proper Euro symbol
    "5000e": "€50",       # Fixed: Using proper Euro symbol
    "2000e": "€20"        # Fixed: Using proper Euro symbol
}

def calculate_volume(denominations, combo):
    """Calculate total volume needed for the given denomination combination"""
    volume = 0
    for denom, count in zip(denominations, combo):
        # Each pack contains 100 bills, so total bills = count * 100
        total_bills = count * 100
        volume += (total_bills * 0.1) * 0.5
    return volume

def calculate_balance_score(denominations, max_counts, combo):
    """
    Calculate a balance score for a combination.
    Lower scores indicate better balance (preferring abundant denominations).
    """
    score = 0
    total_usage_ratio = 0
    
    for i, (denom, count) in enumerate(zip(denominations, combo)):
        if count > 0 and max_counts[i] > 0:
            # Usage ratio: how much of available stock we're using
            usage_ratio = count / max_counts[i]
            total_usage_ratio += usage_ratio
            
            # Penalty for high usage ratios (prefer using bills we have lots of)
            score += usage_ratio * 100
            
            # Bonus for using lower denominations when we have abundance
            if max_counts[i] >= 10:  # If we have plenty of this denomination
                abundance_bonus = max_counts[i] / 100  # Small bonus based on abundance
                score -= abundance_bonus
    
    # Add penalty for uneven distribution
    if len(combo) > 1:
        used_denoms = [count for count in combo if count > 0]
        if used_denoms:
            avg_usage = sum(used_denoms) / len(used_denoms)
            variance = sum((count - avg_usage) ** 2 for count in used_denoms) / len(used_denoms)
            score += variance * 0.1  # Small penalty for high variance
    
    return score

def create_sorted_counts_string(denominations, combo, currency):
    """
    Create a counts string sorted by denomination value (highest to lowest)
    For display purposes in both table and packing confirmation
    """
    # Create list of (denomination_value, count, label) tuples for non-zero counts
    denom_data = []
    for d, c in zip(denominations, combo):
        if c > 0:  # Only include non-zero counts
            label = label_map.get(str(d) + ('e' if currency == 'Euros' else ''), str(d))
            denom_data.append((d, c, label))
    
    # Sort by denomination value (highest first)
    denom_data.sort(key=lambda x: x[0], reverse=True)
    
    # Create the formatted string
    counts_str = ", ".join(f"{label}:{count}" for _, count, label in denom_data)
    return counts_str

def greedy_search(denominations, max_counts, desired_amount, max_results=30):
    """Original greedy search algorithm"""
    results = []
    def recurse(index, current_combo, current_total, total_packs):
        if len(results) >= max_results:
            return
        if current_total > desired_amount:
            return
        if index == len(denominations):
            if current_total == desired_amount:
                if not full_blocks_only.get() or total_packs % 30 == 0:
                    results.append((tuple(current_combo), total_packs, current_total))
            return
        denom = denominations[index]
        for count in reversed(range(min(max_counts[index], (desired_amount - current_total) // denom + 1) + 1)):
            recurse(index + 1, current_combo + [count], current_total + denom * count, total_packs + count)
    recurse(0, [], 0, 0)
    return results

def balanced_search(denominations, max_counts, desired_amount, max_results=50):
    """
    Enhanced search algorithm that prioritizes balanced distribution
    and using denominations where you have abundance.
    """
    results = []
    
    def recurse(index, current_combo, current_total, total_packs):
        if len(results) >= max_results * 2:  # Generate more results for sorting
            return
        if current_total > desired_amount:
            return
        if index == len(denominations):
            if current_total == desired_amount:
                if not full_blocks_only.get() or total_packs % 30 == 0:
                    results.append((tuple(current_combo), total_packs, current_total))
            return
        
        denom = denominations[index]
        max_possible = min(max_counts[index], (desired_amount - current_total) // denom)
        
        # For balanced approach, try different strategies
        ranges_to_try = []
        
        # Strategy 1: Try using more of abundant denominations
        if max_counts[index] >= 5:  # If we have plenty
            # Prioritize using a good chunk of abundant denominations
            preferred_usage = min(max_counts[index] // 2, max_possible)
            ranges_to_try.append(range(max(0, preferred_usage - 2), min(preferred_usage + 3, max_possible + 1)))
        
        # Strategy 2: Standard range but prioritize middle values for balance
        full_range = list(range(max_possible + 1))
        # Sort to try middle values first for better balance
        middle = len(full_range) // 2
        sorted_range = []
        for i in range(len(full_range)):
            if i % 2 == 0:
                idx = middle + i // 2
            else:
                idx = middle - (i + 1) // 2
            if 0 <= idx < len(full_range):
                sorted_range.append(full_range[idx])
        ranges_to_try.append(sorted_range)
        
        # Try all strategies
        tried_counts = set()
        for range_strategy in ranges_to_try:
            for count in range_strategy:
                if count not in tried_counts:
                    tried_counts.add(count)
                    recurse(index + 1, current_combo + [count], current_total + denom * count, total_packs + count)
    
    recurse(0, [], 0, 0)
    
    # Sort results by balance score (lower is better)
    if results:
        scored_results = []
        for combo, packs, total in results:
            balance_score = calculate_balance_score(denominations, max_counts, combo)
            scored_results.append((combo, packs, total, balance_score))
        
        # Sort by balance score, then by total packs
        scored_results.sort(key=lambda x: (x[3], x[1]))
        
        # Return top results without the score
        return [(combo, packs, total) for combo, packs, total, score in scored_results[:max_results]]
    
    return results

def clear_results_table():
    """Clear all results from the table to indicate job completion"""
    for i in tree.get_children():
        tree.delete(i)
    # Insert a completion message
    tree.insert("", tk.END, values=("Job completed - inventory updated", "", "", "", ""))

def calculate_splits():
    """Main calculation function that processes user input and generates results"""
    try:
        desired_amount = int(amount_var.get())
        currency = currency_var.get()

        # Prepare denomination inputs based on selected currency
        denom_inputs = []
        if currency == "Dollars":
            denom_inputs = [(10000, d10k_var), (5000, d5k_var), (2000, d2k_var), (1000, d1k_var)]
        elif currency == "Euros":
            denom_inputs = [(10000, e10k_var), (5000, e5k_var), (2000, e2k_var)]
        elif currency == "Yen":
            denom_inputs = [(1000000, y1m_var), (500000, y500k_var), (100000, y100k_var)]

        # Handle "Only" and "Priority" modes
        only_selected = [value for value, var in only_vars.items() if var.get()]
        priority_selected = [value for value, var in priority_vars.items() if var.get()]

        # If "Only" is selected, use only that denomination
        if only_selected:
            denominations = []
            max_counts = []
            for value, var in denom_inputs:
                # Convert value to string for comparison with only_selected
                value_str = str(value) + ('e' if currency == 'Euros' else '')
                if value_str in only_selected:
                    count_str = var.get().strip()
                    if not count_str:
                        continue
                    max_count = int(count_str)
                    max_useful = min(max_count, desired_amount // value + 1)
                    denominations.append(value)
                    max_counts.append(max_useful)
            allow_partial_packs = True
        else:
            # If "Priority" is selected, sort inputs so priority denominations come first
            allow_partial_packs = False
            if priority_selected:
                # Convert priority_selected to match the value format
                priority_values = []
                for p in priority_selected:
                    if p.endswith('e'):
                        priority_values.append(int(p[:-1]))
                    else:
                        priority_values.append(int(p))
                denom_inputs.sort(key=lambda x: (x[0] not in priority_values, -x[0]))

            # Process all valid denominations
            denominations = []
            max_counts = []
            for value, var in denom_inputs:
                count_str = var.get().strip()
                if not count_str:
                    continue
                max_count = int(count_str)
                max_useful = min(max_count, desired_amount // value)
                if max_useful == 0:
                    continue
                denominations.append(value)
                max_counts.append(max_useful)

        if not denominations:
            for i in tree.get_children(): tree.delete(i)
            tree.insert("", tk.END, values=("No valid denominations", "", "", "", ""))
            return

        # Choose algorithm based on balanced mode
        if balanced_mode.get():
            results = balanced_search(denominations, max_counts, desired_amount)
        else:
            results = greedy_search(denominations, max_counts, desired_amount)

        container_name = container_var.get()
        container_capacity = flat_containers.get(container_name, 1)

        # Clear previous results
        for i in tree.get_children(): tree.delete(i)

        if results:
            # For regular mode, sort by packs; for balanced mode, results are already optimally sorted
            if not balanced_mode.get():
                results.sort(key=lambda x: x[1])
            
            # Display results in the table
            for combo, packs, total in results:
                blocks = packs // 30
                volume = calculate_volume(denominations, combo)
                containers_needed = ceil(volume / container_capacity)
                
                # Use the new sorted counts string function
                counts_str = create_sorted_counts_string(denominations, combo, currency)
                
                # Add balance indicator for balanced mode using ASCII characters
                balance_indicator = ""
                if balanced_mode.get():
                    balance_score = calculate_balance_score(denominations, max_counts, combo)
                    if balance_score < 50:
                        balance_indicator = " *VB"  # Very balanced
                    elif balance_score < 100:
                        balance_indicator = " *GB"  # Good balance
                
                tree.insert("", tk.END, values=(
                    counts_str + balance_indicator, packs, blocks, int(volume), f"{containers_needed} x {container_name}"
                ))
        else:
            tree.insert("", tk.END, values=("No valid combinations found", "", "", "", ""))
        
        # Save current state to memory
        save_memory()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def setup_result_table(root):
    """Create and configure the results table"""
    columns = ("Counts", "Packs", "Blocks", "Volume", "Containers Needed")
    col_widths = {
        "Counts": 380,  # Increased width for balance indicators
        "Packs": 60,
        "Blocks": 70,
        "Volume": 70,
        "Containers Needed": 180
    }

    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))
        tree.column(col, width=col_widths[col], anchor="center")
    tree.grid(row=4, column=0, columnspan=12, sticky="ew", pady=(0, 20))
    return tree

current_sort = {"column": None, "reverse": False}

def sort_column(tv, col, reverse):
    """Sort table column when header is clicked"""
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    try:
        l.sort(key=lambda t: float(t[0].split()[0]) if t[0].split()[0].replace('.', '', 1).isdigit() else t[0], reverse=reverse)
    except Exception:
        l.sort(key=lambda t: t[0], reverse=reverse)

    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    # Remove arrows from all columns
    for c in tv["columns"]:
        tv.heading(c, text=c, command=lambda _col=c: sort_column(tv, _col, False))

    # Add arrow to the sorted column using ASCII characters
    arrow = "v" if reverse else "^"
    tv.heading(col, text=f"{col} {arrow}", command=lambda: sort_column(tv, col, not reverse))

    current_sort["column"] = col
    current_sort["reverse"] = reverse

def create_container_selection():
    """Create the container selection UI with grouped buttons"""
    global container_buttons, current_container_button, container_frame
    
    container_frame = tk.Frame(root)
    container_frame.grid(row=1, column=0, columnspan=12, sticky="ew", pady=(0, 20))
    
    # Title
    tk.Label(container_frame, text="Select Container Type:", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
    
    container_buttons = {}
    current_container_button = None
    
    # Create buttons for each category
    row_offset = 1
    for category, items in containers.items():
        # Category label
        category_label = tk.Label(container_frame, text=category, font=("Arial", 9, "bold"), fg="#666666")
        category_label.grid(row=row_offset, column=0, columnspan=4, sticky="w", pady=(10, 5))
        row_offset += 1
        
        # Container buttons in this category (max 4 per row)
        col = 0
        for container_name, capacity in items.items():
            btn = tk.Button(container_frame, 
                          text=f"{container_name}\n({capacity})",
                          command=lambda name=container_name: select_container(name),
                          width=12, height=2,
                          relief="raised",
                          borderwidth=2,
                          font=("Arial", 8))
            btn.grid(row=row_offset, column=col, padx=5, pady=2, sticky="ew")
            container_buttons[container_name] = btn
            
            col += 1
            if col >= 4:  # Start new row after 4 buttons
                col = 0
                row_offset += 1
        
        if col > 0:  # If we didn't complete a full row, move to next row
            row_offset += 1
    
    return container_frame

def select_container(container_name):
    """Handle container selection and visual feedback"""
    global current_container_button
    
    # Reset previous selection
    if current_container_button:
        reset_button_style(current_container_button)
    
    # Set new selection
    container_var.set(container_name)
    current_container_button = container_buttons[container_name]
    
    # Highlight selected button with green background
    current_container_button.configure(bg="#4CAF50", fg="white", relief="sunken", borderwidth=3)

def reset_button_style(button):
    """Reset button to default style based on current theme"""
    theme = theme_var.get()
    if theme == "dark":
        button.configure(bg="#3e3e3e", fg="white", relief="raised", borderwidth=2)
    else:
        button.configure(bg="#f0f0f0", fg="black", relief="raised", borderwidth=2)

def get_theme_colors():
    """Get current theme colors"""
    theme = theme_var.get()
    if theme == "dark":
        return {
            "bg": "#2e2e2e", 
            "fg": "#ffffff",
            "entry_bg": "#3e3e3e", 
            "entry_fg": "#ffffff",
            "tree_bg": "#3e3e3e", 
            "tree_fg": "#ffffff",
            "highlight": "#555555",
            "button_bg": "#3e3e3e", 
            "button_fg": "#ffffff",
            "frame_bg": "#2e2e2e",
            "label_fg": "#ffffff",
            "category_fg": "#cccccc",
            "dialog_bg": "#2e2e2e",
            "section_bg": "#1a1a1a",
            "text_color": "#ffffff"
        }
    else:
        return {
            "bg": "#f0f0f0", 
            "fg": "#000000",
            "entry_bg": "#ffffff", 
            "entry_fg": "#000000",
            "tree_bg": "#ffffff", 
            "tree_fg": "#000000",
            "highlight": "#cccccc",
            "button_bg": "#f0f0f0", 
            "button_fg": "#000000",
            "frame_bg": "#f0f0f0",
            "label_fg": "#000000",
            "category_fg": "#666666",
            "dialog_bg": "#f0f8ff",
            "section_bg": "#e8f4fd",
            "text_color": "#000000"
        }

def apply_theme(theme):
    """Comprehensive theme application for all UI elements"""
    colors = get_theme_colors()
    
    # Apply to root window
    root.configure(bg=colors["bg"])

    # Comprehensive recursive theme application
    def apply_recursive(widget):
        widget_class = widget.__class__.__name__
        try:
            if widget_class in ["Label"]:
                widget.configure(bg=colors["bg"], fg=colors["label_fg"])
            elif widget_class in ["Button"]:
                widget.configure(bg=colors["button_bg"], fg=colors["button_fg"])
            elif widget_class == "Frame":
                widget.configure(bg=colors["frame_bg"])
            elif widget_class == "Checkbutton":
                widget.configure(bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"], 
                               activebackground=colors["bg"], activeforeground=colors["fg"])
            elif widget_class == "Radiobutton":
                widget.configure(bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"], 
                               activebackground=colors["bg"], activeforeground=colors["fg"])
            elif widget_class in ["Entry", "Text"]:
                widget.configure(bg=colors["entry_bg"], fg=colors["entry_fg"], insertbackground=colors["entry_fg"])
        except Exception:
            pass  # Some widgets may not support certain configurations
        
        # Apply to all child widgets
        for child in widget.winfo_children():
            apply_recursive(child)

    # Apply theme recursively to all widgets
    apply_recursive(root)

    # Special handling for container buttons
    if 'container_buttons' in globals():
        for container_name, button in container_buttons.items():
            if container_var.get() == container_name:
                # Keep selected button highlighted in green
                button.configure(bg="#4CAF50", fg="white", relief="sunken", borderwidth=3)
            else:
                # Apply theme to non-selected buttons
                button.configure(bg=colors["button_bg"], fg=colors["button_fg"], relief="raised", borderwidth=2)

    # Special handling for currency radio buttons
    if 'currency_radios' in globals():
        for radio in currency_radios:
            try:
                radio.configure(bg=colors["bg"], fg=colors["fg"], selectcolor=colors["bg"], 
                              activebackground=colors["bg"], activeforeground=colors["fg"])
            except Exception:
                pass

    # Apply theme to specific named elements
    try:
        instruction_label.configure(bg=colors["bg"], fg="#888888")
        apply_button.configure(bg="#2196F3", fg="white")  # Keep blue color for apply button
        calculate_button.configure(bg="#4CAF50", fg="white")  # Keep green color for calculate button
    except Exception:
        pass

    # Configure ttk styles for treeview and other ttk widgets
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
        background=colors["tree_bg"],
        foreground=colors["tree_fg"],
        fieldbackground=colors["tree_bg"],
        highlightthickness=0,
        rowheight=24
    )
    style.map("Treeview", background=[("selected", colors["highlight"])])

def show_packing_confirmation():
    """Show a large confirmation dialog with packing details sorted by denomination (highest to lowest)"""
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("No Selection", "Please select a result from the table first.")
        return
    
    # Get the selected row data
    item = tree.item(selection[0])
    values = item['values']
    
    if values[0] == "No valid denominations" or values[0] == "No valid combinations found" or values[0] == "Job completed - inventory updated":
        return
    
    # Parse the counts string and create detailed packing information
    counts_str = values[0].replace(" *VB", "").replace(" *GB", "")
    currency = currency_var.get()
    job_amount = amount_var.get()
    container = container_var.get()
    packs = values[1]
    blocks = values[2]
    volume = values[3]
    containers_info = values[4]
    
    # Get current theme colors
    colors = get_theme_colors()
    
    # Count the number of denominations to calculate required window height
    num_denominations = len([part for part in counts_str.split(", ") if ":" in part])
    
    # Calculate dynamic window height based on content
    # Base height components:
    # - Title: ~40px
    # - Job amount section: ~70px  
    # - Packing details header: ~50px
    # - Each denomination line: ~30px
    # - Spacing after denominations: ~20px
    # - Summary section: ~160px
    # - Button section: ~100px
    # - Total padding: ~120px
    base_height = 40 + 70 + 50 + 20 + 160 + 100 + 150
    denomination_height = num_denominations * 30
    calculated_height = base_height + denomination_height
    
    # Set minimum and maximum window sizes
    min_height = 500
    max_height = 900
    window_height = max(min_height, min(calculated_height, max_height))
    window_width = 700
    
    # Create confirmation dialog window
    confirm_window = tk.Toplevel(root)
    confirm_window.title("PACKING CONFIRMATION")
    confirm_window.configure(bg=colors["dialog_bg"])
    confirm_window.resizable(True, True)  # Allow resizing
    
    # Make the window appear in front of the main window
    confirm_window.transient(root)  # Set as child of main window
    confirm_window.grab_set()       # Make it modal
    confirm_window.focus_set()      # Give it focus
    confirm_window.lift()           # Bring to front
    confirm_window.attributes('-topmost', True)  # Keep on top temporarily
    
    # Position popup window in front of and centered on the main program window
    # This works correctly with multi-monitor setups
    root.update_idletasks()  # Ensure main window geometry is fully calculated
    
    # Get main window's absolute position and size
    main_x = root.winfo_rootx()  # Use rootx/rooty for multi-monitor support
    main_y = root.winfo_rooty()
    main_width = root.winfo_width()
    main_height = root.winfo_height()
    
    # Calculate center position relative to main window (works on any monitor)
    popup_x = main_x + (main_width - window_width) // 2
    popup_y = main_y + (main_height - window_height) // 2
    
    # Apply the geometry - this will place it on the same monitor as the main window
    confirm_window.geometry(f"{window_width}x{window_height}+{popup_x}+{popup_y}")
    
    # Additional steps to ensure popup appears on correct monitor and in front
    confirm_window.update_idletasks()  # Force geometry update
    confirm_window.deiconify()         # Ensure window is visible
    confirm_window.lift()              # Bring to front
    confirm_window.focus_force()       # Force focus to popup
    
    # If content might be too long, use a scrollable frame
    if calculated_height > max_height:
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(confirm_window, bg=colors["dialog_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(confirm_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors["dialog_bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y", pady=20)
        
        main_frame = scrollable_frame
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    else:
        # Create main frame without scrolling
        main_frame = tk.Frame(confirm_window, bg=colors["dialog_bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Main title with themed colors
    title_label = tk.Label(main_frame, text="PACKING DETAILS", 
                          font=("Arial", 20, "bold"), 
                          bg=colors["dialog_bg"], fg=colors["text_color"])
    title_label.pack(pady=(0, 15))
    
    # Job amount section with themed colors
    job_frame = tk.Frame(main_frame, bg=colors["section_bg"], relief="raised", borderwidth=2)
    job_frame.pack(fill="x", pady=(0, 15))
    
    tk.Label(job_frame, text=f"Job Amount: {job_amount} {currency}", 
             font=("Arial", 16, "bold"), bg=colors["section_bg"], fg="#2980b9").pack(pady=15)
    
    # Packing details section with themed colors
    details_frame = tk.Frame(main_frame, bg=colors["section_bg"], relief="raised", borderwidth=2)
    details_frame.pack(fill="x", pady=(0, 15))
    
    tk.Label(details_frame, text="PACK THE FOLLOWING (Highest to Lowest):", 
             font=("Arial", 14, "bold"), bg=colors["section_bg"], fg="#856404").pack(pady=(15, 10))
    
    # Parse and display each denomination (already sorted by create_sorted_counts_string)
    for part in counts_str.split(", "):
        if ":" in part:
            denom_label, count = part.split(":")
            pack_text = f"* {count} packs of {denom_label} bills"
            tk.Label(details_frame, text=pack_text, 
                     font=("Arial", 14), bg=colors["section_bg"], fg=colors["text_color"]).pack(pady=3)
    
    # Add some spacing after denomination list
    tk.Label(details_frame, text="", bg=colors["section_bg"]).pack(pady=5)
    
    # Summary information with themed colors
    summary_frame = tk.Frame(main_frame, bg=colors["section_bg"], relief="raised", borderwidth=2)
    summary_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(summary_frame, text="SUMMARY:", 
             font=("Arial", 12, "bold"), bg=colors["section_bg"], fg="#0c5460").pack(pady=(15, 10))
    
    summary_info = [
        f"Total Packs: {packs}",
        f"Full Blocks: {blocks}",
        f"Volume: {volume}",
        f"Container: {containers_info}"
    ]
    
    for info in summary_info:
        tk.Label(summary_frame, text=info, 
                 font=("Arial", 11), bg=colors["section_bg"], fg=colors["text_color"]).pack(pady=2)
    
    # Add some spacing after summary
    tk.Label(summary_frame, text="", bg=colors["section_bg"]).pack(pady=10)
    
    # Button frame - positioned at the bottom with fixed position
    # If using scrollable frame, buttons should be outside the scroll area
    if calculated_height > max_height:
        button_frame = tk.Frame(confirm_window, bg=colors["dialog_bg"])
        button_frame.pack(side="bottom", fill="x", padx=20, pady=(0, 20))
    else:
        button_frame = tk.Frame(main_frame, bg=colors["dialog_bg"])
        button_frame.pack(side="bottom", fill="x", pady=(5, 0))
    
    # Configure button frame columns for equal distribution
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    
    # Define button commands
    def confirm_packing():
        """Confirm the packing and update inventory"""
        try:
            # Subtract the used amounts from inventory
            subtract_used_amounts(counts_str)
            # Clear the results table to indicate completion
            clear_results_table()
            # Save the updated state
            save_memory()
            # Close the confirmation window silently
            confirm_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error confirming packing: {str(e)}")
    
    def cancel_packing():
        """Cancel and return to the previous step"""
        # Close the confirmation window without making any changes
        confirm_window.destroy()
    
    # CONFIRM button - appropriately sized
    confirm_btn = tk.Button(button_frame, 
                           text="CONFIRM\nPACKING", 
                           command=confirm_packing,
                           font=("Arial", 12, "bold"), 
                           bg="#28a745", 
                           fg="white", 
                           width=14,
                           height=2,
                           relief="raised", 
                           borderwidth=3,
                           cursor="hand2")
    confirm_btn.grid(row=0, column=0, padx=15, pady=5, sticky="ew")
    
    # CANCEL button - appropriately sized
    cancel_btn = tk.Button(button_frame, 
                          text="CANCEL\nRETURN", 
                          command=cancel_packing,
                          font=("Arial", 12, "bold"), 
                          bg="#dc3545", 
                          fg="white", 
                          width=14,
                          height=2,
                          relief="raised", 
                          borderwidth=3,
                          cursor="hand2")
    cancel_btn.grid(row=0, column=1, padx=15, pady=5, sticky="ew")
    
    # Set minimum window size to ensure buttons are always visible
    confirm_window.minsize(600, 400)
    
    # Remove topmost after a short delay to allow normal window interaction
    confirm_window.after(500, lambda: confirm_window.attributes('-topmost', False))
    
    # Force window to update and ensure buttons are visible
    confirm_window.update_idletasks()

def subtract_used_amounts(counts_str):
    """Subtract the used amounts from the denomination variables"""
    currency = currency_var.get()
    
    # Parse and apply the counts
    for part in counts_str.split(", "):
        if ":" in part:
            denom_label, count = part.split(":")
            count = int(count)
            
            # Find the corresponding denomination variable
            for denom_str, var in all_denom_vars.items():
                # Skip denominations that don't belong to current currency
                if currency == "Dollars" and (denom_str.endswith('e') or len(denom_str) > 5):
                    continue
                elif currency == "Euros" and not denom_str.endswith('e'):
                    continue
                elif currency == "Yen" and (denom_str.endswith('e') or len(denom_str) <= 5):
                    continue
                
                # Convert denomination to label for comparison
                try:
                    if currency == "Euros" and denom_str.endswith('e'):
                        denom_value = int(denom_str[:-1])
                        label = label_map.get(f"{denom_value}e", str(denom_value))
                    else:
                        denom_value = int(denom_str)
                        label = label_map.get(denom_str, str(denom_value))
                    
                    if label == denom_label:
                        # Get current value and subtract the used amount
                        current_str = var.get().strip()
                        if current_str:
                            current = int(current_str)
                            remaining = max(0, current - count)
                            var.set(str(remaining))
                        break
                except ValueError:
                    # Skip invalid denomination strings
                    continue

def on_result_click(event):
    """Handle clicking on a result row - now shows confirmation dialog"""
    show_packing_confirmation()

# Memory management functions
import json
import os

memory_file = "config.json"

default_memory = {
    "amount": "",
    "currency": "Dollars",
    "container": "Backpack",
    "denominations": {},
    "priority": {},
    "only": {},
    "balanced_mode": False
}

def load_memory():
    """Load saved configuration from file"""
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r") as f:
                return json.load(f)
        except Exception:
            return default_memory.copy()
    return default_memory.copy()

def save_memory():
    """Save current configuration to file"""
    memory = {
        "amount": amount_var.get(),
        "currency": currency_var.get(),
        "container": container_var.get(),
        "balanced_mode": balanced_mode.get(),
        "denominations": {},
        "priority": {},
        "only": {}
    }
    for denom, var in all_denom_vars.items():
        memory["denominations"][str(denom)] = var.get()
        memory["priority"][str(denom)] = priority_vars[denom].get()
        memory["only"][str(denom)] = only_vars[denom].get()
    
    try:
        with open(memory_file, "w") as f:
            json.dump(memory, f)
    except Exception:
        pass  # Silently fail if can't save

# GUI setup starts here
root = tk.Tk()
root.title("Cash Delivery Calculator")
root.configure(padx=20, pady=20)

# Initialize dictionaries for only and priority variables
only_vars = {}
priority_vars = {}

# Main input section - Row 0
input_frame = tk.Frame(root)
input_frame.grid(row=0, column=0, columnspan=12, sticky="ew", pady=(0, 20))

# Job amount input
tk.Label(input_frame, text="Job Amount:").grid(row=0, column=0, sticky="e", padx=(0, 10))
amount_var = tk.StringVar()
tk.Entry(input_frame, textvariable=amount_var, width=15).grid(row=0, column=1, padx=(0, 30))

# Currency selection with radio buttons
tk.Label(input_frame, text="Currency:").grid(row=0, column=2, sticky="e", padx=(0, 10))
currency_var = tk.StringVar(value="Dollars")
currency_radios = []

currency_frame = tk.Frame(input_frame)
currency_frame.grid(row=0, column=3, columnspan=3, sticky="w")

for i, currency in enumerate(["Dollars", "Euros", "Yen"]):
    radio = tk.Radiobutton(currency_frame, text=currency, variable=currency_var, value=currency,
                          font=("Arial", 10), padx=15)
    radio.grid(row=0, column=i, sticky="w")
    currency_radios.append(radio)

# Algorithm options - second row
full_blocks_only = tk.BooleanVar(value=False)
tk.Checkbutton(input_frame, text="Only allow full blocks (30 packs)", variable=full_blocks_only).grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))

balanced_mode = tk.BooleanVar(value=False)
tk.Checkbutton(input_frame, text="Smart Balance (prioritize abundant bills)", variable=balanced_mode, 
               fg="#4CAF50", font=("Arial", 9, "bold")).grid(row=1, column=3, columnspan=4, sticky="w", pady=(10, 0))

# Container selection with grouped buttons - Row 1
container_var = tk.StringVar(value="Backpack")
container_section = create_container_selection()

# Denominations section - Row 2
denom_frame = tk.Frame(root)
denom_frame.grid(row=2, column=0, columnspan=12, sticky="ew", pady=(0, 20))

# Section header
tk.Label(denom_frame, text="Enter number of full packs per denomination:", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=12, pady=(0, 15), sticky="w")

# Column headers
headers = ["Dollars", "Euros", "Yen"]
for i, header in enumerate(headers):
    tk.Label(denom_frame, text=header, font=("Arial", 9, "bold")).grid(row=1, column=i*3, sticky="w", padx=(0, 10))

# Dollar inputs
dollar_frame = tk.Frame(denom_frame)
dollar_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=(0, 30))

dollar_denoms = [10000, 5000, 2000, 1000]
d_vars = [tk.StringVar() for _ in dollar_denoms]
only_vars.update({str(d): tk.BooleanVar() for d in dollar_denoms})
priority_vars.update({str(d): tk.BooleanVar() for d in dollar_denoms})

for i, (denom, var) in enumerate(zip(dollar_denoms, d_vars)):
    tk.Label(dollar_frame, text=label_map[str(denom)]).grid(row=i, column=0, sticky="e", padx=(0, 10))
    tk.Entry(dollar_frame, textvariable=var, width=8).grid(row=i, column=1, padx=(0, 10))
    tk.Checkbutton(dollar_frame, text="Only", variable=only_vars[str(denom)]).grid(row=i, column=2, padx=(0, 10))
    tk.Checkbutton(dollar_frame, text="Priority", variable=priority_vars[str(denom)]).grid(row=i, column=3)

d10k_var, d5k_var, d2k_var, d1k_var = d_vars

# Euro inputs
euro_frame = tk.Frame(denom_frame)
euro_frame.grid(row=2, column=3, columnspan=3, sticky="ew", padx=(0, 30))

euro_denoms = [10000, 5000, 2000]
e_vars = [tk.StringVar() for _ in euro_denoms]
only_vars.update({f"{d}e": tk.BooleanVar() for d in euro_denoms})
priority_vars.update({f"{d}e": tk.BooleanVar() for d in euro_denoms})

for i, (denom, var) in enumerate(zip(euro_denoms, e_vars)):
    tk.Label(euro_frame, text=label_map[f"{denom}e"]).grid(row=i, column=0, sticky="e", padx=(0, 10))
    tk.Entry(euro_frame, textvariable=var, width=8).grid(row=i, column=1, padx=(0, 10))
    tk.Checkbutton(euro_frame, text="Only", variable=only_vars[f"{denom}e"]).grid(row=i, column=2, padx=(0, 10))
    tk.Checkbutton(euro_frame, text="Priority", variable=priority_vars[f"{denom}e"]).grid(row=i, column=3)

e10k_var, e5k_var, e2k_var = e_vars

# Yen inputs
yen_frame = tk.Frame(denom_frame)
yen_frame.grid(row=2, column=6, columnspan=3, sticky="ew")

yen_denoms = [1000000, 500000, 100000]
y_vars = [tk.StringVar() for _ in yen_denoms]
only_vars.update({str(d): tk.BooleanVar() for d in yen_denoms})
priority_vars.update({str(d): tk.BooleanVar() for d in yen_denoms})

for i, (denom, var) in enumerate(zip(yen_denoms, y_vars)):
    tk.Label(yen_frame, text=label_map[str(denom)]).grid(row=i, column=0, sticky="e", padx=(0, 10))
    tk.Entry(yen_frame, textvariable=var, width=8).grid(row=i, column=1, padx=(0, 10))
    tk.Checkbutton(yen_frame, text="Only", variable=only_vars[str(denom)]).grid(row=i, column=2, padx=(0, 10))
    tk.Checkbutton(yen_frame, text="Priority", variable=priority_vars[str(denom)]).grid(row=i, column=3)

y1m_var, y500k_var, y100k_var = y_vars

# Create dictionary of all denomination variables for easy access
all_denom_vars = {
    "10000": d10k_var, "5000": d5k_var, "2000": d2k_var, "1000": d1k_var,
    "10000e": e10k_var, "5000e": e5k_var, "2000e": e2k_var,
    "1000000": y1m_var, "500000": y500k_var, "100000": y100k_var
}

# Calculate button - Row 3
button_frame = tk.Frame(root)
button_frame.grid(row=3, column=0, columnspan=12, pady=20)

calculate_button = tk.Button(button_frame, text="Think for me", command=calculate_splits, 
                           font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", 
                           relief="raised", padx=20, pady=10)
calculate_button.pack()

# Results table - Row 4
tree = setup_result_table(root)

# Instruction label - Row 5
instruction_label = tk.Label(root, text="Select a result and click 'Use Packs' to see packing details and confirm\n*VB = Very Balanced Distribution  *GB = Good Balance", 
                            font=("Arial", 9), fg="#888888")
instruction_label.grid(row=5, column=0, columnspan=12, pady=(0, 10))

# Apply result button - Row 6
apply_button = tk.Button(root, text="Use Packs", command=lambda: on_result_click(None), 
                        font=("Arial", 10), bg="#2196F3", fg="white", 
                        relief="raised", padx=15, pady=5)
apply_button.grid(row=6, column=0, columnspan=12, pady=(0, 10))

# Theme selection - Row 7
theme_frame = tk.Frame(root)
theme_frame.grid(row=7, column=0, columnspan=12, pady=(0, 10))

tk.Label(theme_frame, text="Theme:").pack(side="left", padx=(0, 10))
theme_var = tk.StringVar(value="dark")
tk.Radiobutton(theme_frame, text="Flashbang", variable=theme_var, value="light", 
               command=lambda: apply_theme("light")).pack(side="left", padx=(0, 10))
tk.Radiobutton(theme_frame, text="Dark", variable=theme_var, value="dark", 
               command=lambda: apply_theme("dark")).pack(side="left")

# Load saved memory and apply settings
memory = load_memory()
amount_var.set(memory["amount"])
currency_var.set(memory["currency"])
container_var.set(memory["container"])
balanced_mode.set(memory.get("balanced_mode", False))

# Load denomination values
for denom_str, value in memory["denominations"].items():
    if denom_str in all_denom_vars:
        all_denom_vars[denom_str].set(value)

# Load priority and only settings
for denom_str, value in memory["priority"].items():
    if denom_str in priority_vars:
        priority_vars[denom_str].set(value)

for denom_str, value in memory["only"].items():
    if denom_str in only_vars:
        only_vars[denom_str].set(value)

# Initialize container selection and apply theme
select_container(container_var.get())
apply_theme("dark")

# Start the GUI main loop
root.mainloop()