import traceback, sys, os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def app_dir():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

from pathlib import Path

def log_exception_to_file(exc_text):
    log_file = Path.home() / "crash.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(exc_text + "\n")

from db_config import current_user
from auth import login_user, logout_user
from student_ops import (
    fetch_all_students,
    search_students_by_department,
    fetch_own_record,
    fetch_all_subjects,
    fetch_student_subject_marks,
    add_student,
    update_student,
    update_student_marks,
    delete_student
)
from analytics import (
    fetch_dashboard_stats,
    fetch_top_performers,
    fetch_marks_distribution,
    fetch_department_analytics,
    fetch_department_leaderboard,
    add_bonus_marks,
    export_high_performers
)
from user_mgmt import (
    fetch_users,
    create_user,
    toggle_user,
    create_mysql_users,
    fetch_audit_log
)
from subject import (
    fetch_faculty_subjects,
    fetch_all_subject_marks,
    fetch_my_subject_marks
)

class SPAApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Performance Analyzer")
        self.root.geometry("1180x700")
        self.root.configure(bg="#f4f6f8")
        self.apply_style()
        self.login_screen()

    def apply_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def open_form_popup(self, title, fields, submit_callback):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("400x350")
        popup.configure(bg="white")
        popup.grab_set()

        entries = {}

        tk.Label(
            popup,
            text=title,
            font=("Arial", 15, "bold"),
            bg="white",
            fg="#1f4e79"
        ).pack(pady=15)

        form_frame = tk.Frame(popup, bg="white")
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for label_text, field_name in fields:
            tk.Label(
                form_frame,
                text=label_text,
                bg="white",
                font=("Arial", 11)
            ).pack(anchor="w", pady=(8, 2))
            entry = tk.Entry(form_frame, font=("Arial", 11))
            entry.pack(fill="x", pady=4)
            entries[field_name] = entry

        def submit():
            values = {name: entry.get().strip() for name, entry in entries.items()}
            submit_callback(values, popup)

        tk.Button(
            popup,
            text="Submit",
            font=("Arial", 11, "bold"),
            bg="#1f77b4",
            fg="white",
            command=submit
        ).pack(pady=15)

    def login_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg="white", bd=2, relief="ridge")
        frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=300)

        tk.Label(
            frame,
            text="Student Performance Analyzer",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#1f4e79"
        ).pack(pady=20)

        tk.Label(frame, text="Username", bg="white", font=("Arial", 11)).pack(pady=5)
        self.username_entry = tk.Entry(frame, font=("Arial", 11))
        self.username_entry.pack(pady=5)

        tk.Label(frame, text="Password", bg="white", font=("Arial", 11)).pack(pady=5)
        self.password_entry = tk.Entry(frame, show="*", font=("Arial", 11))
        self.password_entry.pack(pady=5)

        tk.Button(
            frame,
            text="Login",
            font=("Arial", 11, "bold"),
            bg="#1f77b4",
            fg="white",
            width=15,
            command=self.login
        ).pack(pady=20)

    def login(self):
        try:
            success, msg = login_user(self.username_entry.get(), self.password_entry.get())
            if success:
                self.dashboard_screen()
            else:
                messagebox.showerror("Login Failed", msg)
        except Exception as e:
            err = traceback.format_exc()
            log_exception_to_file(err)
            messagebox.showerror("Login Crash", str(e))

    def dashboard_screen(self):
        self.clear_screen()

        header = tk.Frame(self.root, bg="#1f4e79", height=60)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"Welcome, {current_user['username']} ({current_user['role'].upper()})",
            font=("Arial", 16, "bold"),
            bg="#1f4e79",
            fg="white"
        ).pack(side="left", padx=20, pady=15)

        tk.Button(
            header,
            text="Logout",
            bg="#d9534f",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.logout
        ).pack(side="right", padx=20, pady=15)

        sidebar_outer = tk.Frame(self.root, bg="#d9e6f2", width=240)
        sidebar_outer.pack(side="left", fill="y")
        sidebar_outer.pack_propagate(False)

        sidebar_canvas = tk.Canvas(sidebar_outer, bg="#d9e6f2", highlightthickness=0, width=240)
        sidebar_scrollbar = ttk.Scrollbar(sidebar_outer, orient="vertical", command=sidebar_canvas.yview)
        sidebar = tk.Frame(sidebar_canvas, bg="#d9e6f2")

        sidebar.bind("<Configure>", lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all")))
        sidebar_canvas.create_window((0, 0), window=sidebar, anchor="nw")
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
        sidebar_canvas.pack(side="left", fill="both", expand=True)
        sidebar_scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            sidebar_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        sidebar_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.content = tk.Frame(self.root, bg="#f4f6f8")
        self.content.pack(side="right", fill="both", expand=True)

        role = current_user["role"]
        buttons = [("Dashboard", self.show_dashboard_stats)]

        if role in ["admin", "faculty"]:
            buttons.extend([
                ("View Students", self.view_students),
                ("Search by Dept", self.search_by_department),
                ("Add Student", self.add_student_gui),
                ("Add/Update Subject Marks", self.add_update_subject_marks_gui),
                ("Top Performers", self.show_top_performers),
                ("Analytics", self.show_analytics),
                ("Marks Distribution", self.show_marks_distribution),
                ("Department Leaderboard", self.show_department_leaderboard),
                ("Add Bonus Marks", self.add_bonus_marks_gui),
                ("Export High Performers", self.export_high_performers_gui),
                ("All Subjects", self.show_all_subjects),
                ("Faculty Subjects", self.show_faculty_subjects),
                ("All Subject Marks", self.show_all_subject_marks)
            ])

        if role == "admin":
            buttons.extend([
                ("Update Student", self.update_student_gui),
                ("Delete Student", self.delete_student_gui),
                ("Users", self.list_users),
                ("Create User", self.create_user_gui),
                ("Toggle User", self.toggle_user_gui),
                ("Create MySQL Users", self.create_mysql_users_gui),
                ("Audit Log", self.view_audit_log)
            ])

        if role == "student":
            buttons.extend([
                ("View Own Record", self.view_own_record),
                ("Top Performers", self.show_top_performers),
                ("My Subject Marks", self.show_my_subject_marks)
            ])

        for text, cmd in buttons:
            tk.Button(
                sidebar,
                text=text,
                font=("Arial", 11, "bold"),
                width=20,
                bg="white",
                command=cmd
            ).pack(pady=8, padx=10, fill="x")

        self.show_dashboard_stats()

    def create_treeview(self, columns, rows, title):
        self.clear_content()
        tk.Label(self.content, text=title, font=("Arial", 16, "bold"), bg="#f4f6f8", fg="#1f4e79").pack(pady=15)
        frame = tk.Frame(self.content, bg="#f4f6f8")
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor="center")
        for row in rows:
            clean_row = ["N/A" if value is None else value for value in row]
            tree.insert("", "end", values=clean_row)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_dashboard_stats(self):
        try:
            self.clear_content()
            row = fetch_dashboard_stats()
            cards = [
                ("Total Students", row[0]),
                ("Average Marks", row[1]),
                ("Highest Marks", row[2]),
                ("Lowest Marks", row[3])
            ]
            tk.Label(self.content, text="Live Dashboard", font=("Arial", 18, "bold"), bg="#f4f6f8", fg="#1f4e79").pack(pady=20)
            cards_frame = tk.Frame(self.content, bg="#f4f6f8")
            cards_frame.pack(pady=20)
            for i, (label, value) in enumerate(cards):
                card = tk.Frame(cards_frame, bg="white", bd=2, relief="groove", width=180, height=100)
                card.grid(row=0, column=i, padx=10)
                card.grid_propagate(False)
                tk.Label(card, text=label, font=("Arial", 12, "bold"), bg="white", fg="#333").pack(pady=10)
                tk.Label(card, text=str(value), font=("Arial", 16, "bold"), bg="white", fg="#1f77b4").pack()
        except Exception as e:
            messagebox.showerror("Error", f"Dashboard error: {e}")

    def view_students(self):
        try:
            self.create_treeview(["ID", "PRN", "Name", "Department", "Total", "Average", "Enrolled At"], fetch_all_students(), "All Students")
        except Exception as e:
            messagebox.showerror("Error", f"View students error: {e}")

    def search_by_department(self):
        dept = simpledialog.askstring("Search", "Enter department:")
        if not dept:
            return
        try:
            self.create_treeview(["ID", "Name", "Department", "Total", "Average"], search_students_by_department(dept), f"Students - {dept}")
        except Exception as e:
            messagebox.showerror("Error", f"Search error: {e}")

    def view_own_record(self):
        try:
            self.create_treeview(["ID", "Name", "Department", "Total", "Average", "Enrolled At"], fetch_own_record(), "My Record")
        except Exception as e:
            messagebox.showerror("Error", f"Own record error: {e}")

    def show_all_subjects(self):
        try:
            self.create_treeview(["Subject ID", "Subject Name", "Department", "Credits"], fetch_all_subjects(), "All Subjects")
        except Exception as e:
            messagebox.showerror("Error", f"All subjects error: {e}")

    def add_student_gui(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add Student")
        popup.geometry("450x420")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Add Student", font=("Arial", 15, "bold"), bg="white", fg="#1f4e79").pack(pady=15)
        form = tk.Frame(popup, bg="white")
        form.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(form, text="Name", bg="white", font=("Arial", 11)).pack(anchor="w", pady=(8, 2))
        name_entry = tk.Entry(form, font=("Arial", 11))
        name_entry.pack(fill="x", pady=4)

        tk.Label(form, text="Department", bg="white", font=("Arial", 11)).pack(anchor="w", pady=(8, 2))
        dept_entry = tk.Entry(form, font=("Arial", 11))
        dept_entry.pack(fill="x", pady=4)

        tk.Label(form, text="PRN / Username (optional)", bg="white", font=("Arial", 11)).pack(anchor="w", pady=(8, 2))
        prn_entry = tk.Entry(form, font=("Arial", 11))
        prn_entry.pack(fill="x", pady=4)

        tk.Label(form, text="Password (optional)", bg="white", font=("Arial", 11)).pack(anchor="w", pady=(8, 2))
        password_entry = tk.Entry(form, show="*", font=("Arial", 11))
        password_entry.pack(fill="x", pady=4)

        def submit():
            try:
                name = name_entry.get().strip()
                department = dept_entry.get().strip()
                prn = prn_entry.get().strip() or None
                password = password_entry.get().strip() or None
                if not name or not department:
                    messagebox.showwarning("Input Error", "Name and department are required.")
                    return
                if (prn and not password) or (password and not prn):
                    messagebox.showwarning("Input Error", "Enter both PRN and password, or leave both blank.")
                    return
                add_student(name, department, prn, password)
                popup.destroy()
                messagebox.showinfo("Success", "Student added successfully.")
                self.view_students()
            except Exception as e:
                messagebox.showerror("Error", f"Add student error: {e}")

        tk.Button(popup, text="Add Student", font=("Arial", 11, "bold"), bg="#1f77b4", fg="white", width=18, command=submit).pack(pady=20)

    def update_student_gui(self):
        def submit(values, popup):
            try:
                student_id = int(values["student_id"].strip())
                value = values["value"].strip()
                if not value:
                    messagebox.showwarning("Invalid Input", "Department cannot be empty.")
                    return
                update_student(student_id, "department", value)
                popup.destroy()
                messagebox.showinfo("Success", "Student updated successfully.")
                self.view_students()
            except ValueError:
                messagebox.showwarning("Invalid Input", "Student ID must be a number.")
            except Exception as e:
                messagebox.showerror("Error", f"Update student error: {e}")

        self.open_form_popup("Update Student", [("Student ID", "student_id"), ("New Department", "value")], submit)

    def add_update_subject_marks_gui(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add/Update Subject Marks")
        popup.geometry("460x450")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Add/Update Subject Marks", font=("Arial", 15, "bold"), bg="white", fg="#1f4e79").pack(pady=15)
        form = tk.Frame(popup, bg="white")
        form.pack(fill="both", expand=True, padx=20, pady=10)

        fields = [("Student ID", "student_id"), ("Subject ID", "subject_id"), ("Faculty User ID", "faculty_user_id"), ("Marks", "marks")]
        entries = {}
        for label, key in fields:
            tk.Label(form, text=label, bg="white", font=("Arial", 11)).pack(anchor="w", pady=(8, 2))
            entry = tk.Entry(form, font=("Arial", 11))
            entry.pack(fill="x", pady=4)
            entries[key] = entry

        tk.Label(form, text="Exam Type", bg="white", font=("Arial", 11)).pack(anchor="w", pady=(8, 2))
        exam_type_var = tk.StringVar(value="Internal")
        exam_type_box = ttk.Combobox(form, textvariable=exam_type_var, values=["Internal"], state="readonly")
        exam_type_box.pack(fill="x", pady=4)

        def submit():
            try:
                student_id = int(entries["student_id"].get().strip())
                subject_id = int(entries["subject_id"].get().strip())
                faculty_user_id = int(entries["faculty_user_id"].get().strip())
                marks = float(entries["marks"].get().strip())
                exam_type = exam_type_var.get().strip()
                update_student_marks(student_id, subject_id, exam_type, marks, faculty_user_id)
                popup.destroy()
                messagebox.showinfo("Success", "Subject marks saved successfully.")
                self.show_all_subject_marks()
            except ValueError:
                messagebox.showwarning("Input Error", "Enter valid numeric values.")
            except Exception as e:
                messagebox.showerror("Error", f"Subject marks error: {e}")

        tk.Button(popup, text="Submit", font=("Arial", 11, "bold"), bg="#1f77b4", fg="white", width=18, command=submit).pack(pady=20)

    def show_all_subject_marks(self):
        try:
            self.create_treeview(["Student Name", "Department", "Subject Name", "Faculty Username", "Exam Type", "Marks", "Updated At"], fetch_all_subject_marks(), "All Subject Marks")
        except Exception as e:
            messagebox.showerror("Error", f"All subject marks error: {e}")

    def show_my_subject_marks(self):
        try:
            self.create_treeview(["Subject Name", "Faculty Username", "Exam Type", "Marks", "Updated At"], fetch_my_subject_marks(current_user["id"]), "My Subject Marks")
        except Exception as e:
            messagebox.showerror("Error", f"My subject marks error: {e}")

    def show_faculty_subjects(self):
        try:
            self.create_treeview(["Faculty Username", "Subject Name", "Department", "Credits"], fetch_faculty_subjects(), "Faculty Subjects")
        except Exception as e:
            messagebox.showerror("Error", f"Faculty subjects error: {e}")

    def show_top_performers(self):
        try:
            self.create_treeview(["ID", "Name", "Department", "Marks"], fetch_top_performers(), "Top 3 Performers")
        except Exception as e:
            messagebox.showerror("Error", f"Top performers error: {e}")

    def show_marks_distribution(self):
        try:
            self.create_treeview(["Grade", "Count"], fetch_marks_distribution(), "Marks Distribution")
        except Exception as e:
            messagebox.showerror("Error", f"Marks distribution error: {e}")

    def show_department_leaderboard(self):
        try:
            self.create_treeview(["Department", "Average Marks"], fetch_department_leaderboard(), "Department Leaderboard")
        except Exception as e:
            messagebox.showerror("Error", f"Leaderboard error: {e}")

    def show_analytics(self):
        try:
            self.clear_content()
            grades = fetch_marks_distribution()
            dept_rows = fetch_department_analytics()
            tk.Label(self.content, text="Analytics", font=("Arial", 16, "bold"), bg="#f4f6f8", fg="#1f4e79").pack(pady=10)
            chart_frame = tk.Frame(self.content, bg="white", bd=2, relief="groove")
            chart_frame.pack(pady=10, padx=20, fill="x")
            labels = [row[0] for row in grades]
            values = [row[1] for row in grades]
            fig = Figure(figsize=(4.5, 3.2), dpi=100)
            ax = fig.add_subplot(111)
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.set_title("Grade Distribution")
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=10)
            tk.Label(self.content, text="Department-wise Analytics", font=("Arial", 14, "bold"), bg="#f4f6f8", fg="#1f4e79").pack(pady=(20, 10))
            dept_frame = tk.Frame(self.content, bg="#f4f6f8")
            dept_frame.pack(fill="both", expand=True, padx=20, pady=10)
            tree = ttk.Treeview(dept_frame, columns=["Department", "Average", "Highest", "Lowest"], show="headings")
            for col in ["Department", "Average", "Highest", "Lowest"]:
                tree.heading(col, text=col)
                tree.column(col, width=140, anchor="center")
            for row in dept_rows:
                clean_row = ["N/A" if value is None else value for value in row]
                tree.insert("", "end", values=clean_row)
            scrollbar = ttk.Scrollbar(dept_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        except Exception as e:
            messagebox.showerror("Error", f"Analytics error: {e}")

    def add_bonus_marks_gui(self):
        def submit(values, popup):
            try:
                dept = values["department"]
                bonus = float(values["bonus"])
                if not dept:
                    messagebox.showwarning("Input Error", "Department is required.")
                    return
                add_bonus_marks(dept, bonus)
                popup.destroy()
                messagebox.showinfo("Success", "Bonus marks added successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Bonus marks error: {e}")
        self.open_form_popup("Add Bonus Marks", [("Department", "department"), ("Bonus Marks", "bonus")], submit)

    def export_high_performers_gui(self):
        try:
            filename = export_high_performers()
            if filename:
                messagebox.showinfo("Export Success", f"Exported to {filename}")
            else:
                messagebox.showinfo("Export", "No high performers found.")
        except Exception as e:
            messagebox.showerror("Error", f"Export error: {e}")

    def list_users(self):
        try:
            self.create_treeview(["Username", "Role", "Active", "Created At"], fetch_users(), "Users")
        except Exception as e:
            messagebox.showerror("Error", f"List users error: {e}")

    def create_user_gui(self):
        popup = tk.Toplevel(self.root)
        popup.title("Create User")
        popup.geometry("430x560")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()

        outer = tk.Frame(popup, bg="white")
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(scroll_frame, text="Create User", font=("Arial", 15, "bold"), bg="white", fg="#1f4e79").pack(pady=15)

        fields = [
            ("Username", "username"),
            ("Password", "password"),
            ("Role", "role"),
            ("Student Name", "student_name"),
            ("Department", "department"),
            ("Marks", "marks")
        ]
        entries = {}

        for label, key in fields:
            tk.Label(scroll_frame, text=label, bg="white", font=("Arial", 11)).pack(anchor="w", pady=(8, 2), padx=20)
            entry = tk.Entry(scroll_frame, font=("Arial", 11), show="*" if key == "password" else "")
            entry.pack(fill="x", pady=4, padx=20)
            entries[key] = entry

        tk.Label(
            scroll_frame,
            text="Fill student fields only if role is student.",
            bg="white",
            fg="gray",
            font=("Arial", 9),
            wraplength=380,
            justify="left"
        ).pack(anchor="w", pady=(8, 10), padx=20)

        def submit():
            try:
                username = entries["username"].get().strip()
                password = entries["password"].get().strip()
                role = entries["role"].get().strip().lower()
                student_name = entries["student_name"].get().strip()
                department = entries["department"].get().strip()
                marks_text = entries["marks"].get().strip()

                if not username or not password or not role:
                    messagebox.showwarning("Input Error", "Username, password, and role are required.")
                    return

                if role == "student":
                    if not student_name or not department or not marks_text:
                        messagebox.showwarning("Input Error", "Student fields are required for student role.")
                        return
                    try:
                        marks = float(marks_text)
                    except ValueError:
                        messagebox.showwarning("Input Error", "Marks must be numeric.")
                        return
                    create_user(username, password, role, student_name, department, marks)
                else:
                    create_user(username, password, role)

                popup.destroy()
                messagebox.showinfo("Success", "User created successfully.")
                self.list_users()
            except Exception as e:
                messagebox.showerror("Error", f"Create user error: {e}")

        btn_frame = tk.Frame(scroll_frame, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=(10, 18))
        tk.Button(
            btn_frame,
            text="Create User",
            font=("Arial", 11, "bold"),
            bg="#1f77b4",
            fg="white",
            width=18,
            command=submit
        ).pack()

    def toggle_user_gui(self):
        try:
            username = simpledialog.askstring("Toggle User", "Enter username:")
            if not username:
                return
            toggle_user(username)
            messagebox.showinfo("Success", "User status updated successfully.")
            self.list_users()
        except Exception as e:
            messagebox.showerror("Error", f"Toggle user error: {e}")

    def create_mysql_users_gui(self):
        try:
            create_mysql_users()
            messagebox.showinfo("Success", "MySQL application users created successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"MySQL user creation error: {e}")

    def view_audit_log(self):
        try:
            self.create_treeview(
                ["ID", "User ID", "Action", "Details", "Timestamp"],
                fetch_audit_log(),
                "Recent Audit Log"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Audit log error: {e}")

    def delete_student_gui(self):
        def submit(values, popup):
            try:
                student_id = int(values["student_id"])
                delete_student(student_id)
                popup.destroy()
                messagebox.showinfo("Success", "Student deleted successfully.")
                self.view_students()
            except Exception as e:
                messagebox.showerror("Error", f"Delete student error: {e}")

        self.open_form_popup("Delete Student", [("Student ID", "student_id")], submit)

    def logout(self):
        logout_user()
        self.login_screen()

def main():
    try:
        root = tk.Tk()
        app = SPAApp(root)
        root.mainloop()
    except Exception:
        err = traceback.format_exc()
        log_exception_to_file(err)
        raise

if __name__ == "__main__":
    main()