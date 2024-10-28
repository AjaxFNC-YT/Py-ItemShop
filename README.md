# Py-ItemShop
A Python program to generate the Fortnite item shop as an image.

## Overview
This script generates an image of the current Fortnite item shop, saving it in a folder. This project was based on the [Fortnite-Shop-Bot](https://github.com/FortniteFevers/Fortnite-Shop-Bot) by FortniteFevers.

## Updates
- Removed Twitter integration; (FUCK TWITTER)
- Now fully asynchronous with threading to maximize speed.
- Item shops are saved in a `shops` folder for saving.
- OG items are saved in a `og` folder inside the `shops` folder.
- OG items now feature customizable titles on the image.
- OG items now include the date in the name.
- Background images for both OG items and item shop images.
- Optimized if and for loops for cleaner code.
- Various other improvements and fixes.

## Installation Guide

### Step 1: Download
- Download the code by clicking the **Download ZIP** button on the repository page.
- Extract the contents of the ZIP file to a directory of your choice.

### Step 2: Install Dependencies
- Open a terminal in the directory where you extracted the files.
- Run the following command to install the required Python modules:

  ```bash
  pip install -r requirements.txt
  ```

### Step 3: Configure Settings (Optional)
- The settings for the app is in the `bot.py` file and the `merger.py` file, the merger file is for the final image, bot is for creating all the smaller images

## Running the Script
Once everything is set up, you can generate the Fortnite item shop image by running:

```bash
python bot.py
```

This will save the generated images in the `shops` folder.
