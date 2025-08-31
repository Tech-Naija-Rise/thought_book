# ac.py (AutoComplete.py)

import threading
from autocompleteAI.gen import autocomplete
import autocompleteAI.train as train
import tkinter as tk
import re

# use for further finetuning
# train.train()

import customtkinter as ctk


class AutoCompleterAI:
    def __init__(self, app=None, text_box=None, suggestion_label=None) -> None:
        """
        app is the root of the notes app

        text_box is the text box you type in

        suggestion_label is the ctk label to show the 
        autocomplete suggestions

        """
        self.root = app
        self.text_box = text_box
        # Globals for debounce and latest prompt
        self.debounce_id = None
        self.current_prompt = ""
        self.suggest_label = suggestion_label

        self.final_suggestion = ""
    # -------------------- Helper Functions --------------------
    def retrain_model(self):
        train.train(40_000)
        

    def update_suggestion(self, prompt):
        """Run GPT generation in a separate thread and update the label"""
        generated_text = str(autocomplete(prompt, 10)).strip("\n")

        # remove the prompt from the output of automcomplete

        # Only update if this is the latest prompt
        if prompt != self.current_prompt:
            return
        # Trim to first word
        first_word = re.findall(r'\w+', generated_text)

        # predict the current word being typed and the next word
        try:
            self.suggestion_word = first_word[1]+" " +\
                first_word[2]
        except Exception:
            self.suggestion_word = first_word[0]
        # print(
            # f"prompt: {prompt}, Generated: {generated_text}, Suggested word: {suggestion_word}")

        self.final_suggestion = self.suggestion_word

    def get_last_word(self, text: str):
        # prompt is last 15 chars
        prompt = text[::-1][0:15][::-1]
        rev_generated = prompt[::-1]
        get_word = re.match(r'\w+', rev_generated)
        last_word_reved = get_word.group(0) if get_word else " "
        final_last_word = last_word_reved[::-1]
        return final_last_word

    def get_last_words(self, text: str, words=2):
        # prompt is last 15 chars
        prompt = text[::-1][0:15][::-1]
        rev_generated = prompt[::-1]

        get_word = re.findall(r'\w+', rev_generated)
        last_word_reved = ""

        for index in range(words):
            try:
                last_word_reved += str(get_word[index]) + " "
            except IndexError:

                # if there's only one word, just give that back
                last_word_reved += str(get_word[0])

        # remove the last space
        last_word_reved.strip()
        final_last_word = last_word_reved[::-1]
        return final_last_word

    def on_key_release(self, event=None):
        """Called on every key release, debounced"""

        if self.debounce_id:
            self.root.after_cancel(self.debounce_id)  # type: ignore

        content = self.text_box.get("1.0", tk.END).strip()  # type: ignore
        if not content:
            self.current_prompt = ""
            return

        # smaller context for faster prediction
        last_prompt = str(self.get_last_words(content))
        self.current_prompt = last_prompt

        # Start GPT generation after 150ms pause in typing
        self.debounce_id = self.root.after(10, lambda: threading.Thread(  # type: ignore
            target=self.update_suggestion, args=(last_prompt,), daemon=True).start())
