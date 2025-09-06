import subprocess
import sys
import threading
import os
from constants import logs_file
"""
Normally we should have permission from BMA to make changes to
the activities in its database because we could make mistakes 
that would make BMA look bad, basically

Which means that as a convention of BMA suite of apps
we must have a CLI api in order to interact with the apps' files

if thought book wants to communicate with BMA or BMT

he has to run a subprocess or cmd calling

meaning that when deploying any BM app, we must add
them to system environment varibles so that
"""
import logging
# setup logging once (top-level of your file, before class)
logging.basicConfig(
    filename=logs_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",

)

# Every BM app is going to put its folder in
# the environment variables of the user's computer
# if BMA is not installed and its env variable is not set
# then the activities api will not work
# Because BMA is not installed.

_ = os.getenv("BMA")
if _ is None:
    logging.error("BMA environment variable not set.")
    sys.exit(1)


class ActivitiesAPI:
    def __init__(self) -> None:
        self.poa_list = []

    def make_activities(self, poa_list):
        """We are running in another thread because it freezes 
        before exiting which is undesirable."""
        threading.Thread(target=self._make, args=(
            poa_list,), daemon=False).start()

    def _make(self, poa_list):
        self.poa_list = poa_list

        for actv in self.poa_list:
            try:
                cmd = f'{_}\\BMA.exe add "{actv}"'
                # communicate with BMA cli
                info = subprocess.run(cmd, capture_output=True)
                logging.info(
                    "I talked to BMA. He says: "
                    f"{info.stdout.decode(encoding='utf-8').strip()}".strip()
                )
            except Exception as e:
                logging.error(f"{e}: {cmd}")


if __name__ == "__main__":
    ActivitiesAPI().make_activities(
        ['[ ] do something', "[ ] do another thing"])
