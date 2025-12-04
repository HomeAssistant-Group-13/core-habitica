"""Utility functions for Habitica sensors."""

from __future__ import annotations

from datetime import datetime
import random

from habiticalib import ContentData, UserData


def get_daily_motivational_prompt(user: UserData, content: ContentData) -> str:
    """Generate a daily motivational prompt based on user data."""
    # Seed random with current date to ensure same prompt per day
    today = datetime.now().date()
    random.seed(hash(f"{user.id}_{today}"))

    # Base motivational prompts
    base_prompts = [
        "🌟 Ready to tackle your habits today? You've got this!",
        "💪 Every small step counts towards building better habits!",
        "🎯 Focus on progress, not perfection!",
        "🚀 Your future self will thank you for what you do today!",
        "⭐ Consistency is the key to lasting change!",
        "🌈 Make today amazing by completing your habits!",
        "🔥 You're building unstoppable momentum!",
        "💎 Turn your habits into your superpowers!",
        "🏆 Champions are made through daily discipline!",
        "✨ Small habits, big transformations!",
    ]

    # Personalized prompts based on user stats
    level = user.stats.lvl or 1
    if level >= 50:
        base_prompts.extend(
            [
                f"🎖️ Level {level} warrior, show those habits who's boss!",
                "🗡️ Your high level shows your dedication - keep it up!",
            ]
        )
    elif level >= 20:
        base_prompts.extend(
            [
                f"⚔️ Level {level} adventurer, ready for today's quest?",
                "🛡️ You're growing stronger with every habit!",
            ]
        )

    # Class-based prompts
    if user.stats.Class:
        class_name = user.stats.Class.value
        class_prompts = {
            "warrior": "⚔️ Channel your warrior spirit into your habits!",
            "mage": "🔮 Use your magical focus to master your routines!",
            "rogue": "🗡️ Strike swiftly and efficiently at your goals!",
            "healer": "💚 Nurture yourself with positive habits today!",
        }
        if class_name.lower() in class_prompts:
            base_prompts.append(class_prompts[class_name.lower()])

    return random.choice(base_prompts)
