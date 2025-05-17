"""
Test suite for the Habit Tracker application.

This module contains unit tests for the main components:
- Habit class
- HabitTracker class
- Analytics module

Run with: pytest test_habit_tracker.py
"""

import os
import pytest
import sqlite3
from datetime import datetime, timedelta
import tempfile
import shutil
from habit_tracker import (
    Habit, HabitTracker, DataManager,
    get_all_habits, get_habits_by_periodicity,
    get_longest_streak_all, get_longest_streak_for_habit,
    get_current_streak_for_habit, get_habits_with_streak_info,
    get_struggling_habits
)

# ========== Test Fixtures ==========

@pytest.fixture
def mock_db_path(monkeypatch):
    """Create a temporary database for testing."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_habits.db")
    
    # Mock the get_db_path function
    def mock_get_path():
        return db_path
    
    # Apply the mock
    monkeypatch.setattr('habit_tracker.get_db_path', mock_get_path)
    
    yield db_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def setup_db(mock_db_path):
    """Initialize the test database."""
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS habits (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        periodicity TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS completions (
        id TEXT PRIMARY KEY,
        habit_id TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        FOREIGN KEY (habit_id) REFERENCES habits(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    return mock_db_path

@pytest.fixture
def sample_habit():
    """Create a sample daily habit for testing."""
    return Habit(
        name="Test Habit",
        description="A test habit",
        periodicity="daily",
        id="test-habit-1",
        created_at=datetime.now() - timedelta(days=10)
    )

@pytest.fixture
def sample_weekly_habit():
    """Create a sample weekly habit for testing."""
    return Habit(
        name="Weekly Test",
        description="A weekly test habit",
        periodicity="weekly",
        id="test-habit-2",
        created_at=datetime.now() - timedelta(days=28)
    )

@pytest.fixture
def tracker_with_habits(setup_db, sample_habit, sample_weekly_habit):
    """Create a tracker with sample habits."""
    tracker = HabitTracker()
    
    # Manually add habits to tracker
    tracker.habits = [sample_habit, sample_weekly_habit]
    tracker.save_habits()
    
    return tracker

# ========== Habit Class Tests ==========

def test_habit_initialization():
    """Test that a habit can be properly initialized."""
    habit = Habit(
        name="Morning Run",
        description="30 minute run",
        periodicity="daily"
    )
    
    assert habit.name == "Morning Run"
    assert habit.description == "30 minute run"
    assert habit.periodicity == "daily"
    assert isinstance(habit.id, str)
    assert isinstance(habit.created_at, datetime)
    assert habit.completions == []

def test_habit_periodicity_validation():
    """Test that periodicity validation works correctly."""
    with pytest.raises(ValueError):
        Habit(
            name="Invalid Habit",
            description="Has invalid periodicity",
            periodicity="monthly"  # Not supported
        )

def test_complete_task(sample_habit):
    """Test that a habit can be marked as completed."""
    initial_count = len(sample_habit.completions)
    
    sample_habit.complete_task()
    
    assert len(sample_habit.completions) == initial_count + 1
    assert isinstance(sample_habit.completions[-1], datetime)

def test_is_task_completed_for_period_daily(sample_habit):
    """Test checking if a daily habit was completed for a specific day."""
    # Add a completion for yesterday
    yesterday = datetime.now() - timedelta(days=1)
    sample_habit.completions.append(yesterday)
    
    # Check if completed yesterday
    assert sample_habit.is_task_completed_for_period(yesterday)
    
    # Check if completed today (should be false)
    assert not sample_habit.is_task_completed_for_period(datetime.now())

def test_is_task_completed_for_period_weekly(sample_weekly_habit):
    """Test checking if a weekly habit was completed for a specific week."""
    # Add a completion for this week
    today = datetime.now()
    this_week_start = today - timedelta(days=today.weekday())
    completion = this_week_start + timedelta(days=1)  # Tuesday
    sample_weekly_habit.completions.append(completion)
    
    # Check if completed this week
    assert sample_weekly_habit.is_task_completed_for_period(today)
    
    # Check if completed last week (should be false)
    last_week = today - timedelta(days=7)
    assert not sample_weekly_habit.is_task_completed_for_period(last_week)

def test_get_current_streak(sample_habit):
    """Test current streak calculation for a daily habit."""
    # No completions initially
    assert sample_habit.get_current_streak() == 0
    
    # Add completions for the last 3 days
    today = datetime.now()
    for days_ago in range(3):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    assert sample_habit.get_current_streak() == 3
    
    # Add a gap - streak should be broken
    modified_completions = []
    for days_ago in [0, 1, 3, 4]:  # Missing day 2
        completion = today - timedelta(days=days_ago)
        modified_completions.append(completion)
    
    sample_habit.completions = modified_completions
    assert sample_habit.get_current_streak() == 2  # Only today and yesterday count

def test_get_longest_streak(sample_habit):
    """Test longest streak calculation."""
    # Add completions with a pattern: 3 days on, 1 day off, 4 days on
    today = datetime.now()
    
    # First streak (3 days)
    for days_ago in range(7, 10):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    # Gap (1 day)
    
    # Second streak (4 days)
    for days_ago in range(2, 6):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    # Current streak (2 days)
    for days_ago in range(2):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    assert sample_habit.get_longest_streak() == 4

def test_habit_to_dict_and_from_dict():
    """Test converting habits to and from dictionaries."""
    original = Habit(
        name="Test Conversion",
        description="Testing conversion",
        periodicity="daily"
    )
    
    # Add a completion
    original.complete_task()
    
    # Convert to dict
    habit_dict = original.to_dict()
    
    # Convert back to object
    restored = Habit.from_dict(habit_dict)
    
    # Check equivalence
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.description == original.description
    assert restored.periodicity == original.periodicity
    assert restored.created_at.isoformat() == original.created_at.isoformat()
    assert len(restored.completions) == len(original.completions)
    assert restored.completions[0].isoformat() == original.completions[0].isoformat()

# ========== HabitTracker Class Tests ==========

def test_add_habit(tracker_with_habits):
    """Test adding a habit to the tracker."""
    initial_count = len(tracker_with_habits.habits)
    
    new_habit = Habit(
        name="New Test Habit",
        description="A new test habit",
        periodicity="daily"
    )
    
    tracker_with_habits.add_habit(new_habit)
    
    assert len(tracker_with_habits.habits) == initial_count + 1
    assert any(h.id == new_habit.id for h in tracker_with_habits.habits)

def test_remove_habit(tracker_with_habits, sample_habit):
    """Test removing a habit from the tracker."""
    initial_count = len(tracker_with_habits.habits)
    
    result = tracker_with_habits.remove_habit(sample_habit.id)
    
    assert result is True
    assert len(tracker_with_habits.habits) == initial_count - 1
    assert not any(h.id == sample_habit.id for h in tracker_with_habits.habits)

def test_remove_nonexistent_habit(tracker_with_habits):
    """Test removing a non-existent habit."""
    initial_count = len(tracker_with_habits.habits)
    
    result = tracker_with_habits.remove_habit("nonexistent-id")
    
    assert result is False
    assert len(tracker_with_habits.habits) == initial_count

def test_get_habit_by_id(tracker_with_habits, sample_habit):
    """Test getting a habit by ID."""
    habit = tracker_with_habits.get_habit_by_id(sample_habit.id)
    
    assert habit is not None
    assert habit.id == sample_habit.id
    assert habit.name == sample_habit.name

def test_get_nonexistent_habit_by_id(tracker_with_habits):
    """Test getting a non-existent habit by ID."""
    habit = tracker_with_habits.get_habit_by_id("nonexistent-id")
    
    assert habit is None

def test_complete_habit(tracker_with_habits, sample_habit):
    """Test completing a habit."""
    initial_completions = len(sample_habit.completions)
    
    result = tracker_with_habits.complete_habit(sample_habit.id)
    
    # Reload the habit
    updated_habit = tracker_with_habits.get_habit_by_id(sample_habit.id)
    
    assert result is True
    assert len(updated_habit.completions) == initial_completions + 1

def test_complete_nonexistent_habit(tracker_with_habits):
    """Test completing a non-existent habit."""
    result = tracker_with_habits.complete_habit("nonexistent-id")
    
    assert result is False

def test_load_and_save_habits(tracker_with_habits, sample_habit, sample_weekly_habit):
    """Test loading and saving habits."""
    # Modify the loaded habits
    new_habit = Habit(
        name="Another Test",
        description="Another test habit",
        periodicity="daily"
    )
    tracker_with_habits.add_habit(new_habit)
    
    # Create a new tracker that will load from the same DB
    new_tracker = HabitTracker()
    
    # Check if the habits were loaded correctly
    assert len(new_tracker.habits) == 3
    assert any(h.id == sample_habit.id for h in new_tracker.habits)
    assert any(h.id == sample_weekly_habit.id for h in new_tracker.habits)
    assert any(h.id == new_habit.id for h in new_tracker.habits)

# ========== Analytics Module Tests ==========

def test_get_all_habits(tracker_with_habits):
    """Test getting all habits."""
    habits = get_all_habits(tracker_with_habits.habits)
    
    assert len(habits) == 2
    assert habits == tracker_with_habits.habits

def test_get_habits_by_periodicity(tracker_with_habits, sample_habit, sample_weekly_habit):
    """Test filtering habits by periodicity."""
    daily_habits = get_habits_by_periodicity(tracker_with_habits.habits, "daily")
    weekly_habits = get_habits_by_periodicity(tracker_with_habits.habits, "weekly")
    
    assert len(daily_habits) == 1
    assert daily_habits[0].id == sample_habit.id
    
    assert len(weekly_habits) == 1
    assert weekly_habits[0].id == sample_weekly_habit.id

def test_get_longest_streak_all(tracker_with_habits, sample_habit, sample_weekly_habit):
    """Test finding the habit with the longest streak."""
    # Add completions to create streaks
    today = datetime.now()
    
    # Add 3-day streak to daily habit
    for days_ago in range(3):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    # Add 2-week streak to weekly habit
    current_week = today - timedelta(days=today.weekday())
    for weeks_ago in range(2):
        completion = current_week - timedelta(days=weeks_ago * 7)
        sample_weekly_habit.completions.append(completion)
    
    # Save changes
    tracker_with_habits.save_habits()
    
    # Test the function
    best_habit, longest_streak = get_longest_streak_all(tracker_with_habits.habits)
    
    assert best_habit.id == sample_habit.id
    assert longest_streak == 3

def test_get_longest_streak_for_habit(tracker_with_habits, sample_habit):
    """Test getting the longest streak for a specific habit."""
    # Add completions to create a streak
    today = datetime.now()
    
    # Add 3-day streak
    for days_ago in range(3):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    # Save changes
    tracker_with_habits.save_habits()
    
    # Test the function
    streak = get_longest_streak_for_habit(sample_habit.id, tracker_with_habits.habits)
    
    assert streak == 3

def test_get_current_streak_for_habit(tracker_with_habits, sample_habit):
    """Test getting the current streak for a specific habit."""
    # Add completions to create a streak
    today = datetime.now()
    
    # Add 3-day streak
    for days_ago in range(3):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    # Save changes
    tracker_with_habits.save_habits()
    
    # Test the function
    streak = get_current_streak_for_habit(sample_habit.id, tracker_with_habits.habits)
    
    assert streak == 3

def test_get_habits_with_streak_info(tracker_with_habits, sample_habit, sample_weekly_habit):
    """Test getting habit info with streak data."""
    # Add completions to create streaks
    today = datetime.now()
    
    # Add 3-day streak to daily habit
    for days_ago in range(3):
        completion = today - timedelta(days=days_ago)
        sample_habit.completions.append(completion)
    
    # Add 2-week streak to weekly habit
    current_week = today - timedelta(days=today.weekday())
    for weeks_ago in range(2):
        completion = current_week - timedelta(days=weeks_ago * 7)
        sample_weekly_habit.completions.append(completion)
    
    # Save changes
    tracker_with_habits.save_habits()
    
    # Test the function
    info = get_habits_with_streak_info(tracker_with_habits.habits)
    
    assert len(info) == 2
    daily_info = next(i for i in info if i['id'] == sample_habit.id)
    weekly_info = next(i for i in info if i['id'] == sample_weekly_habit.id)
    
    assert daily_info['current_streak'] == 3
    assert weekly_info['current_streak'] == 2

def test_get_struggling_habits(tracker_with_habits, sample_habit, sample_weekly_habit):
    """Test identifying struggling habits."""
    today = datetime.now()
    
    # Make the daily habit struggling
    # Add completions for only 2 out of 10 days
    sample_habit.completions = [
        today - timedelta(days=2),
        today - timedelta(days=8)
    ]
    
    # Make the weekly habit not struggling
    # Add completions for all 4 weeks
    current_week = today - timedelta(days=today.weekday())
    sample_weekly_habit.completions = [
        current_week,
        current_week - timedelta(days=7),
        current_week - timedelta(days=14),
        current_week - timedelta(days=21)
    ]
    
    # Save changes
    tracker_with_habits.save_habits()
    
    # Test the function
    struggling = get_struggling_habits(tracker_with_habits.habits)
    
    assert len(struggling) == 1
    assert struggling[0].id == sample_habit.id

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v"])