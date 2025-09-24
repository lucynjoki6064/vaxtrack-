import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import csv

# --- Database setup ---
def init_db():
    conn = sqlite3.connect("vaxtrack.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vaccines
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  person TEXT NOT NULL,
                  vaccine TEXT NOT NULL,
                  date TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# --- Functions ---
def add_record():
    def save_record():
        person = entry_person.get().strip()
        vaccine = entry_vaccine.get().strip()
        date = entry_date.get().strip()

        if not person or not vaccine or not date:
            messagebox.showwarning("Input Error", "All fields are required!")
            return

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Date Error", "Date must be in YYYY-MM-DD format")
            return

        conn = sqlite3.connect("vaxtrack.db")
        c = conn.cursor()
        c.execute("INSERT INTO vaccines (person, vaccine, date) VALUES (?, ?, ?)",
                  (person, vaccine, date))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Record added successfully!")
        add_window.destroy()

    add_window = tk.Toplevel(root)
    add_window.title("Add Vaccine Record")

    tk.Label(add_window, text="Person:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_person = tk.Entry(add_window, width=30)
    entry_person.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(add_window, text="Vaccine:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_vaccine = tk.Entry(add_window, width=30)
    entry_vaccine.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(add_window, text="Date (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    entry_date = tk.Entry(add_window, width=30)
    entry_date.grid(row=2, column=1, padx=5, pady=5)

    tk.Button(add_window, text="Save", width=15, command=save_record).grid(row=3, columnspan=2, pady=10)

def view_records(search_term=None):
    def refresh_records():
        for widget in frame_records.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("vaxtrack.db")
        c = conn.cursor()
        if search_term:
            c.execute("SELECT id, person, vaccine, date FROM vaccines WHERE person LIKE ? ORDER BY date ASC", 
                      ('%' + search_term + '%',))
        else:
            c.execute("SELECT id, person, vaccine, date FROM vaccines ORDER BY date ASC")
        records = c.fetchall()
        conn.close()

        if not records:
            tk.Label(frame_records, text="No records found.", font=("Arial", 10)).pack(pady=10)
            return

        tk.Label(frame_records, text="Person", font=("Arial", 10, "bold"), width=15).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(frame_records, text="Vaccine", font=("Arial", 10, "bold"), width=15).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame_records, text="Date", font=("Arial", 10, "bold"), width=12).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(frame_records, text="Actions", font=("Arial", 10, "bold"), width=20).grid(row=0, column=3, padx=5, pady=5)

        for i, (rid, person, vaccine, date) in enumerate(records, start=1):
            tk.Label(frame_records, text=person, width=15).grid(row=i, column=0, padx=5, pady=2)
            tk.Label(frame_records, text=vaccine, width=15).grid(row=i, column=1, padx=5, pady=2)
            tk.Label(frame_records, text=date, width=12).grid(row=i, column=2, padx=5, pady=2)
            tk.Button(frame_records, text="Edit", width=8, command=lambda r=rid: edit_record(r)).grid(row=i, column=3, padx=2)
            tk.Button(frame_records, text="Delete", width=8, command=lambda r=rid: delete_record(r, refresh_records)).grid(row=i, column=4, padx=2)

    view_window = tk.Toplevel(root)
    view_window.title("Vaccine Records")

    # --- Search bar ---
    frame_search = tk.Frame(view_window)
    frame_search.pack(pady=5)

    tk.Label(frame_search, text="Search by Person:").pack(side="left")
    entry_search = tk.Entry(frame_search, width=20)
    entry_search.pack(side="left", padx=5)

    def do_search():
        nonlocal search_term
        search_term = entry_search.get().strip()
        refresh_records()

    tk.Button(frame_search, text="Search", command=do_search).pack(side="left", padx=5)
    tk.Button(frame_search, text="Clear", command=lambda: [entry_search.delete(0, tk.END), clear_search()]).pack(side="left", padx=5)

    def clear_search():
        nonlocal search_term
        search_term = None
        refresh_records()

    # --- Export Button ---
    def export_csv():
        conn = sqlite3.connect("vaxtrack.db")
        c = conn.cursor()
        if search_term:
            c.execute("SELECT person, vaccine, date FROM vaccines WHERE person LIKE ? ORDER BY date ASC",
                      ('%' + search_term + '%',))
        else:
            c.execute("SELECT person, vaccine, date FROM vaccines ORDER BY date ASC")
        records = c.fetchall()
        conn.close()

        if not records:
            messagebox.showwarning("No Data", "No records to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV Files", "*.csv")],
                                                 title="Save as")
        if not file_path:
            return

        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Person", "Vaccine", "Date"])
            writer.writerows(records)

        messagebox.showinfo("Export Successful", f"Records exported to {file_path}")

    # --- Import Button ---
    def import_csv():
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")],
                                               title="Select CSV File")
        if not file_path:
            return

        imported_count = 0
        with open(file_path, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    person = row["Person"].strip()
                    vaccine = row["Vaccine"].strip()
                    date = row["Date"].strip()
                    datetime.strptime(date, "%Y-%m-%d")  # validate date

                    conn = sqlite3.connect("vaxtrack.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO vaccines (person, vaccine, date) VALUES (?, ?, ?)",
                              (person, vaccine, date))
                    conn.commit()
                    conn.close()
                    imported_count += 1
                except Exception:
                    continue  # skip bad rows

        messagebox.showinfo("Import Complete", f"Imported {imported_count} records from {file_path}")
        refresh_records()

    tk.Button(frame_search, text="Export CSV", command=export_csv).pack(side="left", padx=5)
    tk.Button(frame_search, text="Import CSV", command=import_csv).pack(side="left", padx=5)

    frame_records = tk.Frame(view_window)
    frame_records.pack(padx=10, pady=10)

    refresh_records()

def edit_record(record_id):
    def save_changes():
        person = entry_person.get().strip()
        vaccine = entry_vaccine.get().strip()
        date = entry_date.get().strip()

        if not person or not vaccine or not date:
            messagebox.showwarning("Input Error", "All fields are required!")
            return

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Date Error", "Date must be in YYYY-MM-DD format")
            return

        conn = sqlite3.connect("vaxtrack.db")
        c = conn.cursor()
        c.execute("UPDATE vaccines SET person=?, vaccine=?, date=? WHERE id=?",
                  (person, vaccine, date, record_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Record updated successfully!")
        edit_window.destroy()

    conn = sqlite3.connect("vaxtrack.db")
    c = conn.cursor()
    c.execute("SELECT person, vaccine, date FROM vaccines WHERE id=?", (record_id,))
    record = c.fetchone()
    conn.close()

    if not record:
        messagebox.showerror("Error", "Record not found!")
        return

    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Vaccine Record")

    tk.Label(edit_window, text="Person:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_person = tk.Entry(edit_window, width=30)
    entry_person.insert(0, record[0])
    entry_person.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(edit_window, text="Vaccine:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_vaccine = tk.Entry(edit_window, width=30)
    entry_vaccine.insert(0, record[1])
    entry_vaccine.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(edit_window, text="Date (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    entry_date = tk.Entry(edit_window, width=30)
    entry_date.insert(0, record[2])
    entry_date.grid(row=2, column=1, padx=5, pady=5)

    tk.Button(edit_window, text="Save Changes", width=15, command=save_changes).grid(row=3, columnspan=2, pady=10)

def delete_record(record_id, refresh_callback):
    if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
        return

    conn = sqlite3.connect("vaxtrack.db")
    c = conn.cursor()
    c.execute("DELETE FROM vaccines WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

    messagebox.showinfo("Deleted", "Record deleted successfully!")
    refresh_callback()

def check_reminders(show_message=True):
    today = datetime.today().date()
    upcoming = today + timedelta(days=3)

    conn = sqlite3.connect("vaxtrack.db")
    c = conn.cursor()
    c.execute("SELECT person, vaccine, date FROM vaccines")
    records = c.fetchall()
    conn.close()

    due_list = []
    for person, vaccine, date_str in records:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if today <= date_obj <= upcoming:
                due_list.append(f"{person} → {vaccine} on {date_obj}")
        except ValueError:
            continue

    if due_list:
        reminder_text = "\n".join(due_list)
        messagebox.showinfo("Upcoming Vaccines", f"The following vaccines are due soon:\n\n{reminder_text}")
    elif show_message:
        messagebox.showinfo("No Upcoming Vaccines", "No vaccines are due in the next 3 days.")

# --- Main App ---
init_db()

root = tk.Tk()
root.title("VaxTrack - Vaccination Tracker")
root.geometry("450x340")

tk.Label(root, text="💉 VaxTrack", font=("Arial", 16, "bold")).pack(pady=10)

tk.Button(root, text="Add Vaccine Record", width=40, command=add_record).pack(pady=5)
tk.Button(root, text="View / Search / Manage Records", width=40, command=view_records).pack(pady=5)
tk.Button(root, text="Check Upcoming Vaccines", width=40, command=lambda: check_reminders(show_message=True)).pack(pady=5)
tk.Button(root, text="Exit", width=40, command=root.destroy).pack(pady=20)

# Auto-check reminders at startup
check_reminders(show_message=False)

root.mainloop()
