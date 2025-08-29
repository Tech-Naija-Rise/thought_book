

# 📝 Thought Book (NotesApp)

A **simple, secure note-taking application** built with **CustomTkinter**.
It provides a clean and modern interface for creating, editing, and managing notes with lightweight encryption and password protection.

<img width="367" height="229" alt="image" src="https://github.com/user-attachments/assets/83fa5039-86da-40c5-9b81-312a9ee051eb" />
<img width="625" height="422" alt="image" src="https://github.com/user-attachments/assets/7b9e7f51-6027-47a9-b00c-2e6ad81735a6" />

---

## 🚀 Features

* 🗂 **Sidebar navigation** – view and switch between notes quickly.
* ✍ **Create, edit, and delete notes** with ease.
* 💾 **Auto-save** while typing (never lose your work).
* 🔒 **Password protection** for opening the app.
* 🔑 **Recovery code** support if you forget your password.
* 🔐 **Light encryption** of note contents.
* 🎨 **Modern UI** powered by [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).

---

## 🔮 Planned Extensions

* Persistent storage with SQLite (currently JSON).
* Dark/Light theme toggle.
* Global hotkeys for creating/saving notes (`Ctrl+N`, `Ctrl+S`).
* Search and filtering inside the sidebar.

---

## 📦 Installation & Usage

1. **Clone this repo**

   ```bash
   git clone https://github.com/Mahmudumar/thought_book.git
   cd Thought_Book
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   > Required: `customtkinter`, `pyinstaller`, `pywin32`

3. **Deploy the app**
   Run the deployment script:

   ```bash
   python deploy.py
   ```

   This will:

   * Bundle the app into a standalone `.exe` (via PyInstaller).
   * Create a Desktop shortcut (`NotesApp.lnk`) with a hotkey (default: `Ctrl+Alt+N`).

4. **Launch the app**

   * Use the Desktop shortcut
   * Or run directly from `dist/notes_app.exe`.

---

## 🔑 First-time Setup

* On first launch, you’ll be asked to **create a password**.
* You’ll also be prompted to set a **recovery code** (write it down somewhere safe!).
* Notes are stored in `notes.json` and protected with light substitution + SHA-256 password hashing.

---

## 🧩 Project Structure

```
Thought_Book/
│── deploy.py        # Deployment script (builds exe + shortcut)
│── notes_app.py     # Main NotesApp source code
│── notes.json       # Saved notes (auto-created)
│── pass.pass        # Stored password hash
│── recovery.key     # Recovery code hash
│── README.md        # Project documentation
│── requirements.txt # Dependencies
```

---

## 👨‍💻 Author

Created by **Umar Mahmud**
Part of the **Tech Naija Rise (TNR)** initiative 🚀

---

## ⚠️ Notes

* Tested on **Windows only** (due to shortcut + hotkey support).
* If you rerun `deploy.py`, it cleans old builds and generates a fresh `.exe`.
* Default hotkey can be changed in `deploy.py`.
