
# NotesApp

A simple, secure note-taking application built with **CustomTkinter**. NotesApp provides a clean and minimal interface for creating, editing, and organizing notes, while keeping your data encrypted and password-protected.

---

## Features

- **Sidebar notes list:** Easily navigate between saved notes.
- **Title & content editor:** Write and organize your notes efficiently.
- **Add/Delete notes:** Create or remove notes with a single click.
- **Automatic note selection:** Load a note by clicking it in the sidebar.
- **Password protection:** Secure your notes with a password.
- **Encrypted storage:** Note content is encrypted using a simple substitution cipher.
- **Recovery code:** Reset your password safely if forgotten.
- **Settings GUI:** Change your password without editing files manually.
- **Autosave:** Notes are saved automatically after changes.

---

## Future Extensions

- Persistent storage enhancements (JSON or SQLite) for cross-session reliability.
- Search and filter functionality for quick note retrieval.
- Dark/Light theme toggle.
- Keyboard shortcuts for efficiency (e.g., Ctrl+N for new note, Ctrl+S to save).

---

## Installation

1. Clone the repository or download the files.
2. Install required packages:

```bash
pip install customtkinter
````

3. Run the application:

```bash
python notes_app.py
```

---

## Usage

1. On first launch, set a password and recovery code.
2. Add a new note using the **Add Note** button.
3. Click on a note in the sidebar to edit it.
4. Use the **Settings** button to change your password.
5. Notes are automatically saved and encrypted.

**Tip:** Keep your recovery code in a safe place to reset your password if needed.

---

## Security

* Passwords are hashed using **SHA-256**.
* Notes content is encrypted with a **simple substitution cipher**.
* Recovery mechanism ensures you can reset passwords without losing data.

---

## Author

**Umar Mahmud**

---

## License

MIT License

```

If you want, I can also create a **more concise version optimized for GitHub** with badges and quick installation instructions—good for showing the project publicly. Do you want me to do that next?
