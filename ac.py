# ac.py (AutoComplete.py)

import threading

import torch
from autoai import train
from autoai.gen import autocomplete
from autoai import m, models_folder
import tkinter as tk
import re
import os
from tkinter.messagebox import askyesno

# use for further finetuning
# train.finetune()

# load the best model
if os.path.exists(models_folder("checkpoint.pth")):
    m.load_state_dict(torch.load(models_folder("checkpoint.pth")))
else:
    m.load_state_dict(torch.load(models_folder("model.pth")))

import sys
import logging

logging.basicConfig(
    filename="training.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class StreamToLogger(object):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        message = message.strip()
        if message:  # avoid blank lines
            self.logger.log(self.level, message)

    def flush(self):
        pass  # needed for file-like object


def run_training_with_logging(func):
    # Redirect stdout and stderr
    sys.stdout = StreamToLogger(logging.getLogger(), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger(), logging.ERROR)

    try:
        func()  # ACAI training
    finally:
        # Restore normal stdout/stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class AutoCompleterAI:
    def __init__(self, app, text_box, suggestion_label) -> None:
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

        self.logger = logging.getLogger("AutoCompleterAI")
        self.final_suggestion = ""
    # -------------------- Helper Functions --------------------

    def train_AI(self, train_content, words_num):
        self.train_content = train_content
        self.logger.info(
            f"Will learn the following content:\n {self.train_content[0:100]}")

        if askyesno("Fine-tune ready",
                    f"You've written approximately {words_num} new words. Fine-tune the model now?"):
            def training_job():
                run_training_with_logging(lambda: train.finetune(
                    m, f"{self.train_content}",
                    "model.pth", "checkpoint.pth", 500, []
                ))

            threading.Thread(target=training_job, daemon=False).start()

    def update_suggestion(self, prompt):
        """Run GPT generation in a separate thread and update the label"""
        generated_text = str(autocomplete(prompt, 10)).strip("\n")

        # remove the prompt from the output of autocomplete

        # Only update if this is the latest prompt
        if prompt != self.current_prompt:
            return
        # Trim to first word
        first_word = re.findall(r'\w+', generated_text)
        print(generated_text)
        # predict the current word being typed and the next word
        try:
            self.suggestion_word = first_word[1]+" " +\
                first_word[2]+" "+first_word[3]
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
            self.root.after_cancel(self.debounce_id)

        content = self.text_box.get("1.0", tk.END).strip()
        if not content:
            self.current_prompt = ""
            return

        # smaller context for faster prediction
        last_prompt = str(self.get_last_words(content))
        self.current_prompt = last_prompt

        # Start GPT generation after 150ms pause in typing
        self.debounce_id = self.root.after(150, lambda: threading.Thread(
            target=self.update_suggestion, args=(last_prompt,), daemon=True).start())

    def accept_suggestion(self, event=None):
        """Insert suggestion into text box"""
        suggestion = self.suggest_label.cget("text")
        if suggestion:
            self.text_box.insert(tk.INSERT, suggestion)
            self.suggest_label.config(text="")
