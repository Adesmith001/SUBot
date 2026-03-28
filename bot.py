from registration_bot.application import create_bot_application


def main():
    application = create_bot_application()
    application.run_polling()


if __name__ == "__main__":
    main()

