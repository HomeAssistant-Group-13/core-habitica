"""Test Habitica sensor utils."""

from unittest.mock import MagicMock, patch

from habiticalib import ContentData, UserData
import pytest

from homeassistant.components.habitica.sensor.utils import get_daily_motivational_prompt


@pytest.fixture
def mock_user_data() -> UserData:
    """Create a mock UserData object."""
    user = MagicMock(spec=UserData)
    user.id = "test-user-id"
    user.stats = MagicMock()
    user.stats.lvl = 38
    user.stats.Class = None
    return user


@pytest.fixture
def mock_content_data() -> ContentData:
    """Create a mock ContentData object."""
    return MagicMock(spec=ContentData)


def test_get_daily_motivational_prompt_warrior_class(
    mock_user_data: UserData,
    mock_content_data: ContentData,
) -> None:
    """Test motivational prompt with warrior class."""
    # Set up warrior class
    mock_user_data.stats.Class = MagicMock()
    mock_user_data.stats.Class.value = "warrior"

    # Mock random.choice to return the class-specific prompt
    with patch(
        "homeassistant.components.habitica.sensor.utils.random.choice"
    ) as mock_choice:
        mock_choice.return_value = "⚔️ Channel your warrior spirit into your habits!"

        result = get_daily_motivational_prompt(mock_user_data, mock_content_data)

        assert result == "⚔️ Channel your warrior spirit into your habits!"
        # Verify the warrior prompt was added to the list
        call_args = mock_choice.call_args[0][0]
        assert "⚔️ Channel your warrior spirit into your habits!" in call_args


def test_get_daily_motivational_prompt_mage_class(
    mock_user_data: UserData,
    mock_content_data: ContentData,
) -> None:
    """Test motivational prompt with mage class."""
    # Set up mage class
    mock_user_data.stats.Class = MagicMock()
    mock_user_data.stats.Class.value = "mage"

    # Mock random.choice to return the class-specific prompt
    with patch(
        "homeassistant.components.habitica.sensor.utils.random.choice"
    ) as mock_choice:
        mock_choice.return_value = "🔮 Use your magical focus to master your routines!"

        result = get_daily_motivational_prompt(mock_user_data, mock_content_data)

        assert result == "🔮 Use your magical focus to master your routines!"
        # Verify the mage prompt was added to the list
        call_args = mock_choice.call_args[0][0]
        assert "🔮 Use your magical focus to master your routines!" in call_args


def test_get_daily_motivational_prompt_rogue_class(
    mock_user_data: UserData,
    mock_content_data: ContentData,
) -> None:
    """Test motivational prompt with rogue class."""
    # Set up rogue class
    mock_user_data.stats.Class = MagicMock()
    mock_user_data.stats.Class.value = "rogue"

    # Mock random.choice to return the class-specific prompt
    with patch(
        "homeassistant.components.habitica.sensor.utils.random.choice"
    ) as mock_choice:
        mock_choice.return_value = "🗡️ Strike swiftly and efficiently at your goals!"

        result = get_daily_motivational_prompt(mock_user_data, mock_content_data)

        assert result == "🗡️ Strike swiftly and efficiently at your goals!"
        # Verify the rogue prompt was added to the list
        call_args = mock_choice.call_args[0][0]
        assert "🗡️ Strike swiftly and efficiently at your goals!" in call_args


def test_get_daily_motivational_prompt_healer_class(
    mock_user_data: UserData,
    mock_content_data: ContentData,
) -> None:
    """Test motivational prompt with healer class."""
    # Set up healer class
    mock_user_data.stats.Class = MagicMock()
    mock_user_data.stats.Class.value = "healer"

    # Mock random.choice to return the class-specific prompt
    with patch(
        "homeassistant.components.habitica.sensor.utils.random.choice"
    ) as mock_choice:
        mock_choice.return_value = "💚 Nurture yourself with positive habits today!"

        result = get_daily_motivational_prompt(mock_user_data, mock_content_data)

        assert result == "💚 Nurture yourself with positive habits today!"
        # Verify the healer prompt was added to the list
        call_args = mock_choice.call_args[0][0]
        assert "💚 Nurture yourself with positive habits today!" in call_args


def test_get_daily_motivational_prompt_unknown_class(
    mock_user_data: UserData,
    mock_content_data: ContentData,
) -> None:
    """Test motivational prompt with unknown class (should not add class-specific prompt)."""
    # Set up an unknown class
    mock_user_data.stats.Class = MagicMock()
    mock_user_data.stats.Class.value = "unknown_class"

    # Mock random.choice to verify no class-specific prompt was added
    with patch(
        "homeassistant.components.habitica.sensor.utils.random.choice"
    ) as mock_choice:
        mock_choice.return_value = (
            "🌟 Ready to tackle your habits today? You've got this!"
        )

        result = get_daily_motivational_prompt(mock_user_data, mock_content_data)

        assert result == "🌟 Ready to tackle your habits today? You've got this!"
        # Verify no class-specific prompt was added
        call_args = mock_choice.call_args[0][0]
        # Should only have base prompts (10) and possibly level-based prompts
        # but no class-specific prompts for unknown class
        assert "⚔️ Channel your warrior spirit into your habits!" not in call_args
        assert "🔮 Use your magical focus to master your routines!" not in call_args
        assert "🗡️ Strike swiftly and efficiently at your goals!" not in call_args
        assert "💚 Nurture yourself with positive habits today!" not in call_args


def test_get_daily_motivational_prompt_no_class(
    mock_user_data: UserData,
    mock_content_data: ContentData,
) -> None:
    """Test motivational prompt with no class (None)."""
    # Ensure Class is None
    mock_user_data.stats.Class = None

    # Mock random.choice
    with patch(
        "homeassistant.components.habitica.sensor.utils.random.choice"
    ) as mock_choice:
        mock_choice.return_value = (
            "🌟 Ready to tackle your habits today? You've got this!"
        )

        result = get_daily_motivational_prompt(mock_user_data, mock_content_data)

        assert result == "🌟 Ready to tackle your habits today? You've got this!"
        # Verify no class-specific prompt was added
        call_args = mock_choice.call_args[0][0]
        assert "⚔️ Channel your warrior spirit into your habits!" not in call_args
        assert "🔮 Use your magical focus to master your routines!" not in call_args
        assert "🗡️ Strike swiftly and efficiently at your goals!" not in call_args
        assert "💚 Nurture yourself with positive habits today!" not in call_args
