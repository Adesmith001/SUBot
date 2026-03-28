from registration_bot.web import create_web_app


app = create_web_app()


if __name__ == "__main__":
    settings = app.config["BOT_APP"].bot_data["settings"]
    app.run(host="0.0.0.0", port=settings.port, debug=True)

