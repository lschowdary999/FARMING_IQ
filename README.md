# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/147b7ba5-2858-4407-a64a-967a8e4b670e

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/147b7ba5-2858-4407-a64a-967a8e4b670e) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Disease Detection Backend (FastAPI)

The app includes a lightweight Python backend to run the provided crop disease models:

- `paddy_disease_model (1).h5`
- `sugarcane_high_accuracy_model.keras`
- `tomato_disease_highmodel_classifier.keras`

### How to run
1. Open a new terminal and run the backend:
```bash
cd server
python -m venv .venv
.\\.venv\\Scripts\\activate  # Windows PowerShell
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Place your trained model files inside `server/models/` as shown:

```
server/
  models/
    paddy_disease_model (1).h5
    sugarcane_high_accuracy_model.keras
    tomato_disease_highmodel_classifier.keras
```
2. Start the React app in another terminal:
```bash
npm run dev
```

The frontend calls `http://localhost:8000/predict`.

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/147b7ba5-2858-4407-a64a-967a8e4b670e) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
