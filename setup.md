# Ludo Online Setup Guide

## Local Development

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Play:**
   - Open `http://127.0.0.1:8000` in your browser.
   - Create a room and share the room number with your friend.

## Deployment to Render

1. **Create a GitHub Repository** and push this code to it.
2. **Connect to Render:**
   - Go to [dashboard.render.com](https://dashboard.render.com).
   - Click "New" -> "Blueprint".
   - Select your repository.
   - Render will automatically use the `render.yaml` file to set up the service.

## Game Rules Implemented
- **Starting:** You need a 6 to move a piece out of the base.
- **Turns:** You get an extra turn if you roll a 6, finish a piece, or hit an opponent's piece.
- **Winning:** All 4 pieces must reach the center (position 57).
- **Safe Spots:** Standard Ludo safe spots (star positions) are implemented to prevent hitting.
