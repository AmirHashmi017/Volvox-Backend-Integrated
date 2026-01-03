# Deploying Volvox Backend to Hugging Face Spaces

This guide will help you deploy your FastAPI backend to Hugging Face Spaces using the Dockerfile we created.

## Prerequisites

1.  A **Hugging Face Account**: [Sign up here](https://huggingface.co/join).
2.  **Git** installed on your machine (you already have this).

## Step 1: Create a Space on Hugging Face

1.  Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2.  **Space Name**: Enter a name (e.g., `Volvox-Backend`).
3.  **License**: Select a license (e.g., MIT) or leave blank.
4.  **Select the Space SDK**: Choose **Docker**.
5.  **Space Hardware**: Select **Free** (CPU basic).
6.  **Visibility**: Choose **Public** or **Private**.
7.  Click **Create Space**.

## Step 2: Configure Environment Variables (Secrets)

Your application needs secrets (like the Database URI) to work. Do NOT put these in code.

1.  In your new Space, go to the **Settings** tab.
2.  Scroll down to the **Variables and secrets** section.
3.  Click **New secret** and add the following from your local `.env` file:
    *   **Name**: `MONGO_DB_URI`
    *   **Value**: (Paste your actual MongoDB connection string here)
    *   **Name**: `OPENAI_API_KEY` (If you are using it)
    *   **Value**: (Paste your OpenAI Key)
    *   *Add any other secrets from your `.env` file.*

## Step 3: Deploy using Git

Since your local folder involves an existing Git repository, we will add your Hugging Face Space as a *second* remote destination. This allows you to push your code there without breaking your current GitHub setup.

1.  **Copy the Clone URL**:
    On your Space page, click the equivalent of the "Clone repository" button (usually in the "App" or "Files" tab, looking like `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`).

2.  **Open your Terminal** in the `Volvox-Backend-Integrated` folder.

3.  **Add the Remote**:
    Run the following command (replace the URL with your Space's URL):
    ```bash
    git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
    ```

4.  **Push to Hugging Face**:
    Now push your local code to the new remote. You might be prompted for your Hugging Face username and password (or Access Token).
    > **Note**: If you use an Access Token (recommended), use it as the password. You can generate one in your HF Settings > Access Tokens (Make sure it has "Write" permissions).

    ```bash
    git push huggingface main
    # OR if your default branch is master:
    # git push huggingface master
    ```
    
    *If you get an error about "unrelated histories" (because the Space might have started with a README), use:*
    ```bash
    git pull huggingface main --allow-unrelated-histories
    # Fix any merge conflicts if they appear (likely just README.md)
    git push huggingface main
    ```

## Troubleshooting Authentication
If you see the error: `remote: Password authentication in git is no longer supported.`

1.  Go to **[Hugging Face Settings > Access Tokens](https://huggingface.co/settings/tokens)**.
2.  Click **Create new token**.
3.  Name it (e.g., "Space-Deploy").
4.  **Important**: Select **Write** permissions (or "Fine-grained" -> "Repo: Write").
5.  Copy the token (it starts with `hf_...`).
6.  Try `git push huggingface main` again.
7.  **Username**: Your Hugging Face username.
8.  **Password**: PASTE THE TOKEN here. (You won't see characters typing).

To avoid typing the token every time, you can embed it in the remote URL (Be careful, this saves the token in your local git config):
```bash
git remote set-url huggingface https://YOUR_USER_NAME:YOUR_ACCESS_TOKEN@huggingface.co/spaces/YOUR_USER_NAME/YOUR_SPACE_NAME
```

### Error: "Updates were rejected" or "failed to push some refs"
If you see this error, it means the Space has files (like a `README.md`) that you don't have yet. You need to pull them first.

Run this command:
```bash
git pull huggingface main --allow-unrelated-histories
```
*   If it opens a text editor (Vim/Nano) for a merge message:
    *   Press `Esc` then type `:wq` and hit `Enter` (for Vim).
    *   Or `Ctrl+X`, then `Y`, then `Enter` (for Nano).

Then push again:
```bash
git push huggingface main
```

## Step 4: Watch the Build

1.  Go back to your Space's **App** tab.
2.  You should see "Building" or "Running".
3.  Click "Logs" to see the deployment progress.
4.  Once it says "Running", your API is live!

## Accessing the API

Your API will be available at:
`https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

Append `/docs` to the URL to verify it's working (e.g., `.../docs`).
