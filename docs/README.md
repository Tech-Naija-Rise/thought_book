
# BM (Bobsi Mo) A System of Interconnected Apps

## 📝 BM Thought Book (NotesApp)

A **simple, secure note-taking application** built with **CustomTkinter**.
It provides a clean and modern interface for creating, editing, and managing notes with lightweight encryption and password protection.

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

* Dark/Light theme toggle.
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
   * Create a Desktop shortcut (`NotesApp.lnk`) with a hotkey (default: `Ctrl+Alt+T`).

4. **Launch the app**

   * Use the Desktop shortcut
   * Or run directly from `dist\Thought Book.exe`.

---

## 🔑 First-time Setup

* On first launch, you’ll be asked to **create a password**.
* You’ll also be prompted to set a **recovery code** (write it down somewhere safe!).
* Notes are stored in `BMTbnotes.db` and the contents are protected with a light substitution cipher.

---

## 🧩 Project Structure

```
Thought_Book/
│── deploy.py        # Deployment script (builds exe + shortcut)
│── notes_app.py     # Main NotesApp source code
│── utils.py         #SQLite helper
│── pass.pass        # Stored password hash
│── recovery.key     # Recovery code hash
│── README.md        # Project documentation
│── requirements.txt # Dependencies
```

---

## 👨‍💻 Author

Created by **Umar Mahmud**

---

## ⚠️ Notes

* Tested on **Windows only** (due to shortcut + hotkey support).
* If you rerun `deploy.py`, it cleans old builds and generates a fresh `.exe`.
* Default hotkey can be changed in `deploy.py`.
* The `BMTbnotes.db` database is universally stored in your system's appdata folder in `roaming` folder (try pressing Windows + R and then typing `appdata`)
* For tips on how to backup your notes, [read the docs](./docs/how_to.md)