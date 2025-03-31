#!/bin/bash

# Запускаем Django через gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 &

# Запускаем Telegram-бота (в том же процессе)
python telegram_bot/run_bot.py
