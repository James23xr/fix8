from web import create_app
import os

app = create_app()

if __name__ == '__main__':
    print("Fix8 SaaS Server Starting...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
